from __future__ import annotations

import os
import sys
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from psycopg.errors import CheckViolation

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
_prior_app_env = os.environ.get("APP_ENV")
os.environ.setdefault("APP_ENV", "local")
try:
    import backend.app.main as main_module
    from backend.app.api.laps import current_user, get_race_db
    from backend.app.main import app
finally:
    if _prior_app_env is None:
        os.environ.pop("APP_ENV", None)
    else:
        os.environ["APP_ENV"] = _prior_app_env


class _Database:
    def __init__(self, tables: list[str] | None = None) -> None:
        self.tables = tables or ["drivers"]
        self.executed: list[tuple[str, Sequence[Any]]] = []

    def fetch_all(self, query: str, params: Sequence[Any] = ()) -> list[dict[str, Any]]:
        if "information_schema.tables" in query:
            return [{"table_name": name} for name in self.tables]
        if "information_schema.columns" in query and "key_column_usage" not in query:
            return [
                {"column_name": "id"},
                {"column_name": 'odd"column'},
                {"column_name": "password_hash"},
            ]
        if "pg_indexes" in query:
            return [
                {
                    "tablename": "drivers",
                    "indexname": "drivers_pkey",
                    "indexdef": (
                        "CREATE UNIQUE INDEX drivers_pkey ON public.drivers USING btree (id)"
                    ),
                }
            ]
        if "c.table_name" in query and "primary_key" in query:
            return [
                {
                    "table_name": "drivers",
                    "column_name": "id",
                    "data_type": "uuid",
                    "primary_key": True,
                },
                {
                    "table_name": "drivers",
                    "column_name": "number",
                    "data_type": "integer",
                    "primary_key": False,
                },
            ]
        if "child.relname AS child" in query:
            return [
                {
                    "child": "session_results",
                    "foreign_key": "driver_id",
                    "parent": "drivers",
                    "parent_key": "id",
                    "optional": False,
                    "children_per_parent": "0..many",
                }
            ]
        if "table_constraints" in query:
            return [{"column_name": "id"}]
        return []


class _Cursor:
    def __init__(self, *, fail_constraint: str | None = None) -> None:
        self.fail_constraint = fail_constraint
        self.sql: list[str] = []
        self.params: list[Sequence[Any]] = []
        self.result: Any = None
        self.counts = iter([(1,), (2,), (1,)])

    def __enter__(self) -> _Cursor:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def execute(self, query: Any, params: Sequence[Any] = ()) -> None:
        rendered = query.as_string(None) if hasattr(query, "as_string") else str(query)
        self.sql.append(rendered)
        self.params.append(params)
        if "INSERT INTO drivers" in rendered and self.fail_constraint:
            raise _ConstraintViolation(self.fail_constraint)
        if "SELECT txid_current()" in rendered:
            self.result = (8675309,)
        elif "SELECT count(*)" in rendered and "transaction_demo_probe" in rendered:
            self.result = next(self.counts)
        elif "SELECT count(*) AS count" in rendered:
            self.result = {"count": 17}
        elif rendered.startswith("SELECT "):
            self.result = None
        else:
            self.result = None

    def fetchone(self) -> Any:
        return self.result

    def fetchall(self) -> list[dict[str, Any]]:
        return [
            {"id": "driver-2", 'odd"column': "value-2"},
            {"id": "driver-3", 'odd"column': "value-3"},
        ]


class _Connection:
    def __init__(self, cursor: _Cursor) -> None:
        self._cursor = cursor

    def __enter__(self) -> _Connection:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def cursor(self, **_kwargs: Any) -> _Cursor:
        return self._cursor


class _ConstraintViolation(CheckViolation):
    def __init__(self, constraint_name: str) -> None:
        super().__init__("synthetic constraint violation")
        self._constraint_name = constraint_name

    @property
    def diag(self) -> Any:
        return type("Diag", (), {"constraint_name": self._constraint_name})()


@pytest.fixture
def setup_sql(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[TestClient, _Database, _Cursor]]:
    database = _Database()
    cursor = _Cursor()
    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[current_user] = lambda: {
        "id": "synthetic-admin",
        "email": "admin@example.invalid",
        "role": "ADMIN",
    }
    app.dependency_overrides[get_race_db] = lambda: database
    monkeypatch.setattr(main_module, "connection", lambda: _Connection(cursor), raising=False)
    try:
        yield TestClient(app), database, cursor
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)


