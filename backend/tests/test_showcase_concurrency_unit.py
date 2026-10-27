from __future__ import annotations

from collections.abc import Iterator
from contextlib import AbstractContextManager
from pathlib import Path
import os
import sys
from typing import Any

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
_prior_app_env = os.environ.get("APP_ENV")
os.environ.setdefault("APP_ENV", "local")
try:
    from backend.app.api import dbms_showcase
    from backend.app.api.laps import current_user
    from backend.app.main import app
finally:
    if _prior_app_env is None:
        os.environ.pop("APP_ENV", None)
    else:
        os.environ["APP_ENV"] = _prior_app_env


@pytest.fixture
def client() -> Iterator[TestClient]:
    app.dependency_overrides.clear()
    app.dependency_overrides[current_user] = lambda: {
        "id": "synthetic-concurrency-admin",
        "email": "concurrency-admin@example.invalid",
        "role": "ADMIN",
    }
    yield TestClient(app)
    app.dependency_overrides.clear()


class _Transaction(AbstractContextManager["_Transaction"]):
    def __init__(self, connection: _ControlledConnection) -> None:
        self.connection = connection

    def __enter__(self) -> _Transaction:
        self.connection.events.append(("transaction_enter", self.connection.identity))
        return self

    def __exit__(self, exc_type: object, *_: object) -> None:
        action = "rollback" if exc_type else "commit"
        self.connection.events.append((action, self.connection.identity))


class _ControlledConnection(AbstractContextManager["_ControlledConnection"]):
    """Small DB-API fake that gives each acquired session its own trace."""

    def __init__(self, identity: int, level: str, events: list[tuple[str, Any]]) -> None:
        self.identity = identity
        self.level = level
        self.events = events
        self.statements: list[str] = []
        self.read_count = 0
        self.autocommit = False

    def __enter__(self) -> _ControlledConnection:
        self.events.append(("connection_enter", self.identity))
        return self

    def __exit__(self, *_: object) -> None:
        self.events.append(("connection_exit", self.identity))

    def transaction(self) -> _Transaction:
        return _Transaction(self)

    def cursor(self, *_: object, **__: object) -> _ControlledConnection:
        return self

    def execute(self, sql: str, params: object = None) -> _ControlledConnection:
        del params
        self.statements.append(sql)
        self.events.append(("execute", (self.identity, sql)))
        return self

    def fetchone(self) -> tuple[int]:
        self.read_count += 1
        if self.identity == 0 and self.read_count > 1 and self.level == "read_committed":
            return (271,)
        return (314,)

    def fetchall(self) -> list[tuple[int]]:
        return []


def _install_sessions(
    monkeypatch: pytest.MonkeyPatch, level: str
) -> tuple[list[_ControlledConnection], list[tuple[str, Any]]]:
    events: list[tuple[str, Any]] = []
    sessions: list[_ControlledConnection] = []

    def acquire() -> _ControlledConnection:
        session = _ControlledConnection(len(sessions), level, events)
        sessions.append(session)
        return session

    monkeypatch.setattr(dbms_showcase, "connection", acquire)
    return sessions, events


@pytest.mark.parametrize(
    ("level", "expected_second_read"),
    [("read_committed", 271), ("repeatable_read", 314), ("serializable", 314)],
)
def test_isolation_route_uses_two_transactions_and_requested_level(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    level: str,
    expected_second_read: int,
) -> None:
    sessions, events = _install_sessions(monkeypatch, level)

    response = client.get(f"/api/dbms/isolation-demo?level={level}")

    assert response.status_code == 200, response.text
    assert len(sessions) == 2
    assert sessions[0] is not sessions[1]
    all_sql = "\n".join(sql.lower() for session in sessions for sql in session.statements)
    assert f"isolation level {level.replace('_', ' ')}" in all_sql
    assert "statement_timeout" in all_sql or "lock_timeout" in all_sql
    assert {kind for kind, _ in events if kind == "connection_exit"} == {"connection_exit"}
    assert {identity for kind, identity in events if kind == "transaction_enter"} == {0, 1}
    assert {identity for kind, identity in events if kind in {"commit", "rollback"}} == {0, 1}

    payload = response.json()
    observed = payload["observed_reads"]
    assert len(observed) >= 2
    assert observed[0]["balance"] == 314
    assert observed[1]["balance"] == expected_second_read


def test_isolation_route_surfaces_database_failure(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail_connection() -> None:
        raise RuntimeError("synthetic isolation database failure")

    monkeypatch.setattr(dbms_showcase, "connection", fail_connection)

    response = client.get("/api/dbms/isolation-demo?level=read_committed")

    assert 500 <= response.status_code < 600, response.text
    assert "synthetic isolation database failure" not in response.text
    assert "observed_reads" not in response.text


def test_deadlock_route_reports_database_failure_instead_of_success(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail_connection() -> None:
        raise RuntimeError("synthetic deadlock database failure")

    monkeypatch.setattr(dbms_showcase, "connection", fail_connection)

    response = client.post("/api/dbms/deadlock-demo")

    assert 500 <= response.status_code < 600, response.text
    assert "synthetic deadlock database failure" not in response.text
    assert "40P01" not in response.text


def test_deadlock_route_does_not_claim_t2_without_postgres_deadlock(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    sessions, events = _install_sessions(monkeypatch, "read_committed")

    response = client.post("/api/dbms/deadlock-demo")

    assert 500 <= response.status_code < 600, response.text
    assert len(sessions) == 2 and sessions[0] is not sessions[1]
    all_sql = "\n".join(sql.lower() for session in sessions for sql in session.statements)
    assert "statement_timeout" in all_sql or "lock_timeout" in all_sql
    assert "40P01" not in response.text
    assert {identity for kind, identity in events if kind == "connection_exit"} == {0, 1}


@pytest.mark.parametrize("level", ["invalid", "dirty_read", "snapshot"])
def test_invalid_isolation_level_is_rejected_before_acquiring_database(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, level: str
) -> None:
    acquired = False

    def acquire() -> None:
        nonlocal acquired
        acquired = True
        raise AssertionError("invalid level must not open a connection")

    monkeypatch.setattr(dbms_showcase, "connection", acquire)

    response = client.get(f"/api/dbms/isolation-demo?level={level}")

    assert response.status_code in {400, 422}
    assert acquired is False
