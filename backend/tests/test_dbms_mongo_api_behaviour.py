from __future__ import annotations

import os
import sys
from collections.abc import Callable, Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pymongo.errors import PyMongoError

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
_prior_app_env = os.environ.get("APP_ENV")
os.environ.setdefault("APP_ENV", "local")
try:
    from backend.app import main as main_module
    from backend.app.api.dbms_mongo import (
        _estimated_telemetry_count,
        _resolve_db,
        _resolve_mongo_db,
        _resolve_telemetry,
        get_mongo_db,
    )
    from backend.app.api.laps import current_user, get_race_db
    from backend.app.config import MONGODB_DATABASE
    from backend.app.core.runtime import RuntimeState, get_mongo, get_telemetry
    from backend.app.main import app
    from backend.app.api.dbms_mongo import create_dbms_mongo_router
    from backend.app.api.laps import admin_role_dependency
    from backend.app.core.serialization import jsonable
    from fastapi import FastAPI
finally:
    if _prior_app_env is None:
        os.environ.pop("APP_ENV", None)
    else:
        os.environ["APP_ENV"] = _prior_app_env


BASE_TS = datetime(2026, 10, 26, 12, tzinfo=UTC)
PRIVILEGED_PATHS = [
    "/api/dbms/overview",
    "/api/dbms/telemetry",
    "/api/dbms/mongo/collections",
    "/api/dbms/mongo/collections/telemetry",
    "/api/dbms/polyglot",
]


class _Cursor:
    def __init__(self, documents: list[dict[str, Any]]) -> None:
        self.documents = list(documents)

    def sort(self, key: str, direction: int) -> _Cursor:
        self.documents.sort(key=lambda doc: doc[key], reverse=direction == -1)
        return self

    def skip(self, offset: int) -> _Cursor:
        self.documents = self.documents[offset:]
        return self

    def limit(self, limit: int) -> _Cursor:
        self.documents = self.documents[:limit]
        return self

    def __iter__(self) -> Any:
        return iter(self.documents)


class _Collection:
    """In-memory stand-in for a pymongo collection that records every call it receives."""

    def __init__(
        self,
        documents: list[dict[str, Any]] | None = None,
        indexes: dict[str, Any] | None = None,
        *,
        error: Exception | None = None,
        aggregate_rows: list[dict[str, Any]] | None = None,
    ) -> None:
        self.documents = list(documents or [])
        self.indexes = indexes if indexes is not None else {"_id_": {"key": [("_id", 1)]}}
        self.error = error
        self.aggregate_rows = list(aggregate_rows or [])
        self.calls: list[str] = []
        self.pipelines: list[list[dict[str, Any]]] = []

    def _call(self, name: str) -> None:
        self.calls.append(name)
        if self.error is not None:
            raise self.error

    def _matching(self, filters: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            dict(document)
            for document in self.documents
            if all(document.get(key) == value for key, value in filters.items())
        ]

    def index_information(self) -> dict[str, Any]:
        self._call("index_information")
        return self.indexes

    def count_documents(self, filters: dict[str, Any]) -> int:
        self._call("count_documents")
        return len(self._matching(filters))

    def estimated_document_count(self) -> int:
        self._call("estimated_document_count")
        return len(self.documents)

    def find(self, filters: dict[str, Any] | None = None, projection: Any = None) -> _Cursor:
        self._call("find")
        rows = self._matching(filters or {})
        if projection and projection.get("_id") == 0:
            for row in rows:
                row.pop("_id", None)
        return _Cursor(rows)

    def aggregate(self, pipeline: list[dict[str, Any]]) -> list[dict[str, Any]]:
        self._call("aggregate")
        self.pipelines.append(pipeline)
        return [dict(row) for row in self.aggregate_rows]


class _MongoDatabase:
    def __init__(
        self,
        collections: dict[str, _Collection],
        *,
        list_error: Exception | None = None,
    ) -> None:
        self.collections = collections
        self.list_error = list_error
        self.list_calls = 0

    def list_collection_names(self) -> list[str]:
        self.list_calls += 1
        if self.list_error is not None:
            raise self.list_error
        return list(self.collections)

    def __getitem__(self, name: str) -> _Collection:
        return self.collections[name]


