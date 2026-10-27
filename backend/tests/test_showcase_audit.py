from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

_prior_app_env = os.environ.get("APP_ENV")
os.environ.setdefault("APP_ENV", "local")
try:
    from backend.app.api import dbms_showcase, stewards
    from backend.app.schemas_operations import Decision
finally:
    if _prior_app_env is None:
        os.environ.pop("APP_ENV", None)
    else:
        os.environ["APP_ENV"] = _prior_app_env


class _Cursor:
    def __init__(self, rows_by_query: dict[str, list[dict[str, Any]]] | None = None):
        self.rows_by_query = rows_by_query or {}
        self.executed: list[tuple[str, Any]] = []
        self.rows: list[dict[str, Any]] = []

    def __enter__(self) -> _Cursor:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def execute(self, sql: str, params: Any = None) -> None:
        self.executed.append((sql, params))
        self.rows = next(
            (rows for marker, rows in self.rows_by_query.items() if marker in sql), []
        )

    def fetchall(self) -> list[dict[str, Any]]:
        return self.rows

    def fetchone(self) -> dict[str, Any] | None:
        return self.rows.pop(0) if self.rows else None


class _Connection:
    def __init__(self, cursor: _Cursor):
        self._cursor = cursor

    def __enter__(self) -> _Connection:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def cursor(self, *_: object, **__: object) -> _Cursor:
        return self._cursor


def test_security_metadata_is_built_from_database_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    cursor = _Cursor(
        {
            "FROM pg_roles": [{"rolname": "apexgrid_readonly"}],
            "FROM information_schema.role_table_grants": [
                {
                    "grantee": "apexgrid_readonly",
                    "table_name": "audit_log",
                    "privilege_type": "SELECT",
                }
            ],
            "FROM pg_policies": [
                {
                    "policyname": "observed_policy",
                    "tablename": "audit_log",
                    "roles": ["stewards"],
                    "cmd": "SELECT",
                }
            ],
        }
    )
    monkeypatch.setattr(dbms_showcase, "connection", lambda: _Connection(cursor))

    result = dbms_showcase.get_security()

    assert result.roles == ["apexgrid_readonly"]
    assert [grant.model_dump() for grant in result.grants] == [
        {
            "grantee": "apexgrid_readonly",
            "table_name": "audit_log",
            "privilege_type": "SELECT",
        }
    ]
    assert [policy.model_dump() for policy in result.policies] == [
        {
            "policyname": "observed_policy",
            "tablename": "audit_log",
            "roles": ["stewards"],
            "cmd": "SELECT",
        }
    ]


def test_security_metadata_empty_rows_stay_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    cursor = _Cursor()
    monkeypatch.setattr(dbms_showcase, "connection", lambda: _Connection(cursor))

    result = dbms_showcase.get_security()

    assert result.roles == []
    assert result.grants == []
    assert result.policies == []


def test_security_metadata_database_error_is_generic(monkeypatch: pytest.MonkeyPatch) -> None:
    class BrokenCursor(_Cursor):
        def execute(self, sql: str, params: Any = None) -> None:
            raise RuntimeError("synthetic-secret-db-detail")

    monkeypatch.setattr(dbms_showcase, "connection", lambda: _Connection(BrokenCursor()))

    with pytest.raises(HTTPException) as caught:
        dbms_showcase.get_security()

    assert caught.value.status_code == 500
    assert "synthetic-secret-db-detail" not in str(caught.value.detail)


def test_steward_penalty_write_sets_authenticated_actor_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    incident_id = UUID("00000000-0000-0000-0000-000000000111")
    session_id = UUID("00000000-0000-0000-0000-000000000222")
    driver_id = UUID("00000000-0000-0000-0000-000000000333")
    cursor = _Cursor(
        {
            "SELECT * FROM incident_reports": [
                {"state": "OPEN", "session_id": session_id, "driver_id": driver_id}
            ],
            "UPDATE incident_reports": [{"id": incident_id, "state": "APPROVED"}],
            "INSERT INTO penalties": [{"id": "synthetic-penalty", "points": 2}],
            "SELECT d.eligibility": [{"eligibility": "ELIGIBLE", "season_points": 0}],
        }
    )
    monkeypatch.setattr(stewards, "_get_connection", lambda _database=None: _Connection(cursor))
    monkeypatch.setattr(stewards, "_resolve_publish", lambda _bus=None: lambda *_: None)
    actor = "known-steward-actor"

    stewards.decide_incident(
        incident_id,
        Decision.model_validate(
            {"approve": True, "points": 2, "actor": "forged-client-actor"}
        ),
        user={"id": actor, "role": "STEWARD"},
        database=None,
        bus=None,
    )

    context_calls = [
        (sql, params)
        for sql, params in cursor.executed
        if "set_config('apexgrid.actor'" in sql or 'set_config("apexgrid.actor"' in sql
    ]
    assert len(context_calls) == 1
    sql, params = context_calls[0]
    assert "set_config" in sql and "apexgrid.actor" in sql
    assert params is not None and actor in params
    assert "forged-client-actor" not in repr(params)
    assert not any(actor in sql or "forged-client-actor" in sql for sql, _ in cursor.executed)


@pytest.mark.parametrize(
    ("principal", "expected_role"),
    [
        ({"id": "steward-actor", "role": "STEWARD"}, "steward"),
        ({"id": "admin-actor", "role": "ADMIN"}, "admin"),
        ({"id": "unknown-actor", "role": "ROOT"}, None),
        (None, None),
    ],
)
def test_penalty_write_binds_only_authenticated_role_in_transaction(
    monkeypatch: pytest.MonkeyPatch,
    principal: dict[str, str] | None,
    expected_role: str | None,
) -> None:
    incident_id = UUID("00000000-0000-0000-0000-000000000111")
    session_id = UUID("00000000-0000-0000-0000-000000000222")
    driver_id = UUID("00000000-0000-0000-0000-000000000333")
    cursor = _Cursor(
        {
            "SELECT * FROM incident_reports": [
                {"state": "OPEN", "session_id": session_id, "driver_id": driver_id}
            ],
            "UPDATE incident_reports": [{"id": incident_id, "state": "APPROVED"}],
            "INSERT INTO penalties": [{"id": "synthetic-penalty", "points": 2}],
            "SELECT d.eligibility": [{"eligibility": "ELIGIBLE", "season_points": 0}],
        }
    )
    monkeypatch.setattr(stewards, "_get_connection", lambda _database=None: _Connection(cursor))
    monkeypatch.setattr(stewards, "_resolve_publish", lambda _bus=None: lambda *_: None)

    stewards.decide_incident(
        incident_id,
        Decision.model_validate(
            {"approve": True, "points": 2, "role": "DIRECTOR", "actor": "forged-client"}
        ),
        user=principal,
        database=None,
        bus=None,
    )

    role_calls = [
        (index, sql, params)
        for index, (sql, params) in enumerate(cursor.executed)
        if "set_config('apexgrid.role'" in sql or 'set_config("apexgrid.role"' in sql
    ]
    penalty_index = next(
        index for index, (sql, _) in enumerate(cursor.executed) if "INSERT INTO penalties" in sql
    )
    if expected_role is None:
        assert role_calls == []
        return

    assert len(role_calls) == 1
    role_index, sql, params = role_calls[0]
    assert role_index < penalty_index
    assert "set_config('apexgrid.role', %s, true)" in sql
    assert params == (expected_role,)
