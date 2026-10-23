"""Seeded read characterization for the pit strategy route."""

import os
from uuid import uuid4

import pytest
from app import main as main_module
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def database_api_client():
    with TestClient(app) as client:
        yield client


@pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="requires seeded PostgreSQL")
def test_seeded_pit_strategy_read_contract(database_api_client):
    client = database_api_client
    seeded = main_module.fetch_one("""SELECT s.id, s.state
        FROM race_sessions s
        WHERE s.session_type='RACE' AND s.state='COMPLETED'
          AND EXISTS (SELECT 1 FROM session_results r WHERE r.session_id=s.id)
          AND NOT EXISTS (SELECT 1 FROM demo_races d WHERE d.session_id=s.id)
        ORDER BY s.scheduled_at, s.id LIMIT 1""")
    assert seeded, "expected a seeded completed historical race session"
    session_id = str(seeded["id"])
    path = f"/api/sessions/{session_id}/pit-strategy"

    client.cookies.clear()
    anonymous = client.get(path)
    assert anonymous.status_code == 401, anonymous.text
    assert anonymous.json() == {"detail": "Authentication required"}
    assert anonymous.headers["www-authenticate"] == "Bearer"

    login = client.post(
        "/api/auth/login",
        json={
            "email": "admin@apexgrid.test",
            "password": "ApexGrid2026!",
        },
    )
    assert login.status_code == 200, login.text
    headers = {"Authorization": "Bearer " + login.json()["access_token"]}
    client.cookies.clear()

    missing = client.get(f"/api/sessions/{uuid4()}/pit-strategy", headers=headers)
    assert missing.status_code == 404, missing.text
    assert missing.json() == {"detail": "Session not found"}

    response = client.get(path, headers=headers)
    assert response.status_code == 200, response.text
    payload = response.json()
    assert set(payload) == {
        "session_id",
        "session_state",
        "source",
        "strategy",
        "historical_summary",
    }
    assert payload["session_id"] == session_id
    assert payload["session_state"] == seeded["state"] == "COMPLETED"
    assert payload["source"] == "history"
    assert isinstance(payload["strategy"], list) and payload["strategy"]
    strategy_keys = {
        "driver_id",
        "driver_name",
        "driver_number",
        "team_id",
        "team_name",
        "current_lap",
        "tire_compound",
        "tire_age_laps",
        "tire_wear_pct",
        "pit_window_start_lap",
        "pit_window_end_lap",
        "recommended_stop_lap",
        "laps_until_decision",
        "status",
        "reason",
        "assigned_box",
        "stops",
    }
    assert all(set(row) == strategy_keys for row in payload["strategy"])
    assert all(row["status"] == "NO_AUTOMATIC_STRATEGY" for row in payload["strategy"])
    assert all("showing recorded stop history" in row["reason"] for row in payload["strategy"])
    summary = payload["historical_summary"]
    assert set(summary) == {"total_stops", "by_driver"}
    assert isinstance(summary["total_stops"], int)
    assert isinstance(summary["by_driver"], list)
    summary_keys = {"driver_id", "driver_name", "team_name", "stop_count", "laps"}
    assert all(set(row) == summary_keys for row in summary["by_driver"])