class _SqlDatabase:
    def __init__(
        self,
        counts: dict[str, int] | None = None,
        rows: list[dict[str, Any]] | None = None,
    ) -> None:
        self.counts = counts or {}
        self.rows = rows or []
        self.queries: list[str] = []

    def fetch_one(self, sql: str, params: Any = ()) -> dict[str, Any]:
        self.queries.append(sql)
        return dict(self.counts)

    def fetch_all(self, sql: str, params: Any = ()) -> list[dict[str, Any]]:
        self.queries.append(sql)
        return [dict(row) for row in self.rows]


def _telemetry_documents() -> list[dict[str, Any]]:
    return [
        {
            "_id": f"doc-{index}",
            "session_id": "session-a" if index < 4 else "session-b",
            "driver_id": "driver-1" if index % 2 == 0 else "driver-2",
            "lap": index,
            "sector": 2,
            "ts": BASE_TS + timedelta(minutes=index),
            "speed_kph": 210 + index,
        }
        for index in range(1, 6)
    ]


def _user(role: str) -> dict[str, Any]:
    return {
        "id": f"synthetic-{role.lower()}",
        "email": f"{role.lower()}@example.invalid",
        "role": role,
    }


@pytest.fixture
def telemetry() -> _Collection:
    return _Collection(
        _telemetry_documents(),
        {"_id_": {"key": [("_id", 1)]}, "ts_1": {"key": [("ts", 1)]}},
    )


@pytest.fixture
def mongo(telemetry: _Collection) -> _MongoDatabase:
    return _MongoDatabase(
        {
            "telemetry": telemetry,
            "empty_events": _Collection([], {"_id_": {"key": [("_id", 1)]}}),
            "system.profile": _Collection([], {}),
        }
    )


@pytest.fixture
def sql() -> _SqlDatabase:
    return _SqlDatabase(
        counts={
            "active_sessions": 2,
            "completed_sessions": 5,
            "open_incidents": 1,
            "reserved_pit_stops": 3,
            "completed_pit_stops": 8,
            "official_results": 12,
        },
        rows=[
            {
                "session_id": "s1",
                "state": "COMPLETED",
                "driver_id": "d1",
                "full_name": "Ada Lovelace",
            },
            {
                "session_id": "s2",
                "state": "ACTIVE",
                "driver_id": "d2",
                "full_name": "Grace Hopper",
            },
        ],
    )


@pytest.fixture
def overrides() -> Iterator[dict[Any, Any]]:
    previous = app.dependency_overrides.copy()
    try:
        yield app.dependency_overrides
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)


@pytest.fixture
def wired(
    overrides: dict[Any, Any],
    mongo: _MongoDatabase,
    telemetry: _Collection,
    sql: _SqlDatabase,
) -> Callable[..., TestClient]:
    overrides[get_mongo_db] = lambda: mongo
    overrides[get_telemetry] = lambda: telemetry
    overrides[get_race_db] = lambda: sql

    def _client(role: str = "ADMIN") -> TestClient:
        overrides[current_user] = lambda: _user(role)
        return TestClient(app)

    return _client


def _request_for(
    dependency_overrides: dict[Any, Any] | None = None,
    runtime: Any = None,
) -> Any:
    return SimpleNamespace(
        app=SimpleNamespace(
            dependency_overrides=dependency_overrides or {},
            state=SimpleNamespace(runtime=runtime),
        )
    )


# --- Authorization -----------------------------------------------------------


@pytest.mark.parametrize("path", PRIVILEGED_PATHS)
@pytest.mark.parametrize("role", ["STEWARD", "DRIVER"])
def test_non_admin_roles_are_forbidden_and_stores_are_never_read(
    wired: Callable[..., TestClient],
    path: str,
    role: str,
    mongo: _MongoDatabase,
    telemetry: _Collection,
    sql: _SqlDatabase,
) -> None:
    response = wired(role).get(path)

    assert response.status_code == 403
    assert mongo.list_calls == 0
    assert telemetry.calls == []
    assert sql.queries == []


@pytest.mark.parametrize("path", PRIVILEGED_PATHS)
def test_missing_credentials_are_unauthorized_and_stores_are_never_read(
    overrides: dict[Any, Any],
    wired: Callable[..., TestClient],
    mongo: _MongoDatabase,
    telemetry: _Collection,
    sql: _SqlDatabase,
    path: str,
) -> None:
    wired()
    overrides.pop(current_user, None)

    response = TestClient(app).get(path)

    assert response.status_code == 401
    assert mongo.list_calls == 0
    assert telemetry.calls == []
    assert sql.queries == []


