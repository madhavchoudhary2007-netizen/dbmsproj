"""Behaviour tests for the stewards incident API and its router factory.

The factory-built router (create_stewards_router) is exercised against the
disposable PostgreSQL stack. Every request shares one connection whose
transaction is rolled back at teardown, so no test leaves rows behind. The
resolver helpers are covered with fake main-module namespaces so both the
"main loaded" and "main absent" fallbacks are asserted.
"""

from __future__ import annotations

import os
import sys
import types
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import datetime
from typing import Any
from uuid import uuid4

import psycopg
import pytest
from app import database as db_module
from app.api import stewards
from app.core.events import EventBus
from app.core.request_auth import current_user
from app.core.request_database import DatabaseSession
from app.core.serialization import jsonable
from app.core.validation import limit_offset
from app.main import app
from app.simulation_core import MAX_SESSION_LAPS
from fastapi import FastAPI
from fastapi.testclient import TestClient
from psycopg.rows import dict_row

MAIN_MODULE = "backend.app.main"


@pytest.fixture
def txn() -> Iterator[psycopg.Connection]:
    conn = psycopg.connect(os.environ["DATABASE_URL"])
    try:
        yield conn
    finally:
        conn.rollback()
        conn.close()


@pytest.fixture
def refs(txn: psycopg.Connection) -> dict[str, Any]:
    with txn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT id, total_laps FROM race_sessions s WHERE total_laps > 0"
            " AND total_laps < %s AND NOT EXISTS (SELECT 1 FROM demo_races dr"
            " WHERE dr.session_id = s.id) ORDER BY id LIMIT 1",
            (MAX_SESSION_LAPS,),
        )
        session = cur.fetchone()
        cur.execute("SELECT id FROM drivers ORDER BY id LIMIT 1")
        driver = cur.fetchone()
        cur.execute("SELECT id FROM users ORDER BY id LIMIT 1")
        user = cur.fetchone()
    assert session and driver and user, "seeded PostgreSQL stack is required"
    return {
        "session_id": session["id"],
        "total_laps": session["total_laps"],
        "driver_id": driver["id"],
        "user_id": user["id"],
    }


def _one(conn: psycopg.Connection, sql: str, params: tuple[Any, ...] = ()) -> tuple[Any, ...]:
    with conn.cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
    assert row is not None
    return tuple(row)


def _db_adapters(conn: psycopg.Connection) -> tuple[Callable[[], Any], Callable[..., Any]]:
    @contextmanager
    def connection() -> Iterator[psycopg.Connection]:
        yield conn

    def fetch_all(sql: str, params: Any = ()) -> list[Any]:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, params)
            return cur.fetchall()

    return connection, fetch_all


def _build_router(
    connection: Callable[[], Any], fetch_all: Callable[..., Any]
) -> tuple[Any, dict[str, Callable[..., Any]], list[tuple[str, str, Any]]]:
    published: list[tuple[str, str, Any]] = []

    def publish(session_id: Any, kind: str, data: Any) -> None:
        published.append((str(session_id), kind, data))

    router, handlers = stewards.create_stewards_router(
        fetch_all,
        jsonable,
        limit_offset,
        stewards.authenticated_user_dependency,
        connection,
        publish,
        stewards.admin_steward_dependency,
    )
    return router, handlers, published


def _client(router: Any, user: dict[str, object]) -> TestClient:
    application = FastAPI()
    application.include_router(router)
    application.dependency_overrides[current_user] = lambda: user
    return TestClient(application)


def _stack(
    conn: psycopg.Connection, refs: dict[str, Any], role: str = "ADMIN"
) -> tuple[TestClient, list[tuple[str, str, Any]], Any]:
    connection, fetch_all = _db_adapters(conn)
    router, handlers, published = _build_router(connection, fetch_all)
    user = {"id": str(refs["user_id"]), "role": role}
    return _client(router, user), published, handlers


def _incident_body(refs: dict[str, Any], **overrides: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "session_id": str(refs["session_id"]),
        "driver_id": str(refs["driver_id"]),
        "lap": 3,
        "description": "Contact at turn one",
    }
    body.update(overrides)
    return body


