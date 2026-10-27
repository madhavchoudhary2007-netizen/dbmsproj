"""End-to-end ApexGrid smoke flow against explicitly owned disposable databases."""

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from ipaddress import ip_address
from urllib.parse import unquote, urlparse
from uuid import UUID

import psycopg
from pymongo import MongoClient
from websockets.sync.client import connect


API = ""
DATABASE_URL = os.getenv("DATABASE_URL", "")
MONGO_URL = os.getenv("MONGODB_URL", "")


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


def _is_loopback_host(host):
    if not host:
        return False
    if host.lower() == "localhost":
        return True
    try:
        return ip_address(host).is_loopback
    except ValueError:
        return False


def ensure_disposable_target(database_url, mongo_database):
    raw = database_url or ""
    parsed = urlparse(raw)
    if ("?" in raw or "#" in raw or parsed.query or parsed.fragment or parsed.params
            or raw.count("@") > 1 or "," in parsed.netloc.rsplit("@", 1)[-1]):
        raise ValueError("DATABASE_URL cannot contain query, fragment, multi-host, or ambiguous options")
    if parsed.scheme not in {"postgres", "postgresql"}:
        raise ValueError("DATABASE_URL must use PostgreSQL")
    if not parsed.netloc or not parsed.path.startswith("/") or parsed.path.count("/") != 1:
        raise ValueError("DATABASE_URL must contain exactly one database path segment")
    database = unquote(parsed.path[1:])
    try:
        hostname, port = parsed.hostname, parsed.port
    except ValueError as exc:
        raise ValueError("DATABASE_URL has an ambiguous authority") from exc
    if not _is_loopback_host(hostname) or port != 15432:
        raise ValueError("DATABASE_URL must target loopback PostgreSQL on port 15432")
    prefix = "apexgrid_acceptance_"
    suffix = database[len(prefix):] if database.startswith(prefix) else ""
    if not suffix or not all(char.isalnum() or char in "-_" for char in suffix):
        raise ValueError("PostgreSQL database must be uniquely named apexgrid_acceptance_<run-id>")
    if mongo_database != database:
        raise ValueError("MongoDB database must match the owned PostgreSQL database name")
    return database


def ensure_mongo_target(mongo_url, database):
    raw = mongo_url or ""
    parsed = urlparse(raw)
    if ("?" in raw or "#" in raw or parsed.query or parsed.fragment or parsed.params
            or raw.count("@") > 1 or "," in parsed.netloc.rsplit("@", 1)[-1]):
        raise ValueError("MONGODB_URL cannot contain query, fragment, multi-host, or ambiguous options")
    if parsed.scheme not in {"mongodb", "mongodb+srv"}:
        raise ValueError("MONGODB_URL must be a MongoDB URL")
    if not parsed.netloc or not parsed.path.startswith("/") or parsed.path.count("/") != 1:
        raise ValueError("MONGODB_URL must contain exactly one database path segment")
    try:
        hostname, port = parsed.hostname, parsed.port
    except ValueError as exc:
        raise ValueError("MONGODB_URL has an ambiguous authority") from exc
    if not _is_loopback_host(hostname) or port != 27018:
        raise ValueError("MONGODB_URL must target loopback MongoDB on port 27018")
    if unquote(parsed.path[1:]) != database:
        raise ValueError("MONGODB_URL must select the matching run-owned database")


def verify_run_ownership(database_url, mongo_url, database, run_id, owner_token):
    prefix = "apexgrid_acceptance_"
    if not run_id or database != f"{prefix}{run_id}" or not owner_token:
        raise RuntimeError("Acceptance requires a matching run id and ownership token")
    with psycopg.connect(database_url) as db:
        with db.cursor() as cur:
            cur.execute("SELECT shobj_description(oid, 'pg_database') FROM pg_database WHERE datname=current_database()")
            row = cur.fetchone()
    expected = f"apexgrid-acceptance:{run_id}:{owner_token}"
    if not row or row[0] != expected:
        raise RuntimeError("Acceptance database ownership marker is missing or mismatched")
    with MongoClient(mongo_url, serverSelectionTimeoutMS=5000) as client:
        marker = client[database]["acceptance_metadata"].find_one({"_id": "run_owner"})
        if not marker or marker.get("run_id") != run_id or marker.get("owner_token") != owner_token:
            raise RuntimeError("Acceptance MongoDB ownership marker is missing or mismatched")