# --- Collection listing ------------------------------------------------------


def test_collection_listing_reports_configured_database_for_an_empty_store(
    wired: Callable[..., TestClient],
) -> None:
    overrides_db = _MongoDatabase({})
    client = wired()
    app.dependency_overrides[get_mongo_db] = lambda: overrides_db

    body = client.get("/api/dbms/mongo/collections").json()

    assert body["store"] == "MongoDB"
    assert body["database"] == MONGODB_DATABASE
    assert body["collections"] == []
    assert body["updated_at"]


def test_collection_listing_returns_503_when_an_index_read_fails(
    wired: Callable[..., TestClient],
) -> None:
    broken = _MongoDatabase({"broken": _Collection(error=RuntimeError("index scan failed"))})
    client = wired()
    app.dependency_overrides[get_mongo_db] = lambda: broken

    response = client.get("/api/dbms/mongo/collections")

    assert response.status_code == 503
    assert response.json()["detail"] == "Could not inspect MongoDB collections"


def test_collection_listing_returns_503_when_database_enumeration_fails(
    wired: Callable[..., TestClient],
) -> None:
    unreachable = _MongoDatabase({}, list_error=PyMongoError("server selection timed out"))
    client = wired()
    app.dependency_overrides[get_mongo_db] = lambda: unreachable

    response = client.get("/api/dbms/mongo/collections")

    assert response.status_code == 503
    assert response.json()["detail"] == "Could not inspect MongoDB collections"


# --- Document browse ---------------------------------------------------------