def _open_incident(client: TestClient, refs: dict[str, Any]) -> str:
    response = client.post("/api/incidents", json=_incident_body(refs))
    assert response.status_code == 201, response.text
    incident_id: str = response.json()["id"]
    return incident_id


def _decide(client: TestClient, incident_id: str, **body: Any) -> Any:
    return client.post(f"/api/incidents/{incident_id}/decision", json=body)


def _incident_count(conn: psycopg.Connection, refs: dict[str, Any]) -> int:
    row = _one(
        conn,
        "SELECT count(*) FROM incident_reports WHERE session_id=%s",
        (refs["session_id"],),
    )
    return int(row[0])


def test_steward_creates_open_incident_persists_row_and_publishes(
    txn: psycopg.Connection, refs: dict[str, Any]
) -> None:
    client, published, _ = _stack(txn, refs, role="STEWARD")

    response = client.post("/api/incidents", json=_incident_body(refs))

    assert response.status_code == 201, response.text
    created = response.json()
    assert created["state"] == "OPEN"
    assert created["lap"] == 3
    assert created["description"] == "Contact at turn one"
    assert _one(
        txn,
        "SELECT state, lap, description, session_id::text, driver_id::text"
        " FROM incident_reports WHERE id=%s",
        (created["id"],),
    ) == ("OPEN", 3, "Contact at turn one", str(refs["session_id"]), str(refs["driver_id"]))
    assert len(published) == 1
    session_id, kind, data = published[0]
    assert (session_id, kind) == (str(refs["session_id"]), "incident.update")
    assert data["id"] == created["id"]


def test_driver_role_cannot_create_incident_and_nothing_is_written(
    txn: psycopg.Connection, refs: dict[str, Any]
) -> None:
    client, published, _ = _stack(txn, refs, role="DRIVER")
    before = _incident_count(txn, refs)

    response = client.post("/api/incidents", json=_incident_body(refs))

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient role"
    assert _incident_count(txn, refs) == before
    assert published == []


@pytest.mark.parametrize(
    "override",
    [
        {"lap": 0},
        {"lap": MAX_SESSION_LAPS + 1},
        {"description": "no"},
        {"driver_id": "not-a-uuid"},
    ],
)
def test_invalid_incident_payload_is_422_and_writes_nothing(
    txn: psycopg.Connection, refs: dict[str, Any], override: dict[str, Any]
) -> None:
    client, published, _ = _stack(txn, refs)
    before = _incident_count(txn, refs)

    response = client.post("/api/incidents", json=_incident_body(refs, **override))

    assert response.status_code == 422
    assert _incident_count(txn, refs) == before
    assert published == []


def test_unknown_session_is_404_and_writes_nothing(
    txn: psycopg.Connection, refs: dict[str, Any]
) -> None:
    client, published, _ = _stack(txn, refs)
    missing = str(uuid4())

    response = client.post("/api/incidents", json=_incident_body(refs, session_id=missing))

    assert response.status_code == 404
    assert response.json()["detail"] == "Session not found"
    assert _one(
        txn, "SELECT count(*) FROM incident_reports WHERE session_id=%s", (missing,)
    ) == (0,)
    assert published == []


