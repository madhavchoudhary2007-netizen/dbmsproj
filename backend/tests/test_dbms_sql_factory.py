from __future__ import annotations

import os
import sys
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest
from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient
from psycopg.errors import CheckViolation

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ.setdefault("APP_ENV", "local")

from backend.app.api.dbms_sql import create_dbms_sql_router

TABLE_NAME = 'factory"table'


class _ConstraintViolation(CheckViolation):
    @property
    def diag(self) -> Any:
        return type("Diag", (), {"constraint_name": "drivers_number_check"})()


class _Cursor:
    def __init__(self) -> None:
        self.queries: list[tuple[str, Sequence[Any]]] = []
        self.result: Any = None
        self.counts = iter([(1,), (2,), (1,)])

    def __enter__(self) -> _Cursor:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def execute(self, query: Any, params: Sequence[Any] = ()) -> None:
        rendered = query.as_string(None) if hasattr(query, "as_string") else str(query)
        self.queries.append((rendered, params))
        if rendered.startswith("INSERT INTO drivers"):
            raise _ConstraintViolation("synthetic constraint failure")
        if "SELECT txid_current()" in rendered:
            self.result = (424242,)
        elif "SELECT count(*)" in rendered and "transaction_demo_probe" in rendered:
            self.result = next(self.counts)
        elif "SELECT count(*) AS count" in rendered:
            self.result = {"count": 8}
        else:
            self.result = None

    def fetchone(self) -> Any:
        return self.result

    def fetchall(self) -> list[dict[str, Any]]:
        return [
            {"id": "row-2", 'odd"column': "two"},
            {"id": "row-3", 'odd"column': "three"},
        ]


class _Connection:
    def __init__(self, cursor: _Cursor) -> None:
        self.cursor_instance = cursor

    def __enter__(self) -> _Connection:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def cursor(self, **_kwargs: Any) -> _Cursor:
        return self.cursor_instance


class _Services:
    def __init__(self) -> None:
        self.cursor = _Cursor()
        self.fetches: list[str] = []

    def fetch_all(self, query: str, _params: Sequence[Any] = ()) -> list[dict[str, Any]]:
        self.fetches.append(query)
        if "information_schema.tables" in query:
            return [{"table_name": TABLE_NAME}]
        if "information_schema.columns" in query and "table_constraints" not in query:
            return [
                {"column_name": "id"},
                {"column_name": 'odd"column'},
                {"column_name": "password_hash"},
            ]
        if "table_constraints" in query:
            return [{"column_name": "id"}]
        return []

    @contextmanager
    def connection(self) -> Iterator[_Connection]:
        yield _Connection(self.cursor)


@pytest.fixture
def factory_client() -> Iterator[tuple[TestClient, _Services, dict[str, str]]]:
    services = _Services()
    caller = {"role": "ADMIN"}

    def admin_user() -> dict[str, str]:
        if caller["role"] != "ADMIN":
            raise HTTPException(403, "Admin role required")
        return caller

    router, handlers = create_dbms_sql_router(
        services.fetch_all,
        lambda value: value,
        Depends(admin_user),
        services.connection,
    )
    api = FastAPI()
    api.include_router(router)
    assert "dbms_table_rows" in handlers
    try:
        yield TestClient(api), services, caller
    finally:
        services.cursor.queries.clear()


def test_factory_table_route_allowlists_and_quotes_identifiers_with_paging(
    factory_client: tuple[TestClient, _Services, dict[str, str]],
) -> None:
    client, services, _caller = factory_client

    response = client.get(f"/api/dbms/tables/{TABLE_NAME.replace(chr(34), '%22')}?limit=2&offset=3")

    assert response.status_code == 200
    body = response.json()
    assert body["table_name"] == TABLE_NAME
    assert body["columns"] == ["id", 'odd"column']
    assert body["rows"] == [
        {"id": "row-2", 'odd"column': "two"},
        {"id": "row-3", 'odd"column': "three"},
    ]
    assert (body["total"], body["limit"], body["offset"]) == (8, 2, 3)
    select, params = next(
        (query, params)
        for query, params in services.cursor.queries
        if query.startswith("SELECT ") and "LIMIT %s OFFSET %s" in query
    )
    assert 'public."factory""table"' in select
    assert '"odd""column"' in select
    assert 'ORDER BY "id" LIMIT %s OFFSET %s' in select
    assert params == (2, 3)


def test_factory_table_route_rejects_unlisted_names_and_invalid_pages(
    factory_client: tuple[TestClient, _Services, dict[str, str]],
) -> None:
    client, services, _caller = factory_client

    missing = client.get("/api/dbms/tables/users")
    invalid = client.get(f"/api/dbms/tables/{TABLE_NAME.replace(chr(34), '%22')}?offset=-1")

    assert missing.status_code == 404
    assert missing.json() == {"detail": "Database table not found"}
    assert invalid.status_code == 422
    assert not services.cursor.queries


def test_factory_transaction_and_constraint_routes_preserve_savepoint_semantics(
    factory_client: tuple[TestClient, _Services, dict[str, str]],
) -> None:
    client, services, _caller = factory_client

    transaction = client.post("/api/dbms/transaction-demo")
    constraint = client.post("/api/dbms/constraint-demo")

    assert transaction.status_code == 200
    assert transaction.json() == {
        "transaction_id": 424242,
        "before": 1,
        "during": 2,
        "after_rollback": 1,
        "savepoint_rolled_back": True,
        "committed_effects": 0,
    }
    assert constraint.status_code == 200
    assert constraint.json() == {
        "constraint": "drivers_number_check",
        "rejected": True,
        "sqlstate": "23514",
    }
    queries = [query for query, _ in services.cursor.queries]
    assert queries.index("SAVEPOINT tx_demo") < queries.index("ROLLBACK TO SAVEPOINT tx_demo")
    assert queries.index("SAVEPOINT constraint_demo") < queries.index(
        "ROLLBACK TO SAVEPOINT constraint_demo"
    ) < queries.index("RELEASE SAVEPOINT constraint_demo")


def test_factory_routes_enforce_injected_admin_dependency(
    factory_client: tuple[TestClient, _Services, dict[str, str]],
) -> None:
    client, services, caller = factory_client
    caller["role"] = "DRIVER"

    response = client.get("/api/dbms/tables")
    transaction = client.post("/api/dbms/transaction-demo")

    assert response.status_code == transaction.status_code == 403
    assert response.json() == {"detail": "Admin role required"}
    assert transaction.json() == {"detail": "Admin role required"}
    assert services.fetches == []
    assert services.cursor.queries == []