def test_table_rows_allowlist_quotes_identifiers_and_applies_paging(
    setup_sql: tuple[TestClient, _Database, _Cursor],
) -> None:
    client, database, cursor = setup_sql
    database.tables = ['odd"table']

    response = client.get('/api/dbms/tables/odd%22table?limit=2&offset=4')

    assert response.status_code == 200
    body = response.json()
    assert body["table_name"] == 'odd"table'
    assert body["columns"] == ["id", 'odd"column']
    assert body["rows"] == [
        {"id": "driver-2", 'odd"column': "value-2"},
        {"id": "driver-3", 'odd"column': "value-3"},
    ]
    assert body["total"] == 17
    assert (body["limit"], body["offset"]) == (2, 4)
    select = next(query for query in cursor.sql if query.startswith("SELECT "))
    assert '"odd""column"' in select
    assert 'public."odd""table"' in select
    assert 'ORDER BY "id" LIMIT %s OFFSET %s' in select
    assert cursor.params[cursor.sql.index(select)] == (2, 4)


def test_table_rows_reject_non_public_table_and_invalid_paging(
    setup_sql: tuple[TestClient, _Database, _Cursor],
) -> None:
    client, _database, cursor = setup_sql

    missing = client.get("/api/dbms/tables/users")
    invalid = client.get("/api/dbms/tables/drivers?limit=0")

    assert missing.status_code == 404
    assert missing.json() == {"detail": "Database table not found"}
    assert invalid.status_code == 422
    assert cursor.sql == []


def test_schema_and_index_reports_return_catalog_rows(
    setup_sql: tuple[TestClient, _Database, _Cursor],
) -> None:
    client, _database, _cursor = setup_sql

    schema = client.get("/api/dbms/schema")
    indexes = client.get("/api/dbms/indexes")

    assert schema.status_code == 200
    assert schema.json() == [
        {"column_name": "id"},
        {"column_name": 'odd"column'},
        {"column_name": "password_hash"},
    ]
    assert indexes.status_code == 200
    assert indexes.json()[0]["indexname"] == "drivers_pkey"
    assert "CREATE UNIQUE INDEX" in indexes.json()[0]["indexdef"]


def test_eer_report_includes_primary_key_and_foreign_key_cardinality(
    setup_sql: tuple[TestClient, _Database, _Cursor],
) -> None:
    client, _database, _cursor = setup_sql

    response = client.get("/api/dbms/eer")

    assert response.status_code == 200
    assert response.json() == {
        "columns": [
            {
                "table_name": "drivers",
                "column_name": "id",
                "data_type": "uuid",
                "primary_key": True,
            },
            {
                "table_name": "drivers",
                "column_name": "number",
                "data_type": "integer",
                "primary_key": False,
            },
        ],
        "relationships": [
            {
                "child": "session_results",
                "foreign_key": "driver_id",
                "parent": "drivers",
                "parent_key": "id",
                "optional": False,
                "children_per_parent": "0..many",
            }
        ],
    }


def test_transaction_demo_reports_savepoint_rollback_counts(
    setup_sql: tuple[TestClient, _Database, _Cursor],
) -> None:
    client, _database, cursor = setup_sql

    response = client.post("/api/dbms/transaction-demo")

    assert response.status_code == 200
    assert response.json() == {
        "transaction_id": 8675309,
        "before": 1,
        "during": 2,
        "after_rollback": 1,
        "savepoint_rolled_back": True,
        "committed_effects": 0,
    }
    assert "SAVEPOINT tx_demo" in cursor.sql
    assert "ROLLBACK TO SAVEPOINT tx_demo" in cursor.sql


def test_constraint_demo_reports_expected_constraint_and_rolls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cursor = _Cursor(fail_constraint="drivers_number_check")
    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[current_user] = lambda: {"role": "ADMIN"}
    app.dependency_overrides[get_race_db] = lambda: _Database()
    monkeypatch.setattr(main_module, "connection", lambda: _Connection(cursor), raising=False)
    try:
        response = TestClient(app).post("/api/dbms/constraint-demo")
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)

    assert response.status_code == 200
    assert response.json() == {
        "constraint": "drivers_number_check",
        "rejected": True,
        "sqlstate": "23514",
    }
    assert cursor.sql[0] == "SAVEPOINT constraint_demo"
    assert "ROLLBACK TO SAVEPOINT constraint_demo" in cursor.sql
    assert cursor.sql[-1] == "RELEASE SAVEPOINT constraint_demo"