def test_lap_beyond_session_length_is_422_and_writes_nothing(
    txn: psycopg.Connection, refs: dict[str, Any]
) -> None:
    client, published, _ = _stack(txn, refs)
    before = _incident_count(txn, refs)

    response = client.post(
        "/api/incidents", json=_incident_body(refs, lap=refs["total_laps"] + 1)
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Incident lap exceeds the session lap count"
    assert _incident_count(txn, refs) == before
    assert published == []


def test_incident_list_filters_by_state_and_reports_joined_context(
    txn: psycopg.Connection, refs: dict[str, Any]
) -> None:
    client, _, _ = _stack(txn, refs)
    incident_id = _open_incident(client, refs)

    open_rows = client.get("/api/incidents", params={"state": "OPEN", "limit": 200})
    assert open_rows.status_code == 200, open_rows.text
    matches = [row for row in open_rows.json() if row["id"] == incident_id]
    assert len(matches) == 1
    assert {"driver_name", "number", "session_type", "event_name"} <= set(matches[0])
    assert all(row["state"] == "OPEN" for row in open_rows.json())

    approved = client.get("/api/incidents", params={"state": "APPROVED", "limit": 200})
    assert approved.status_code == 200
    assert incident_id not in {row["id"] for row in approved.json()}


@pytest.mark.parametrize(
    "params",
    [
        {"state": "PENDING"},
        {"limit": 0},
        {"limit": 201},
        {"offset": -1},
    ],
)
def test_incident_list_rejects_bad_query_parameters(
    txn: psycopg.Connection, refs: dict[str, Any], params: dict[str, Any]
) -> None:
    client, _, _ = _stack(txn, refs)

    response = client.get("/api/incidents", params=params)

    assert response.status_code == 422
    if "state" in params:
        assert response.json()["detail"] == "Invalid incident state"


def test_approving_with_points_writes_penalty_and_returns_snapshot(
    txn: psycopg.Connection, refs: dict[str, Any]
) -> None:
    client, published, _ = _stack(txn, refs)
    incident_id = _open_incident(client, refs)

    response = _decide(client, incident_id, approve=True, notes="Track limits", points=3)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["incident"]["state"] == "APPROVED"
    assert body["incident"]["decision_notes"] == "Track limits"
    assert str(body["incident"]["decided_by"]) == str(refs["user_id"])
    assert str(body["penalty"]["incident_id"]) == incident_id
    assert body["penalty"]["points"] == 3
    assert body["penalty"]["time_seconds"] == 0
    assert body["penalty"]["grid_places"] == 0
    assert body["driver"] is not None
    assert "eligibility" in body["driver"]
    assert "season_points" in body["driver"]
    assert _one(
        txn,
        "SELECT state, decided_by::text, decision_notes FROM incident_reports WHERE id=%s",
        (incident_id,),
    ) == ("APPROVED", str(refs["user_id"]), "Track limits")
    assert _one(
        txn,
        "SELECT count(*), COALESCE(SUM(points), 0) FROM penalties WHERE incident_id=%s",
        (incident_id,),
    ) == (1, 3)
    assert published[-1][0] == str(refs["session_id"])
    assert published[-1][1] == "incident.update"
    assert published[-1][2]["incident"]["state"] == "APPROVED"


@pytest.mark.parametrize(
    ("approve", "points", "expect_penalty"),
    [(True, 0, False), (False, 5, False), (True, 4, True)],
)
def test_decision_state_and_penalty_row_follow_the_approval_flags(
    txn: psycopg.Connection,
    refs: dict[str, Any],
    approve: bool,
    points: int,
    expect_penalty: bool,
) -> None:
    client, _, _ = _stack(txn, refs, role="STEWARD")
    incident_id = _open_incident(client, refs)

    response = _decide(client, incident_id, approve=approve, points=points)

    assert response.status_code == 200, response.text
    body = response.json()
    expected_state = "APPROVED" if approve else "REJECTED"
    assert body["incident"]["state"] == expected_state
    assert _one(
        txn, "SELECT state FROM incident_reports WHERE id=%s", (incident_id,)
    ) == (expected_state,)
    if expect_penalty:
        assert body["penalty"]["points"] == points
    else:
        assert body["penalty"] is None
    assert _one(
        txn,
        "SELECT count(*), COALESCE(SUM(points), 0) FROM penalties WHERE incident_id=%s",
        (incident_id,),
    ) == ((1, points) if expect_penalty else (0, 0))


def test_second_decision_conflicts_and_keeps_first_outcome(
    txn: psycopg.Connection, refs: dict[str, Any]
) -> None:
    client, _, _ = _stack(txn, refs)
    incident_id = _open_incident(client, refs)
    assert _decide(client, incident_id, approve=True, points=2).status_code == 200

    conflict = _decide(client, incident_id, approve=False)

    assert conflict.status_code == 409
    assert conflict.json()["detail"] == "Incident has already been decided"
    assert _one(
        txn, "SELECT state FROM incident_reports WHERE id=%s", (incident_id,)
    ) == ("APPROVED",)
    assert _one(
        txn,
        "SELECT count(*), COALESCE(SUM(points), 0) FROM penalties WHERE incident_id=%s",
        (incident_id,),
    ) == (1, 2)


def test_decision_on_unknown_incident_is_404(
    txn: psycopg.Connection, refs: dict[str, Any]
) -> None:
    client, published, _ = _stack(txn, refs)

    response = _decide(client, str(uuid4()), approve=True)

    assert response.status_code == 404
    assert response.json()["detail"] == "Incident not found"
    assert published == []


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"approve": True, "points": 13},
        {"approve": True, "time_seconds": 5},
        {"approve": True, "grid_places": 2},
    ],
)
def test_decision_body_validation_rejects_before_any_write(
    txn: psycopg.Connection, refs: dict[str, Any], body: dict[str, Any]
) -> None:
    client, published, _ = _stack(txn, refs)
    incident_id = _open_incident(client, refs)
    published.clear()

    response = client.post(f"/api/incidents/{incident_id}/decision", json=body)

    assert response.status_code == 422
    assert _one(
        txn, "SELECT state FROM incident_reports WHERE id=%s", (incident_id,)
    ) == ("OPEN",)
    assert _one(
        txn, "SELECT count(*) FROM penalties WHERE incident_id=%s", (incident_id,)
    ) == (0,)
    assert published == []


