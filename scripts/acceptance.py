"""End-to-end ApexGrid smoke flow against running Compose services.

Run with backend dependencies plus websockets installed:
  DATABASE_URL=postgresql://apexgrid:apexgrid@localhost:5432/apexgrid \
  MONGODB_URL=mongodb://localhost:27017 python scripts/acceptance.py

The script creates and removes a temporary session and its telemetry. It restores
the tested driver's pre-run penalty state and recalculates standings on cleanup.
"""

import json
import os
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from uuid import UUID

import psycopg
from pymongo import MongoClient
from websockets.sync.client import connect


API = os.getenv("API_URL", "http://localhost:8000/api")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://apexgrid:apexgrid@localhost:5432/apexgrid")
MONGO_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")


def request(path, token=None, body=None, method=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(API + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


def expect(path, token=None, body=None, method=None, status=200):
    actual, value = request(path, token, body, method)
    assert actual == status, (path, actual, value)
    return value


def assert_penalty_guard_enabled(cur):
    cur.execute("""SELECT tgenabled FROM pg_trigger
        WHERE tgrelid='penalties'::regclass AND tgname='trg_penalties_immutable' AND NOT tgisinternal""")
    row = cur.fetchone()
    if not row or row[0] != "O":
        raise RuntimeError("Apply the penalty immutability migration before running acceptance")


def main():
    health = expect("/health")
    assert health["services"] == {"postgres": "up", "mongodb": "up"}
    token = expect("/auth/login", body={"email": "admin@apexgrid.test", "password": "ApexGrid2026!"})["access_token"]
    championship = next(row for row in expect("/championships", token) if row["name"] == "ApexGrid World Series")
    events = expect("/events", token)
    event = next(row for row in events if row["round_number"] == 3 and row["championship_id"] == championship["id"])
    driver_rows = []
    offset = 0
    while True:
        page = expect(f"/drivers?limit=200&offset={offset}", token)
        driver_rows.extend(page)
        if len(page) < 200:
            break
        offset += 200
    drivers = sorted((row for row in driver_rows if str(row["licence_number"]).startswith("AG-")), key=lambda row: row["number"])
    teams = expect("/teams", token)
    assert len(drivers) >= 8 and len(teams) >= 2
    driver = next(row for row in drivers if row["number"] == 9)
    race_options = expect("/dbms/races", token)
    archived = next(row for row in race_options if row["state"] == "COMPLETED" and row["event_name"] == "Redwood Grand Prix")
    archive = expect(f"/dbms/races/{archived['id']}", token)
    assert archive["results"] and archive["laps"], archive
    assert archive["lap_source"] == "historical_demo"
    assert len({row["lap"] for row in archive["laps"]}) == archived["total_laps"]
    compact_archive = expect(f"/dbms/races/{archived['id']}?include_laps=false", token)
    archive_laps = expect(f"/dbms/races/{archived['id']}/laps", token)
    assert compact_archive["laps"] == [] and compact_archive["laps_included"] is False
    assert compact_archive["completed_driver_laps"] == len(archive["laps"])
    assert archive_laps["laps"] == archive["laps"]
    model = expect("/dbms/eer", token)
    assert any(row["child"] == "session_results" and row["parent"] == "race_sessions" for row in model["relationships"])
    relationship_keys = [(row["child"], row["foreign_key"], row["parent"], row["parent_key"]) for row in model["relationships"]]
    assert len(relationship_keys) == len(set(relationship_keys))
    session_id = None
    with psycopg.connect(DATABASE_URL) as db:
        with db.cursor() as cur:
            assert_penalty_guard_enabled(cur)
            cur.execute("SELECT points FROM penalty_points WHERE driver_id=%s AND season=%s", (driver["id"], championship["season"]))
            original_points = cur.fetchone()
            original_eligibility = driver["eligibility"]
    mongo = MongoClient(MONGO_URL)["apexgrid"]["telemetry"]
    demo_session_id = None
    incident_id = None
    try:
        session = expect("/sessions", token, {
            "event_id": event["id"], "session_type": "RACE", "state": "SCHEDULED",
            "scheduled_at": datetime.now(timezone.utc).isoformat(), "total_laps": 10,
        }, status=201)
        session_id = session["id"]
        expect(f"/sessions/{session_id}/action", token, {"action": "start"})

        ws_url = API.replace("http://", "ws://").replace("https://", "wss://")
        with connect(f"{ws_url}/ws/sessions/{session_id}", subprotocols=["apexgrid.jwt", token], open_timeout=8) as ws:
            expect(f"/sessions/{session_id}/simulate", token, {"action": "start", "cars": 4, "rate_hz": 2})
            seen = set()
            for _ in range(20):
                event_message = json.loads(ws.recv(timeout=8))
                seen.add(event_message["type"])
                if {"telemetry.sample", "timing.update"} <= seen:
                    break
            assert {"telemetry.sample", "timing.update"} <= seen, seen
        expect(f"/sessions/{session_id}/simulate", token, {"action": "stop"})
        race_records = expect(f"/dbms/races/{session_id}", token)
        assert race_records["session"]["state"] == "ACTIVE" and len(race_records["latest"]) == 4
        assert race_records["telemetry_count"] >= 4
        packets = expect(f"/telemetry?session_id={session_id}&limit=20", token)
        assert len(packets) >= 4 and mongo.count_documents({"session_id": session_id}) >= 4
        assert expect(f"/sessions/{session_id}/live", token)["session"]["state"] == "ACTIVE"

        boxes = expect(f"/pit-boxes?event_id={event['id']}", token)
        start = datetime.now(timezone.utc) + timedelta(minutes=5)
        window = {"pit_box_id": boxes[0]["id"], "session_id": session_id,
                  "starts_at": start.isoformat(), "ends_at": (start + timedelta(minutes=10)).isoformat()}
        with ThreadPoolExecutor(max_workers=2) as workers:
            futures = [workers.submit(request, "/pit-reservations", token, {**window, "team_id": team["id"]}) for team in teams[:2]]
            reservation_responses = [f.result() for f in futures]
        assert sorted(status for status, _ in reservation_responses) == [201, 409], reservation_responses
        reservation_id = next(value["id"] for status, value in reservation_responses if status == 201)
        assert len(expect(f"/pit-boxes?event_id={event['id']}", token)) == len(boxes)
        assert expect(f"/pit-reservations/{reservation_id}", token,
                      {"status": "CANCELLED"}, method="PATCH")["status"] == "CANCELLED"
        assert request(f"/pit-reservations/{reservation_id}", token,
                       {"status": "COMPLETED"}, method="PATCH")[0] == 409
        membership = next(row for row in expect(f"/drivers/{driver['id']}/memberships", token)
                          if row["end_date"] is None)
        allocated = expect("/pit-reservations/auto", token, {
            "session_id": session_id, "team_id": membership["team_id"],
            "driver_id": driver["id"],
        }, method="POST", status=201)
        assert allocated["allocation_source"] == "AUTOMATIC"
        assert allocated["driver_id"] == driver["id"]
        assert allocated["box_number"] in {box["number"] for box in boxes}
        assert any(row["id"] == allocated["id"] for row in expect(f"/pit-reservations?session_id={session_id}", token))
        assert any(row["id"] == allocated["id"] for row in expect(f"/dbms/races/{session_id}?include_laps=false", token)["pit_reservations"])
        assert expect(f"/pit-reservations/{allocated['id']}", token,
                      {"status": "CANCELLED"}, method="PATCH")["status"] == "CANCELLED"

        incident = expect("/incidents", token, {"session_id": session_id, "driver_id": driver["id"],
                                                     "lap": 1, "description": "Acceptance race control review"}, status=201)
        incident_id = incident["id"]
        decision = expect(f"/incidents/{incident['id']}/decision", token,
                          {"approve": True, "notes": "Confirmed", "points": 12})
        assert decision["driver"]["eligibility"] == "RACE_BANNED"
        assert expect(f"/drivers/{driver['id']}", token)["eligibility"] == "RACE_BANNED"

        result_rows = [{"driver_id": row["id"], "position": index + 1,
                        "lap_time_ms": 85000 + index * 100, "pole": index == 0,
                        "fastest_lap": index == 1, "classified": True}
                       for index, row in enumerate(drivers)]
        assert len(expect(f"/sessions/{session_id}/results", token, result_rows)) == len(drivers)
        expect(f"/sessions/{session_id}/action", token, {"action": "finish"})
        expect(f"/championships/{championship['id']}/recalculate", token, {})
        assert expect(f"/championships/{championship['id']}/standings", token)

        assert expect("/dbms/schema", token)
        assert expect("/dbms/indexes", token)
        assert expect("/dbms/explain?query=leaderboard", token)["plan"]
        assert expect("/dbms/constraint-demo", token, {})["rejected"] is True
        assert expect("/dbms/transaction-demo", token, {})["savepoint_rolled_back"] is True
        lock_demo = expect("/dbms/lock-demo", token, {})
        assert lock_demo["lock_wait_observed"] is True
        assert lock_demo["rejection_sqlstate"] == "23P01"
        assert expect("/dbms/locks", token)
        assert expect("/dbms/telemetry", token)["count"] > 0
        assert expect("/dbms/polyglot", token)["rows"]
        demo_race = expect("/demo-races", token, {"cars": 6}, method="POST", status=201)
        demo_session_id = demo_race["session_id"]
        assert demo_race["car_count"] == 6 and demo_race["simulation_state"] == "running"
        assert any(row["session_id"] == demo_session_id for row in expect("/demo-races", token))
        assert expect(f"/sessions/{demo_session_id}/live", token)["session"]["state"] == "ACTIVE"
        print("PASS: login, session, simulator, MongoDB, WebSocket, pit conflict, trigger/ban, results, standings, DBMS, generated demo races")
    finally:
        if demo_session_id:
            request(f"/demo-races/{demo_session_id}", token, method="DELETE")
        if session_id:
            request(f"/sessions/{session_id}/simulate", token, {"action": "stop"})
            mongo.delete_many({"session_id": session_id})
            with psycopg.connect(DATABASE_URL) as db:
                with db.cursor() as cur:
                    cur.execute("DELETE FROM pit_reservations WHERE session_id=%s", (session_id,))
                    if incident_id:
                        cur.execute("SELECT 1 FROM penalties WHERE incident_id=%s", (incident_id,))
                        if cur.fetchone():
                            # This is an acceptance-owned penalty in a disposable session.
                            # Keep the production trigger immutable and bypass it only
                            # around this exact cleanup delete inside this transaction.
                            cur.execute("ALTER TABLE penalties DISABLE TRIGGER trg_penalties_immutable")
                            try:
                                cur.execute("DELETE FROM penalties WHERE incident_id=%s", (incident_id,))
                            finally:
                                cur.execute("ALTER TABLE penalties ENABLE TRIGGER trg_penalties_immutable")
                    cur.execute("DELETE FROM incident_reports WHERE session_id=%s", (session_id,))
                    cur.execute("DELETE FROM session_results WHERE session_id=%s", (session_id,))
                    cur.execute("DELETE FROM race_sessions WHERE id=%s", (session_id,))
                    if original_points is None:
                        cur.execute("DELETE FROM penalty_points WHERE driver_id=%s AND season=%s", (driver["id"], championship["season"]))
                    else:
                        cur.execute("UPDATE penalty_points SET points=%s WHERE driver_id=%s AND season=%s", (original_points[0], driver["id"], championship["season"]))
                    cur.execute("UPDATE drivers SET eligibility=%s WHERE id=%s", (original_eligibility, driver["id"]))
                    cur.execute("SELECT recalculate_standings(%s)", (championship["id"],))
                    assert_penalty_guard_enabled(cur)


if __name__ == "__main__":
    main()
