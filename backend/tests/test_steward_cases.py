from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ.setdefault("APP_ENV", "local")

from backend.app.api import stewards
from backend.app.api.laps import current_user, get_race_db
from backend.app.main import app

SESSION_ID = "a2100000-0000-4000-8000-000000000001"
DRIVER_ID = "a2100000-0000-4000-8000-000000000002"
INCIDENT_ID = UUID("a2100000-0000-4000-8000-000000000003")


class _Cursor:
    def __init__(self, *, total_laps: int | None = 30, incident_state: str = "OPEN") -> None:
        self.total_laps = total_laps
        self.incident_state = incident_state
        self.executed: list[tuple[str, tuple[Any, ...]]] = []
        self.row: dict[str, Any] | None = None

    def __enter__(self) -> _Cursor:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def execute(self, query: str, params: tuple[Any, ...] = ()) -> None:
        self.executed.append((query, params))
        if query.startswith("SELECT total_laps"):
            self.row = {"total_laps": self.total_laps} if self.total_laps is not None else None
        elif query.startswith("SELECT 1 FROM demo_races"):
            self.row = None
        elif query.startswith("SELECT 1 FROM demo_race_entries"):
            self.row = {"?column?": 1}
        elif query.startswith("INSERT INTO incident_reports"):
            self.row = {
                "id": INCIDENT_ID,
                "session_id": params[0],
                "driver_id": params[1],
                "lap": params[2],
                "description": params[3],
                "state": "OPEN",
            }
        elif query.startswith("SELECT * FROM incident_reports"):
            self.row = {
                "id": INCIDENT_ID,
                "session_id": UUID(SESSION_ID),
                "driver_id": UUID(DRIVER_ID),
                "state": self.incident_state,
            }
        elif query.startswith("UPDATE incident_reports"):
            self.row = {
                "id": INCIDENT_ID,
                "session_id": UUID(SESSION_ID),
                "driver_id": UUID(DRIVER_ID),
                "state": params[0],
                "decided_by": params[1],
                "decision_notes": params[2],
            }
        elif query.startswith("INSERT INTO penalties"):
            self.row = {
                "id": "penalty-1",
                "incident_id": params[0],
                "driver_id": params[1],
                "points": params[2],
                "time_seconds": params[3],
                "grid_places": params[4],
            }
        elif query.startswith("SELECT d.eligibility"):
            self.row = {"eligibility": "ELIGIBLE", "season_points": 3}
        else:
            self.row = None

    def fetchone(self) -> dict[str, Any] | None:
        return self.row


class _Connection:
    def __init__(self, cursor: _Cursor) -> None:
        self._cursor = cursor

    def __enter__(self) -> _Connection:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def cursor(self, **_kwargs: Any) -> _Cursor:
        return self._cursor


class _Database:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Any]] = []

    def fetch_all(self, query: str, params: Any = ()) -> list[dict[str, Any]]:
        self.calls.append((query, params))
        return [{"id": str(INCIDENT_ID), "state": "OPEN"}]


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Any:
    previous_overrides = app.dependency_overrides.copy()
    cursor = _Cursor()
    database = _Database()
    user: dict[str, Any] = {"id": "steward-1", "role": "STEWARD"}
    events: list[tuple[Any, ...]] = []
    app.dependency_overrides[current_user] = lambda: user
    app.dependency_overrides[get_race_db] = lambda: database

    @contextmanager
    def connection() -> Any:
        yield _Connection(cursor)

    monkeypatch.setattr(stewards, "_get_connection", lambda _database=None: connection())
    monkeypatch.setattr(
        stewards,
        "_resolve_publish",
        lambda _bus=None: lambda *args: events.append(args),
    )
    try:
        yield TestClient(app), cursor, database, user, events
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)


def test_driver_cannot_create_incident_and_steward_can_create_and_publish(client: Any) -> None:
    api, cursor, _database, user, events = client
    body = {
        "session_id": SESSION_ID,
        "driver_id": DRIVER_ID,
        "lap": 8,
        "description": "Unsafe rejoin after pit exit",
    }

    user.update(id="driver-1", role="DRIVER")
    denied = api.post("/api/incidents", json=body)
    assert denied.status_code == 403
    assert denied.json() == {"detail": "Insufficient role"}
    assert cursor.executed == []

    user.update(id="steward-1", role="STEWARD")
    created = api.post("/api/incidents", json=body)
    assert created.status_code == 201
    assert created.json() == {
        "id": str(INCIDENT_ID),
        "session_id": SESSION_ID,
        "driver_id": DRIVER_ID,
        "lap": 8,
        "description": "Unsafe rejoin after pit exit",
        "state": "OPEN",
    }
    assert [query for query, _ in cursor.executed] == [
        "SELECT total_laps FROM race_sessions WHERE id=%s",
        "SELECT 1 FROM demo_races WHERE session_id=%s",
        (
            "INSERT INTO incident_reports(session_id,driver_id,lap,description) "
            "VALUES (%s,%s,%s,%s) RETURNING *"
        ),
    ]
    assert cursor.executed[-1][1] == (UUID(SESSION_ID), UUID(DRIVER_ID), 8, body["description"])
    assert events == [(UUID(SESSION_ID), "incident.update", created.json())]