def test_driver_role_cannot_decide_and_incident_stays_open(
    txn: psycopg.Connection, refs: dict[str, Any]
) -> None:
    steward_client, _, _ = _stack(txn, refs, role="STEWARD")
    incident_id = _open_incident(steward_client, refs)
    driver_client, published, _ = _stack(txn, refs, role="DRIVER")

    response = _decide(driver_client, incident_id, approve=True, points=3)

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient role"
    assert _one(
        txn, "SELECT state FROM incident_reports WHERE id=%s", (incident_id,)
    ) == ("OPEN",)
    assert published == []


def test_factory_handler_map_matches_the_registered_routes(txn: psycopg.Connection) -> None:
    connection, fetch_all = _db_adapters(txn)
    router, handlers, _ = _build_router(connection, fetch_all)

    assert set(handlers) == {"get_incidents", "create_incident", "decide_incident"}
    assert len(router.routes) == 3
    assert {route.endpoint for route in router.routes} == set(handlers.values())


class _FakeCursor:
    def __init__(self, log: list[str]) -> None:
        self.log = log
        self.row: dict[str, Any] | None = None

    def __enter__(self) -> _FakeCursor:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def execute(self, sql: str, params: Any = ()) -> None:
        self.log.append(sql)
        if sql.startswith("SELECT total_laps"):
            self.row = {"total_laps": 30}
        elif sql.startswith("SELECT 1 FROM demo_races"):
            self.row = {"?column?": 1}
        else:
            self.row = None

    def fetchone(self) -> dict[str, Any] | None:
        return self.row


class _FakeConnection:
    def __init__(self) -> None:
        self.log: list[str] = []

    def cursor(self, row_factory: Any = None) -> _FakeCursor:
        return _FakeCursor(self.log)


def test_generated_race_rejects_drivers_outside_entry_list_without_insert(
    refs: dict[str, Any],
) -> None:
    fake = _FakeConnection()

    @contextmanager
    def connection() -> Iterator[_FakeConnection]:
        yield fake

    router, _handlers, published = _build_router(connection, lambda sql, params=(): [])
    client = _client(router, {"id": str(refs["user_id"]), "role": "ADMIN"})

    response = client.post("/api/incidents", json=_incident_body(refs))

    assert response.status_code == 422
    assert response.json()["detail"] == "Driver is not entered in this generated race"
    assert not any(sql.startswith("INSERT INTO incident_reports") for sql in fake.log)
    assert published == []


def test_incident_routes_on_the_live_app_reject_anonymous_callers() -> None:
    with TestClient(app) as client:
        assert client.get("/api/incidents").status_code == 401
        assert (
            client.post("/api/incidents", json={"lap": 1}).status_code == 401
        )
        assert (
            client.post(
                f"/api/incidents/{uuid4()}/decision", json={"approve": True}
            ).status_code
            == 401
        )


class _RecordingBus:
    def __init__(self) -> None:
        self.events: list[tuple[Any, dict[str, Any]]] = []

    def send(self, sid: Any, event: dict[str, Any]) -> None:
        self.events.append((sid, event))