def test_document_browse_filters_by_driver_and_orders_newest_first(
    wired: Callable[..., TestClient],
) -> None:
    response = wired().get(
        "/api/dbms/mongo/collections/telemetry",
        params={"driver_id": "driver-2", "limit": 2, "offset": 1},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["collection"] == "telemetry"
    assert body["filters"] == {"driver_id": "driver-2"}
    assert body["total"] == 3
    assert (body["limit"], body["offset"]) == (2, 1)
    assert [item["lap"] for item in body["documents"]] == [3, 1]
    assert [item["id"] for item in body["documents"]] == ["doc-3", "doc-1"]


def test_document_browse_combines_lap_and_session_filters(
    wired: Callable[..., TestClient],
) -> None:
    response = wired().get(
        "/api/dbms/mongo/collections/telemetry",
        params={"session_id": "session-b", "lap": 5},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["filters"] == {"session_id": "session-b", "lap": 5}
    assert body["total"] == 1
    assert [item["id"] for item in body["documents"]] == ["doc-5"]


def test_document_browse_uses_default_pagination_when_no_filters_are_given(
    wired: Callable[..., TestClient],
) -> None:
    body = wired().get("/api/dbms/mongo/collections/empty_events").json()

    assert body["filters"] == {}
    assert body["documents"] == []
    assert body["total"] == 0
    assert (body["limit"], body["offset"]) == (50, 0)


@pytest.mark.parametrize("name", ["system.profile", "no_such_collection"])
def test_document_browse_hides_system_and_unknown_collections_with_404(
    wired: Callable[..., TestClient],
    telemetry: _Collection,
    name: str,
) -> None:
    response = wired().get(f"/api/dbms/mongo/collections/{name}")

    assert response.status_code == 404
    assert response.json()["detail"] == "MongoDB collection not found"
    assert "count_documents" not in telemetry.calls


@pytest.mark.parametrize(
    "params",
    [
        {"limit": 0},
        {"limit": 101},
        {"offset": -1},
        {"lap": 0},
        {"sector": 0},
        {"sector": 4},
        {"session_id": "x" * 65},
        {"driver_id": "x" * 65},
    ],
)
def test_document_browse_rejects_out_of_range_parameters_before_reading(
    wired: Callable[..., TestClient],
    telemetry: _Collection,
    params: dict[str, Any],
) -> None:
    response = wired().get("/api/dbms/mongo/collections/telemetry", params=params)

    assert response.status_code == 422
    assert telemetry.calls == []


def test_document_browse_returns_503_when_collection_read_fails(
    wired: Callable[..., TestClient],
) -> None:
    failing = _MongoDatabase(
        {"telemetry": _Collection(error=RuntimeError("cursor lost"))},
    )
    client = wired()
    app.dependency_overrides[get_mongo_db] = lambda: failing

    response = client.get("/api/dbms/mongo/collections/telemetry")

    assert response.status_code == 503
    assert response.json()["detail"] == "Could not read MongoDB collection"


def test_document_browse_returns_503_when_database_enumeration_fails(
    wired: Callable[..., TestClient],
) -> None:
    failing = _MongoDatabase({}, list_error=PyMongoError("connection reset"))
    client = wired()
    app.dependency_overrides[get_mongo_db] = lambda: failing

    response = client.get("/api/dbms/mongo/collections/telemetry")

    assert response.status_code == 503
    assert response.json()["detail"] == "Could not read MongoDB collection"


# --- Telemetry inspection ----------------------------------------------------


def test_telemetry_route_reports_count_indexes_and_three_newest_samples(
    wired: Callable[..., TestClient],
) -> None:
    response = wired().get("/api/dbms/telemetry")

    assert response.status_code == 200
    body = response.json()
    assert body["store"] == "MongoDB"
    assert body["count"] == 5
    assert body["indexes"] == ["_id_", "ts_1"]
    assert [item["lap"] for item in body["sample"]] == [5, 4, 3]
    assert all("_id" not in item for item in body["sample"])


def test_telemetry_route_returns_503_when_inspection_fails(
    overrides: dict[Any, Any],
    wired: Callable[..., TestClient],
) -> None:
    client = wired()
    broken = _Collection(error=RuntimeError("collection stats unavailable"))
    overrides[get_telemetry] = lambda: broken

    response = client.get("/api/dbms/telemetry")

    assert response.status_code == 503
    assert response.json()["detail"] == "Could not inspect MongoDB telemetry"


# --- Overview ----------------------------------------------------------------


def test_overview_reports_relational_counts_and_mongo_sample_total(
    wired: Callable[..., TestClient],
    sql: _SqlDatabase,
) -> None:
    response = wired().get("/api/dbms/overview")

    assert response.status_code == 200
    body = response.json()
    assert body["active_sessions"] == 2
    assert body["completed_sessions"] == 5
    assert body["open_incidents"] == 1
    assert body["reserved_pit_stops"] == 3
    assert body["completed_pit_stops"] == 8
    assert body["official_results"] == 12
    assert body["telemetry_samples"] == 5
    assert body["postgres"] == "up"
    assert body["mongodb"] == "up"
    assert body["updated_at"]
    assert any("pit_reservations" in query for query in sql.queries)


def test_overview_degrades_to_mongo_down_without_failing_the_request(
    overrides: dict[Any, Any],
    wired: Callable[..., TestClient],
) -> None:
    client = wired()
    offline = _Collection(error=PyMongoError("server selection timed out"))
    overrides[get_telemetry] = lambda: offline

    response = client.get("/api/dbms/overview")

    assert response.status_code == 200
    body = response.json()
    assert body["mongodb"] == "down"
    assert body["telemetry_samples"] is None
    assert body["postgres"] == "up"
    assert body["active_sessions"] == 2


# --- Polyglot ----------------------------------------------------------------


def test_polyglot_merges_telemetry_totals_into_relational_rows(
    wired: Callable[..., TestClient],
    telemetry: _Collection,
) -> None:
    latest = datetime(2026, 10, 26, 12, 4, tzinfo=UTC)
    telemetry.aggregate_rows = [
        {
            "_id": {"session_id": "s1", "driver_id": "d1"},
            "samples": 4,
            "latest": latest,
        }
    ]

    response = wired().get("/api/dbms/polyglot")

    assert response.status_code == 200
    body = response.json()
    assert body["relational_rows"] == 2
    assert [row["full_name"] for row in body["rows"]] == ["Ada Lovelace", "Grace Hopper"]
    assert body["rows"][0]["telemetry"]["samples"] == 4
    assert body["rows"][0]["telemetry"]["_id"] == {"session_id": "s1", "driver_id": "d1"}
    assert body["rows"][1]["telemetry"] == {"samples": 0}


def test_polyglot_aggregation_is_bounded_to_recent_samples(
    wired: Callable[..., TestClient],
    telemetry: _Collection,
) -> None:
    response = wired().get("/api/dbms/polyglot")

    assert response.status_code == 200
    assert len(telemetry.pipelines) == 1
    pipeline = telemetry.pipelines[0]
    assert "$gte" in pipeline[0]["$match"]["ts"]
    assert pipeline[1] == {"$sort": {"ts": -1}}
    assert pipeline[2] == {"$limit": 5000}


def test_polyglot_with_no_relational_entries_returns_empty_rows(
    wired: Callable[..., TestClient],
    overrides: dict[Any, Any],
) -> None:
    client = wired()
    overrides[get_race_db] = lambda: _SqlDatabase()

    body = client.get("/api/dbms/polyglot").json()

    assert body == {"relational_rows": 0, "rows": []}


# --- Dependency resolution helpers -------------------------------------------


def test_get_mongo_db_prefers_a_registered_dependency_override() -> None:
    expected = _MongoDatabase({})
    request = _request_for({get_mongo: lambda: expected})

    assert get_mongo_db(request) is expected


def test_get_mongo_db_uses_the_runtime_client_database_without_an_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(main_module, "_default_mongo_database_ready", None, raising=False)
    monkeypatch.setattr(main_module, "mongo_database_ready", None, raising=False)
    database = _MongoDatabase({})
    runtime = RuntimeState(mongo_client={MONGODB_DATABASE: database})  # type: ignore[arg-type]

    assert get_mongo_db(_request_for(runtime=runtime)) is database


def test_get_mongo_db_honours_a_replaced_main_factory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database = _MongoDatabase({})
    monkeypatch.setattr(main_module, "mongo_database_ready", lambda: database, raising=False)
    monkeypatch.setattr(
        main_module, "_default_mongo_database_ready", lambda: None, raising=False
    )

    assert get_mongo_db(_request_for()) is database


def test_get_mongo_db_raises_503_when_no_store_is_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(main_module, "_default_mongo_database_ready", None, raising=False)
    monkeypatch.setattr(main_module, "mongo_database_ready", None, raising=False)

    with pytest.raises(HTTPException) as excinfo:
        get_mongo_db(_request_for(runtime=RuntimeState()))

    assert excinfo.value.status_code == 503
    assert excinfo.value.detail == "MongoDB document store is unavailable"


def test_resolve_mongo_db_returns_the_explicit_database_when_given() -> None:
    database = _MongoDatabase({})

    assert _resolve_mongo_db(database) is database


def test_resolve_mongo_db_uses_the_main_factory_when_no_database_is_given(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database = _MongoDatabase({})
    monkeypatch.setattr(main_module, "mongo_database_ready", lambda: database, raising=False)

    assert _resolve_mongo_db() is database


def test_resolve_mongo_db_raises_503_without_any_factory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(main_module, "mongo_database_ready", None, raising=False)

    with pytest.raises(HTTPException) as excinfo:
        _resolve_mongo_db()

    assert excinfo.value.status_code == 503
    assert excinfo.value.detail == "MongoDB document store is unavailable"


def test_resolve_telemetry_prefers_an_explicit_collection() -> None:
    collection = _Collection()

    assert _resolve_telemetry(col=collection) is collection


def test_resolve_telemetry_uses_the_runtime_collection_when_the_dependency_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(main_module, "mongo_ready", None, raising=False)
    runtime_collection = _Collection()

    def _unavailable() -> _Collection:
        raise RuntimeError("dependency unavailable")

    request = _request_for(
        {get_telemetry: _unavailable},
        runtime=RuntimeState(telemetry_collection=runtime_collection),  # type: ignore[arg-type]
    )

    assert _resolve_telemetry(request=request) is runtime_collection


def test_resolve_telemetry_raises_503_without_any_store(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(main_module, "mongo_ready", None, raising=False)

    with pytest.raises(HTTPException) as excinfo:
        _resolve_telemetry()

    assert excinfo.value.status_code == 503
    assert excinfo.value.detail == "MongoDB telemetry store is unavailable"


def test_resolve_db_wraps_the_main_fetch_functions_when_no_session_is_given(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        main_module,
        "fetch_all",
        lambda sql, params=(): [{"probe": sql}],
        raising=False,
    )

    session = _resolve_db()

    assert session.fetch_all("SELECT 1") == [{"probe": "SELECT 1"}]


def test_resolve_db_returns_the_explicit_session_when_given() -> None:
    session = _SqlDatabase()

    assert _resolve_db(session) is session  # type: ignore[arg-type]


def test_estimated_count_prefers_the_server_estimate() -> None:
    collection = SimpleNamespace(
        estimated_document_count=lambda: 7,
        count_documents=lambda filters: 99,
    )

    assert _estimated_telemetry_count(collection) == 7


def test_estimated_count_falls_back_to_exact_count_when_estimate_fails() -> None:
    def _broken_estimate() -> int:
        raise PyMongoError("estimate unavailable")

    collection = SimpleNamespace(
        estimated_document_count=_broken_estimate,
        count_documents=lambda filters: 3,
    )

    assert _estimated_telemetry_count(collection) == 3


def test_estimated_count_uses_exact_count_when_no_estimate_exists() -> None:
    collection = SimpleNamespace(count_documents=lambda filters: 4)

    assert _estimated_telemetry_count(collection) == 4


# --- Router factory (create_dbms_mongo_router) handlers -----------------------


def _factory(
    mongo: _MongoDatabase,
    telemetry: _Collection,
    sql: _SqlDatabase,
) -> tuple[Any, dict[str, Callable[..., Any]]]:
    return create_dbms_mongo_router(
        fetch_one=sql.fetch_one,
        jsonable=jsonable,
        mongo_ready=lambda: telemetry,
        admin_dependency=admin_role_dependency,
        mongo_database_ready=lambda: mongo,
        mongodb_database_name="apexgrid-factory",
        fetch_all=sql.fetch_all,
    )


def _factory_client(
    mongo: _MongoDatabase,
    telemetry: _Collection,
    sql: _SqlDatabase,
    role: str = "ADMIN",
) -> TestClient:
    rt, _handlers = _factory(mongo, telemetry, sql)
    factory_app = FastAPI()
    factory_app.include_router(rt)
    factory_app.dependency_overrides[current_user] = lambda: _user(role)
    return TestClient(factory_app)


def test_factory_router_registers_every_dbms_route_and_handler(
    mongo: _MongoDatabase,
    telemetry: _Collection,
    sql: _SqlDatabase,
) -> None:
    rt, handlers = _factory(mongo, telemetry, sql)

    assert {route.path for route in rt.routes} == {
        "/api/dbms/overview",
        "/api/dbms/telemetry",
        "/api/dbms/mongo/collections",
        "/api/dbms/mongo/collections/{collection_name}",
        "/api/dbms/polyglot",
    }
    assert set(handlers) == {
        "dbms_overview",
        "dbms_telemetry",
        "dbms_mongo_collections",
        "dbms_mongo_collection_documents",
        "dbms_polyglot",
    }


@pytest.mark.parametrize("path", PRIVILEGED_PATHS)
def test_factory_router_forbids_non_admin_roles(
    mongo: _MongoDatabase,
    telemetry: _Collection,
    sql: _SqlDatabase,
    path: str,
) -> None:
    response = _factory_client(mongo, telemetry, sql, role="STEWARD").get(path)

    assert response.status_code == 403
    assert telemetry.calls == []
    assert sql.queries == []


def test_factory_collection_listing_uses_the_injected_database_name(
    mongo: _MongoDatabase,
    telemetry: _Collection,
    sql: _SqlDatabase,
) -> None:
    body = _factory_client(mongo, telemetry, sql).get("/api/dbms/mongo/collections").json()

    assert body["store"] == "MongoDB"
    assert body["database"] == "apexgrid-factory"
    assert [item["name"] for item in body["collections"]] == ["empty_events", "telemetry"]
    telemetry_entry = body["collections"][1]
    assert telemetry_entry["document_count"] == 5
    assert telemetry_entry["indexes"] == [
        {"name": "_id_", "key": [["_id", 1]]},
        {"name": "ts_1", "key": [["ts", 1]]},
    ]


def test_factory_collection_listing_returns_503_on_enumeration_failure(
    telemetry: _Collection,
    sql: _SqlDatabase,
) -> None:
    unreachable = _MongoDatabase({}, list_error=PyMongoError("server selection timed out"))

    response = _factory_client(unreachable, telemetry, sql).get("/api/dbms/mongo/collections")

    assert response.status_code == 503
    assert response.json()["detail"] == "Could not inspect MongoDB collections"


def test_factory_document_browse_filters_orders_and_paginates(
    mongo: _MongoDatabase,
    telemetry: _Collection,
    sql: _SqlDatabase,
) -> None:
    response = _factory_client(mongo, telemetry, sql).get(
        "/api/dbms/mongo/collections/telemetry",
        params={"driver_id": "driver-2", "limit": 2, "offset": 1},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["filters"] == {"driver_id": "driver-2"}
    assert body["total"] == 3
    assert [item["id"] for item in body["documents"]] == ["doc-3", "doc-1"]
    assert all("_id" not in item for item in body["documents"])


@pytest.mark.parametrize("name", ["system.profile", "missing_collection"])
def test_factory_document_browse_returns_404_for_hidden_or_unknown_collections(
    mongo: _MongoDatabase,
    telemetry: _Collection,
    sql: _SqlDatabase,
    name: str,
) -> None:
    response = _factory_client(mongo, telemetry, sql).get(f"/api/dbms/mongo/collections/{name}")

    assert response.status_code == 404
    assert response.json()["detail"] == "MongoDB collection not found"


def test_factory_document_browse_rejects_invalid_limit_with_422(
    mongo: _MongoDatabase,
    telemetry: _Collection,
    sql: _SqlDatabase,
) -> None:
    response = _factory_client(mongo, telemetry, sql).get(
        "/api/dbms/mongo/collections/telemetry", params={"limit": 0}
    )

    assert response.status_code == 422
    assert telemetry.calls == []


def test_factory_document_browse_returns_503_when_reads_fail(
    telemetry: _Collection,
    sql: _SqlDatabase,
) -> None:
    failing = _MongoDatabase({"telemetry": _Collection(error=RuntimeError("cursor lost"))})

    response = _factory_client(failing, telemetry, sql).get("/api/dbms/mongo/collections/telemetry")

    assert response.status_code == 503
    assert response.json()["detail"] == "Could not read MongoDB collection"


def test_factory_overview_reports_counts_and_mongo_status(
    mongo: _MongoDatabase,
    telemetry: _Collection,
    sql: _SqlDatabase,
) -> None:
    body = _factory_client(mongo, telemetry, sql).get("/api/dbms/overview").json()

    assert body["active_sessions"] == 2
    assert body["official_results"] == 12
    assert body["telemetry_samples"] == 5
    assert body["mongodb"] == "up"
    assert body["postgres"] == "up"


def test_factory_overview_reports_mongo_down_when_telemetry_is_offline(
    mongo: _MongoDatabase,
    sql: _SqlDatabase,
) -> None:
    offline = _Collection(error=PyMongoError("server selection timed out"))

    response = _factory_client(mongo, offline, sql).get("/api/dbms/overview")

    assert response.status_code == 200
    assert response.json()["mongodb"] == "down"
    assert response.json()["telemetry_samples"] is None


def test_factory_telemetry_route_reports_count_and_newest_samples(
    mongo: _MongoDatabase,
    telemetry: _Collection,
    sql: _SqlDatabase,
) -> None:
    body = _factory_client(mongo, telemetry, sql).get("/api/dbms/telemetry").json()

    assert body["count"] == 5
    assert body["indexes"] == ["_id_", "ts_1"]
    assert [item["lap"] for item in body["sample"]] == [5, 4, 3]


def test_factory_telemetry_route_returns_503_when_inspection_fails(
    mongo: _MongoDatabase,
    sql: _SqlDatabase,
) -> None:
    broken = _Collection(error=RuntimeError("collection stats unavailable"))

    response = _factory_client(mongo, broken, sql).get("/api/dbms/telemetry")

    assert response.status_code == 503
    assert response.json()["detail"] == "Could not inspect MongoDB telemetry"


def test_factory_polyglot_merges_telemetry_into_relational_rows(
    mongo: _MongoDatabase,
    telemetry: _Collection,
    sql: _SqlDatabase,
) -> None:
    telemetry.aggregate_rows = [
        {
            "_id": {"session_id": "s1", "driver_id": "d1"},
            "samples": 4,
            "latest": datetime(2026, 10, 26, 12, 4, tzinfo=UTC),
        }
    ]

    body = _factory_client(mongo, telemetry, sql).get("/api/dbms/polyglot").json()

    assert body["relational_rows"] == 2
    assert body["rows"][0]["telemetry"]["samples"] == 4
    assert body["rows"][1]["telemetry"] == {"samples": 0}
    assert telemetry.pipelines[0][2] == {"$limit": 5000}
