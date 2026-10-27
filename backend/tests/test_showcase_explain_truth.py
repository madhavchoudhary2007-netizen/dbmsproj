from __future__ import annotations

import os
import sys
from collections.abc import Iterator
from pathlib import Path
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
    previous = app.dependency_overrides.get(current_user)
    app.dependency_overrides[current_user] = lambda: {
        "id": "synthetic-explain-admin",
        "email": "explain-admin@example.invalid",
        "role": "ADMIN",
    }
    try:
        yield TestClient(app)
    finally:
        if previous is None:
            app.dependency_overrides.pop(current_user, None)
        else:
            app.dependency_overrides[current_user] = previous


class _Cursor:
    def __init__(self, row: tuple[Any, ...] | None = None, error: Exception | None = None):
        self.row = row
        self.error = error
        self.executions: list[tuple[str, object]] = []

    def __enter__(self) -> _Cursor:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def execute(self, sql: str, params: object = None) -> None:
        self.executions.append((sql, params))
        if self.error:
            raise self.error

    def fetchone(self) -> tuple[Any, ...] | None:
        return self.row


class _Connection:
    def __init__(self, cursor: _Cursor):
        self._cursor = cursor

    def __enter__(self) -> _Connection:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def transaction(self) -> _Connection:
        return self

    def cursor(self, *args: object, **kwargs: object) -> _Cursor:
        return self._cursor


def _install_cursor(monkeypatch: pytest.MonkeyPatch, cursor: _Cursor) -> None:
    monkeypatch.setattr(dbms_showcase, "connection", lambda: _Connection(cursor))


@pytest.mark.parametrize("query_name", [None, "driver_history"])
def test_explain_database_error_returns_generic_server_error(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, query_name: str | None
) -> None:
    _install_cursor(monkeypatch, _Cursor(error=RuntimeError("synthetic private database detail")))
    params = "" if query_name is None else f"?query_name={query_name}"

    response = client.get(f"/api/dbms/explain{params}")

    assert response.status_code >= 500
    assert "synthetic private database detail" not in response.text
    assert "Aggregate" not in response.text


@pytest.mark.parametrize("query_name", [None, "driver_history"])
def test_explain_empty_result_returns_generic_server_error(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, query_name: str | None
) -> None:
    _install_cursor(monkeypatch, _Cursor(row=None))
    params = "" if query_name is None else f"?query_name={query_name}"

    response = client.get(f"/api/dbms/explain{params}")

    assert response.status_code >= 500
    assert "Aggregate" not in response.text
    assert "plan" not in response.json()


@pytest.mark.parametrize(
    ("query_name", "analyze", "expected_params"),
    [
        ("standings_rollup", False, ()),
        ("driver_history", True, ()),
        (
            "lap_telemetry_window",
            False,
            ("[]", "00000000-0000-0000-0000-000000000000"),
        ),
    ],
)
def test_explain_returns_database_plan_and_binds_inputs(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    query_name: str,
    analyze: bool,
    expected_params: tuple[str, ...],
) -> None:
    supplied_plan = [{"Plan": {"Node Type": "Index Scan", "Total Cost": 3.25}}]
    cursor = _Cursor(row=(supplied_plan,))
    _install_cursor(monkeypatch, cursor)

    response = client.get(
        f"/api/dbms/explain?query_name={query_name}&analyze={str(analyze).lower()}"
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["query_name"] == query_name
    assert body["plan"] == supplied_plan
    assert body["analyze"] is analyze
    assert len(cursor.executions) == 1
    sql, bound_params = cursor.executions[0]
    assert sql.startswith(
        f"EXPLAIN (ANALYZE {'TRUE' if analyze else 'FALSE'}, BUFFERS TRUE, FORMAT JSON)"
    )
    assert bound_params == expected_params


@pytest.mark.parametrize("query_name", ["random_query", "drop table users"])
def test_explain_rejects_disallowed_named_query_without_database_call(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, query_name: str
) -> None:
    calls: list[bool] = []
    monkeypatch.setattr(dbms_showcase, "connection", lambda: calls.append(True))

    response = client.get(f"/api/dbms/explain?query_name={query_name.replace(' ', '%20')}")

    assert response.status_code in (400, 422)
    assert calls == []
