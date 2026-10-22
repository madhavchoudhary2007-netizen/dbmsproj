"""Seeded read characterization for telemetry and live session routes."""

import os
from datetime import UTC, datetime
from uuid import uuid4

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


@pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="requires seeded PostgreSQL")
def test_seeded_telemetry_and_live_read_contract(database_api_client):
    client = database_api_client
    admin = _login(client, "admin@apexgrid.test")
    driver = _login(client, "driver01@apexgrid.test")
    client.cookies.clear()

    session_response = client.get("/api/sessions", headers=admin)
    drivers_response = client.get("/api/drivers", headers=admin)
    assert session_response.status_code == drivers_response.status_code == 200
    session_id = session_response.json()[0]["id"]
    driver_ids = [item["id"] for item in drivers_response.json()[:2]]
    assert len(driver_ids) == 2

    telemetry_url = f"/api/telemetry?session_id={session_id}"
    live_url = f"/api/sessions/{session_id}/live"
    for url in (telemetry_url, live_url):
        assert client.get(url).status_code == 401

    collection = main_module.telemetry_collection
    assert collection is not None
    inserted_ids = []
    base = datetime(9998, 1, 1, tzinfo=UTC)
    packet_keys = {
        "id", "session_id", "driver_id", "ts", "lap", "sector", "elapsed_ms",
        "lap_time_ms", "sector_ms", "position", "speed_kph", "throttle_pct",
        "brake_pct", "tire_compound", "tire_age_laps", "tire_wear_pct",
        "tire_temp_c", "pit_state",
    }
    samples = [
        (driver_ids[0], 1),
        (driver_ids[1], 2),
        (driver_ids[0], 3),
    ]
    try:
        for index, (driver_id, lap) in enumerate(samples):
            doc = {
                "_id": ObjectId(),
                "session_id": session_id,
                "driver_id": driver_id,
                "ts": base.replace(microsecond=index * 1000),
                "lap": lap,
                "sector": 1,
                "elapsed_ms": lap * 1000,
                "lap_time_ms": 90000,
                "sector_ms": [30000, 30000, 30000],
                "position": lap,
                "speed_kph": 210,
                "throttle_pct": 100,
                "brake_pct": 0,
                "tire_compound": "MEDIUM",
                "tire_age_laps": 1,
                "tire_wear_pct": 1,
                "tire_temp_c": [80, 81, 82, 83],
                "pit_state": "TRACK",
            }
            inserted_ids.append(collection.insert_one(doc).inserted_id)

        for headers in (admin, driver):
            listed = client.get(telemetry_url, headers=headers)
            assert listed.status_code == 200, listed.text
            assert isinstance(listed.json(), list)
            rows = [row for row in listed.json() if row["id"] in {str(i) for i in inserted_ids}]
            assert [row["id"] for row in rows] == [str(i) for i in reversed(inserted_ids)]
            assert all(set(row) == packet_keys and row["session_id"] == session_id for row in rows)
            assert all(row["ts"].endswith("Z") and row["driver_id"] in driver_ids for row in rows)

            limited = client.get(f"{telemetry_url}&limit=1", headers=headers)
            assert limited.status_code == 200
            assert limited.json()[0]["id"] == str(inserted_ids[-1])

            filtered = client.get(
                f"{telemetry_url}&driver_id={driver_ids[0]}", headers=headers
            )
            assert filtered.status_code == 200
            tagged_filtered = [
                row for row in filtered.json() if row["id"] in {str(i) for i in inserted_ids}
            ]
            assert [row["id"] for row in tagged_filtered] == [
                str(inserted_ids[2]), str(inserted_ids[0])
            ]

            live = client.get(live_url, headers=headers)
            assert live.status_code == 200, live.text
            body = live.json()
            assert set(body) == {"session", "drivers", "packets"}
            assert isinstance(body["session"], dict)
            assert body["session"]["id"] == session_id
            assert isinstance(body["drivers"], list)
            assert isinstance(body["packets"], list)
            inserted_id_strings = {str(item) for item in inserted_ids}
            tagged_live = [p for p in body["packets"] if p["id"] in inserted_id_strings]
            assert [p["id"] for p in tagged_live] == [str(i) for i in inserted_ids]
            assert all(
                set(packet) == packet_keys and packet["session_id"] == session_id
                for packet in tagged_live
            )

        missing_session = str(uuid4())
        missing_telemetry = client.get(
            f"/api/telemetry?session_id={missing_session}", headers=admin
        )
        assert missing_telemetry.status_code == 404
        missing_live = client.get(f"/api/sessions/{missing_session}/live", headers=admin)
        assert missing_live.status_code == 404
    finally:
        for inserted_id in inserted_ids:
            collection.delete_one({"_id": inserted_id})
