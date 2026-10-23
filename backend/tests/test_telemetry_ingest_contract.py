"""Seeded write characterization for telemetry ingest."""

import os
from datetime import datetime, timedelta

import pytest
from app import main as main_module
from app.main import app
from bson import ObjectId
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def database_api_client():
    with TestClient(app) as client:
        yield client


def _login(client, email):
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "ApexGrid2026!"},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _packet(session_id, driver_id, latest_packet):
    lap_time_ms = 90123
    latest_ts = datetime.fromisoformat(latest_packet["ts"].replace("Z", "+00:00"))
    return {
        "session_id": session_id,
        "driver_id": driver_id,
        "ts": (latest_ts + timedelta(milliseconds=lap_time_ms)).isoformat().replace("+00:00", "Z"),
        "lap": latest_packet["lap"] + 1,
        "sector": 0,
        "elapsed_ms": latest_packet["elapsed_ms"] + lap_time_ms,
        "lap_time_ms": lap_time_ms,
        "sector_ms": [30100, 30000, 30023],
        "position": 1,
        "speed_kph": 210.5,
        "throttle_pct": 82.0,
        "brake_pct": 3.0,
        "tire_compound": "MEDIUM",
        "tire_age_laps": 2,
        "tire_wear_pct": 4.5,
        "tire_temp_c": [80.0, 82.0, 79.0, 81.0],
        "pit_state": "TRACK",
    }


def _latest_packet(client, admin, session_id, driver_id):
    current = client.get(f"/api/telemetry?session_id={session_id}", headers=admin)
    assert current.status_code == 200, current.text
    driver_packets = [row for row in current.json() if row["driver_id"] == driver_id]
    assert driver_packets, "generated race should have current driver telemetry"
    return max(
        driver_packets,
        key=lambda row: (row["lap"], row["sector"], row["elapsed_ms"]),
    )


PACKET_KEYS = {
    "id",
    "session_id",
    "driver_id",
    "ts",
    "lap",
    "sector",
    "elapsed_ms",
    "lap_time_ms",
    "last_lap_ms",
    "sector_ms",
    "position",
    "speed_kph",
    "throttle_pct",
    "brake_pct",
    "tire_compound",
    "tire_age_laps",
    "tire_wear_pct",
    "tire_temp_c",
    "pit_state",
    "pit_reservation_id",
    "pit_box_number",
    "pit_team_id",
    "pit_starts_at",
    "pit_ends_at",
}


def _assert_role_rejections(client, driver, packet):
    assert client.post("/api/telemetry/ingest", json=packet).status_code == 401
    rejected = client.post("/api/telemetry/ingest", headers=driver, json=packet)
    assert rejected.status_code == 403


def _assert_persisted_and_readable(client, admin, collection, packet, response, inserted_id):
    body = response.json()
    assert set(body) == {"accepted", "packet"}
    assert body["accepted"] is True
    result_packet = body["packet"]
    assert set(result_packet) == PACKET_KEYS
    assert {key: result_packet[key] for key in packet} == packet
    stored = collection.find_one({"_id": inserted_id})
    assert stored is not None
    assert stored["session_id"] == packet["session_id"]
    assert stored["driver_id"] == packet["driver_id"]
    assert stored["lap"] == packet["lap"]
    assert stored["elapsed_ms"] == packet["elapsed_ms"]

    listed = client.get(f"/api/telemetry?session_id={packet['session_id']}", headers=admin)
    assert listed.status_code == 200, listed.text
    matching = [row for row in listed.json() if row["id"] == str(inserted_id)]
    assert len(matching) == 1
    assert set(matching[0]) == PACKET_KEYS
    assert matching[0] == result_packet


def _assert_inactive_rejected(client, admin, packet):
    sessions = client.get("/api/sessions", headers=admin)
    assert sessions.status_code == 200, sessions.text
    inactive = next((row for row in sessions.json() if row["state"] != "ACTIVE"), None)
    if inactive:
        rejected = client.post(
            "/api/telemetry/ingest",
            headers=admin,
            json={**packet, "session_id": inactive["id"]},
        )
        assert rejected.status_code == 409


@pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="requires seeded PostgreSQL")
def test_seeded_telemetry_ingest_write_contract(database_api_client):
    client = database_api_client
    admin = _login(client, "admin@apexgrid.test")
    driver = _login(client, "driver01@apexgrid.test")
    client.cookies.clear()

    created = client.post("/api/demo-races", headers=admin, json={"cars": 6})
    assert created.status_code == 201, created.text
    session_id = created.json()["session_id"]
    collection = main_module.telemetry_collection
    inserted_id = None
    try:
        assert collection is not None
        live = client.get(f"/api/sessions/{session_id}/live", headers=admin)
        assert live.status_code == 200, live.text
        driver_id = live.json()["drivers"][0]["id"]
        packet = _packet(
            session_id, driver_id, _latest_packet(client, admin, session_id, driver_id)
        )
        _assert_role_rejections(client, driver, packet)
        packet = _packet(
            session_id, driver_id, _latest_packet(client, admin, session_id, driver_id)
        )
        accepted = client.post("/api/telemetry/ingest", headers=admin, json=packet)
        assert accepted.status_code == 202, accepted.text
        inserted_id = ObjectId(accepted.json()["packet"]["id"])
        _assert_persisted_and_readable(client, admin, collection, packet, accepted, inserted_id)
        _assert_inactive_rejected(client, admin, packet)
    finally:
        if collection is not None and inserted_id is not None:
            collection.delete_one({"_id": inserted_id})
        deleted = client.delete(f"/api/demo-races/{session_id}", headers=admin)
        assert deleted.status_code == 204, deleted.text