@pytest.mark.parametrize(
    ("body", "expected_status", "expected_detail"),
    [
        (
            {"session_id": SESSION_ID, "driver_id": DRIVER_ID, "lap": 0, "description": "Bad"},
            422,
            None,
        ),
        (
            {
                "session_id": SESSION_ID,
                "driver_id": DRIVER_ID,
                "lap": 31,
                "description": "Beyond session",
            },
            422,
            "Incident lap exceeds the session lap count",
        ),
        (
            {"session_id": SESSION_ID, "driver_id": DRIVER_ID, "lap": 3, "description": "ok"},
            422,
            None,
        ),
    ],
)
def test_incident_create_validates_payload_and_session_lap_limit(
    client: Any, body: dict[str, Any], expected_status: int, expected_detail: str | None
) -> None:
    api, cursor, _database, _user, events = client

    response = api.post("/api/incidents", json=body)

    assert response.status_code == expected_status
    if expected_detail is not None:
        assert response.json() == {"detail": expected_detail}
    assert not any(query.startswith("INSERT INTO incident_reports") for query, _ in cursor.executed)
    assert events == []


def test_incident_list_filters_and_pages_with_state_validation(client: Any) -> None:
    api, _cursor, database, _user, _events = client

    response = api.get("/api/incidents?state=OPEN&limit=5&offset=2")
    invalid = api.get("/api/incidents?state=IGNORED")

    assert response.status_code == 200
    assert response.json() == [{"id": str(INCIDENT_ID), "state": "OPEN"}]
    query, params = database.calls[0]
    assert "WHERE i.state=%s" in query
    assert params == ["OPEN", 5, 2]
    assert invalid.status_code == 422
    assert invalid.json() == {"detail": "Invalid incident state"}
    assert len(database.calls) == 1


def test_approved_decision_records_authenticated_actor_penalty_and_publishes(client: Any) -> None:
    api, cursor, _database, user, events = client
    user.update(id="known-steward", role="STEWARD")
    body = {
        "approve": True,
        "notes": "Unsafe rejoin",
        "points": 4,
        "actor": "forged-client-actor",
        "role": "ADMIN",
    }

    response = api.post(f"/api/incidents/{INCIDENT_ID}/decision", json=body)

    assert response.status_code == 200
    result = response.json()
    assert result == {
        "incident": {
            "id": str(INCIDENT_ID),
            "session_id": SESSION_ID,
            "driver_id": DRIVER_ID,
            "state": "APPROVED",
            "decided_by": "known-steward",
            "decision_notes": "Unsafe rejoin",
        },
        "penalty": {
            "id": "penalty-1",
            "incident_id": str(INCIDENT_ID),
            "driver_id": DRIVER_ID,
            "points": 4,
            "time_seconds": 0,
            "grid_places": 0,
        },
        "driver": {"eligibility": "ELIGIBLE", "season_points": 3},
    }
    actor_calls = [
        (query, params) for query, params in cursor.executed if "apexgrid.actor" in query
    ]
    role_calls = [
        (query, params) for query, params in cursor.executed if "apexgrid.role" in query
    ]
    penalty_call = next(
        params for query, params in cursor.executed if query.startswith("INSERT INTO penalties")
    )
    assert actor_calls == [("SELECT set_config('apexgrid.actor', %s, true)", ("known-steward",))]
    assert role_calls == [("SELECT set_config('apexgrid.role', %s, true)", ("steward",))]
    assert penalty_call == (INCIDENT_ID, UUID(DRIVER_ID), 4, 0, 0)
    assert "forged-client-actor" not in repr(cursor.executed)
    assert events == [(UUID(SESSION_ID), "incident.update", result)]


def test_rejected_decision_has_no_penalty_and_closed_incident_cannot_be_decided_twice(
    client: Any,
) -> None:
    api, cursor, _database, _user, events = client

    rejected = api.post(
        f"/api/incidents/{INCIDENT_ID}/decision",
        json={"approve": False, "notes": "Insufficient evidence", "points": 7},
    )
    assert rejected.status_code == 200
    assert rejected.json()["incident"]["state"] == "REJECTED"
    assert rejected.json()["penalty"] is None
    assert not any(query.startswith("INSERT INTO penalties") for query, _ in cursor.executed)
    assert not any("apexgrid.actor" in query for query, _ in cursor.executed)
    assert events == [(UUID(SESSION_ID), "incident.update", rejected.json())]

    cursor.incident_state = "APPROVED"
    decided_again = api.post(
        f"/api/incidents/{INCIDENT_ID}/decision", json={"approve": True, "points": 2}
    )
    assert decided_again.status_code == 409
    assert decided_again.json() == {"detail": "Incident has already been decided"}
    assert events == [(UUID(SESSION_ID), "incident.update", rejected.json())]


@pytest.mark.parametrize(
    ("body", "expected_status"),
    [
        ({"approve": True, "points": -1}, 422),
        ({"approve": True, "points": 13}, 422),
        ({"approve": True, "time_seconds": 1}, 422),
        ({"approve": True, "grid_places": 1}, 422),
    ],
)
def test_decision_rejects_invalid_or_unsupported_penalties_without_writes(
    client: Any, body: dict[str, Any], expected_status: int
) -> None:
    api, cursor, _database, _user, events = client

    response = api.post(f"/api/incidents/{INCIDENT_ID}/decision", json=body)

    assert response.status_code == expected_status
    assert cursor.executed == []
    assert events == []