def _install_main(monkeypatch: pytest.MonkeyPatch, **attrs: Any) -> None:
    monkeypatch.setitem(sys.modules, MAIN_MODULE, types.SimpleNamespace(**attrs))


def test_resolve_db_routes_queries_through_the_loaded_main_functions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, tuple[Any, ...]]] = []

    def fetch_all(sql: str, params: Any = ()) -> list[dict[str, int]]:
        calls.append((sql, tuple(params)))
        return [{"n": 1}]

    def fetch_one(sql: str, params: Any = ()) -> dict[str, int]:
        calls.append((sql, tuple(params)))
        return {"n": 2}

    _install_main(monkeypatch, fetch_all=fetch_all, fetch_one=fetch_one)

    session = stewards._resolve_db()

    assert isinstance(session, DatabaseSession)
    assert session.fetch_all("SELECT 1", ["x"]) == [{"n": 1}]
    assert session.fetch_one("SELECT 2", ()) == {"n": 2}
    assert calls == [("SELECT 1", ("x",)), ("SELECT 2", ())]


def test_resolve_db_falls_back_to_database_module_when_main_is_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delitem(sys.modules, MAIN_MODULE, raising=False)
    monkeypatch.setattr(db_module, "fetch_all", lambda sql, params=(): [{"from": "module"}])

    session = stewards._resolve_db()

    assert session.fetch_all("SELECT 3", ()) == [{"from": "module"}]


def test_resolve_db_returns_the_database_session_it_was_given() -> None:
    session = _MarkerSession()

    assert stewards._resolve_db(session) is session


class _MarkerSession:
    pass


def test_resolve_bus_prefers_explicit_then_loaded_main_then_fresh_bus(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    explicit = _RecordingBus()
    assert stewards._resolve_bus(explicit) is explicit  # type: ignore[arg-type]

    main_bus = _RecordingBus()
    _install_main(monkeypatch, bus=main_bus)
    assert stewards._resolve_bus() is main_bus  # type: ignore[comparison-overlap]

    _install_main(monkeypatch)
    assert isinstance(stewards._resolve_bus(), EventBus)

    monkeypatch.delitem(sys.modules, MAIN_MODULE, raising=False)
    assert isinstance(stewards._resolve_bus(), EventBus)


def test_default_publisher_wraps_payload_and_sends_to_the_resolved_bus(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delitem(sys.modules, MAIN_MODULE, raising=False)
    bus = _RecordingBus()
    publish = stewards._resolve_publish(bus)  # type: ignore[arg-type]
    session_id = uuid4()

    publish(session_id, "pit.update", {"lap": 4})

    assert len(bus.events) == 1
    sent_sid, event = bus.events[0]
    assert sent_sid is session_id
    assert event["type"] == "pit.update"
    assert event["session_id"] == str(session_id)
    assert event["data"] == {"lap": 4}
    stamp = datetime.fromisoformat(event["ts"].replace("Z", "+00:00"))
    assert stamp.utcoffset().total_seconds() == 0  # type: ignore[union-attr]


def test_resolve_publish_prefers_an_overridden_main_publish(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def default_publish(*_args: Any) -> None:
        return None

    def custom_publish(*_args: Any) -> None:
        return None

    _install_main(monkeypatch, publish=custom_publish, _default_publish=default_publish)

    assert stewards._resolve_publish() is custom_publish


def test_resolve_publish_uses_main_publish_when_no_default_marker_exists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def custom_publish(*_args: Any) -> None:
        return None

    _install_main(monkeypatch, publish=custom_publish)

    assert stewards._resolve_publish() is custom_publish


def test_resolve_publish_ignores_an_unchanged_main_publish(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def shared(*_args: Any) -> None:
        return None

    _install_main(monkeypatch, publish=shared, _default_publish=shared)
    bus = _RecordingBus()

    publish = stewards._resolve_publish(bus)  # type: ignore[arg-type]

    assert publish is not shared
    session_id = uuid4()
    publish(session_id, "incident.update", {"ok": True})
    assert [event["type"] for _, event in bus.events] == ["incident.update"]
    assert bus.events[0][1]["data"] == {"ok": True}