def start_owned_api(database_url, mongo_url):
    global API
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    process = None
    try:
        sock.bind(("127.0.0.1", 0))
        sock.listen(socket.SOMAXCONN)
        port = sock.getsockname()[1]
        API = f"http://127.0.0.1:{port}/api"
        child_env = os.environ.copy()
        child_env["DATABASE_URL"] = database_url
        child_env["MONGODB_URL"] = mongo_url
        child_env["MONGODB_DATABASE"] = unquote(urlparse(mongo_url).path.lstrip("/"))
        child_env["AUTO_DEMO_RACE"] = "0"
        child_env.pop("API_URL", None)
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--fd",
             str(sock.fileno()), "--log-level", "warning"],
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            env=child_env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            pass_fds=(sock.fileno(),),
        )
    except Exception:
        sock.close()
        if process is not None:
            stop_owned_api(process)
        raise
    sock.close()
    try:
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError("Owned acceptance API exited before becoming healthy")
            try:
                health = expect("/health")
                if health.get("services") == {"postgres": "up", "mongodb": "up"} and process.poll() is None:
                    return process
            except (OSError, urllib.error.URLError, AssertionError, ValueError):
                pass
            time.sleep(0.25)
        raise RuntimeError("Owned acceptance API did not become healthy within 30 seconds")
    except Exception:
        stop_owned_api(process)
        raise


def stop_owned_api(process):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def create_owned_fixture(token, circuit_id, unique_suffix):
    championships = expect("/championships?limit=200&offset=0", token)
    used_seasons = {row["season"] for row in championships}
    season = datetime.now(timezone.utc).year + 100
    while season in used_seasons:
        season += 1
    championship = None
    event = None
    try:
        championship = expect("/championships", token, {
            "name": f"Acceptance Test {unique_suffix}", "season": season,
        }, method="POST", status=201)
        event = expect("/events", token, {
            "championship_id": championship["id"], "circuit_id": circuit_id,
            "round_number": 3, "name": f"Acceptance Test Round 3 {unique_suffix}",
            "start_date": datetime.now(timezone.utc).date().isoformat(),
        }, method="POST", status=201)
    except Exception:
        if championship and championship.get("id"):
            try:
                expect(f"/championships/{championship['id']}", token, method="DELETE", status=204)
            except Exception:
                pass
        raise
    return {
        "championship_id": championship["id"], "season": season,
        "event_id": event["id"], "unique_suffix": unique_suffix,
    }


def cleanup_owned_fixture(token, fixture):
    event_id = fixture.get("event_id")
    championship_id = fixture.get("championship_id")
    if event_id:
        for path, id_key in (("/sessions?limit=200&offset=0", "event_id"),
                             ("/results?limit=200&offset=0", "event_id")):
            for row in expect(path, token):
                if row.get(id_key) == event_id and row.get("id"):
                    expect(f"{path.split('?')[0]}/{row['id']}", token, method="DELETE", status=204)
        expect(f"/events/{event_id}", token, method="DELETE", status=204)
    if championship_id:
        expect(f"/championships/{championship_id}", token, method="DELETE", status=204)


def assert_penalty_guard_enabled(cur):
    cur.execute("""SELECT tgenabled FROM pg_trigger
        WHERE tgrelid='penalties'::regclass AND tgname='trg_penalties_immutable' AND NOT tgisinternal""")
    row = cur.fetchone()
    if not row or row[0] != "O":
        raise RuntimeError("Apply the penalty immutability migration before running acceptance")


def _run_acceptance(database):
    mongo_database = unquote(urlparse(MONGO_URL or "").path.lstrip("/"))
    health = expect("/health")
    assert health["services"] == {"postgres": "up", "mongodb": "up"}
    token = expect("/auth/login", body={"email": "admin@apexgrid.test", "password": "ApexGrid2026!"})["access_token"]
    circuit = next(iter(expect("/circuits", token)))
    fixture = create_owned_fixture(token, circuit["id"], UUID(int=0).hex[:12] + "-" + os.urandom(4).hex())
    championship = next(row for row in expect("/championships", token)
                        if row["id"] == fixture["championship_id"])
    event = next(row for row in expect("/events?limit=200&offset=0", token)
                 if row["id"] == fixture["event_id"])
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
    mongo = MongoClient(MONGO_URL)[database]["telemetry"]
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
        try:
            if demo_session_id:
                request(f"/demo-races/{demo_session_id}", token, method="DELETE")
            if session_id:
                request(f"/sessions/{session_id}/simulate", token, {"action": "stop"})
                mongo.delete_many({"session_id": session_id})
        finally:
            mongo.database.client.close()
        # Official penalties are immutable. The operator-owned lifecycle must stop
        # this API and drop this exact run-owned database after the process exits.


def main():
    global MONGO_URL
    mongo_database = unquote(urlparse(MONGO_URL or "").path.lstrip("/"))
    database = ensure_disposable_target(DATABASE_URL, mongo_database)
    ensure_mongo_target(MONGO_URL, database)
    run_id = os.getenv("ACCEPTANCE_RUN_ID", "")
    owner_token = os.getenv("ACCEPTANCE_OWNERSHIP_TOKEN", "")
    verify_run_ownership(DATABASE_URL, MONGO_URL, database, run_id, owner_token)
    process = start_owned_api(DATABASE_URL, MONGO_URL)
    try:
        _run_acceptance(database)
    finally:
        stop_owned_api(process)


if __name__ == "__main__":
    main()
