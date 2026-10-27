from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any

from app.api.dbms_mongo import create_dbms_mongo_router
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.testclient import TestClient
from pymongo.errors import PyMongoError


class MemoryCursor:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = list(rows)

    def sort(self, key: str, direction: int) -> MemoryCursor:
        self.rows.sort(key=lambda row: row[key], reverse=direction < 0)
        return self

    def skip(self, offset: int) -> MemoryCursor:
        self.rows = self.rows[offset:]
        return self

    def limit(self, count: int) -> MemoryCursor:
        self.rows = self.rows[:count]
        return self

    def __iter__(self) -> Iterator[dict[str, Any]]:
        return iter(self.rows)


class MemoryCollection:
    def __init__(self, rows: list[dict[str, Any]], indexes: dict[str, Any] | None = None):
        self.rows = rows
        self.indexes = indexes or {"_id_": {"key": [["_id", 1]]}}
        self.fail_count: Exception | None = None
        self.fail_estimated_count: Exception | None = None

    def _matching(self, filters: dict[str, Any]) -> list[dict[str, Any]]:
        return [row.copy() for row in self.rows if all(row.get(k) == v for k, v in filters.items())]

    def count_documents(self, filters: dict[str, Any]) -> int:
        if self.fail_count:
            raise self.fail_count
        return len(self._matching(filters))

    def estimated_document_count(self) -> int:
        if self.fail_estimated_count:
            raise self.fail_estimated_count
        return len(self.rows)

    def index_information(self) -> dict[str, Any]:
        return self.indexes

    def find(
        self, filters: dict[str, Any], projection: dict[str, int] | None = None
    ) -> MemoryCursor:
        rows = self._matching(filters)
        if projection and projection.get("_id") == 0:
            rows = [{key: value for key, value in row.items() if key != "_id"} for row in rows]
        return MemoryCursor(rows)


class MemoryDatabase:
    def __init__(self, collections: dict[str, MemoryCollection]):
        self.collections = collections
        self.fail_listing: Exception | None = None

    def list_collection_names(self) -> list[str]:
        if self.fail_listing:
            raise self.fail_listing
        return list(self.collections)

    def __getitem__(self, name: str) -> MemoryCollection:
        return self.collections[name]


class MemoryTelemetry(MemoryCollection):
    def __init__(self, rows: list[dict[str, Any]], polyglot_rows: list[dict[str, Any]]):
        super().__init__(
            rows,
            {"_id_": {"key": [["_id", 1]]}, "ts_1": {"key": [["ts", 1]]}},
        )
        self.polyglot_rows = polyglot_rows
        self.pipelines: list[list[dict[str, Any]]] = []
        self.aggregate_failure: Exception | None = None

    def aggregate(self, pipeline: list[dict[str, Any]]) -> list[dict[str, Any]]:
        self.pipelines.append(pipeline)
        if self.aggregate_failure:
            raise self.aggregate_failure
        return list(self.polyglot_rows)


def make_client() -> tuple[TestClient, MemoryDatabase, MemoryTelemetry, list[str]]:
    now = datetime.now(UTC)
    docs = [
        {
            "_id": f"doc-{index}",
            "session_id": "session-a" if index <= 4 else "session-b",
            "driver_id": "driver-1" if index % 2 else "driver-2",
            "lap": index,
            "sector": 2,
            "ts": now - timedelta(minutes=index),
            "speed_kph": 200 + index,
        }
        for index in range(1, 6)
    ]
    telemetry = MemoryTelemetry(docs, [])
    database = MemoryDatabase(
        {
            "telemetry": telemetry,
            "events": MemoryCollection([], {"_id_": {"key": [["_id", 1]]}}),
            "system.profile": MemoryCollection([]),
        }
    )
    sql_calls: list[str] = []

    def fetch_one(_sql: str) -> dict[str, int]:
        return {
            "active_sessions": 1,
            "completed_sessions": 2,
            "open_incidents": 3,
            "reserved_pit_stops": 4,
            "completed_pit_stops": 5,
            "official_results": 6,
        }

    def fetch_all(sql: str) -> list[dict[str, Any]]:
        sql_calls.append(sql)
        return [
            {"session_id": "session-a", "driver_id": "driver-1", "state": "ACTIVE"},
            {"session_id": "session-a", "driver_id": "driver-2", "state": "ACTIVE"},
            {"session_id": "session-b", "driver_id": "driver-9", "state": "COMPLETED"},
        ]

    def require_admin(x_role: str = Header(default="")) -> str:
        if x_role != "ADMIN":
            raise HTTPException(status_code=403, detail="Admin role required")
        return x_role

    router, _handlers = create_dbms_mongo_router(
        fetch_one=fetch_one,
        jsonable=lambda value: value,
        mongo_ready=lambda: telemetry,
        admin_dependency=Depends(require_admin),
        mongo_database_ready=lambda: database,
        mongodb_database_name="test_db",
        fetch_all=fetch_all,
    )
    app = FastAPI()
    app.include_router(router)
    return TestClient(app), database, telemetry, sql_calls


def test_factory_collection_listing_reports_sorted_real_metadata_and_admin_gate():
    client, _database, _telemetry, _sql_calls = make_client()

    denied = client.get("/api/dbms/mongo/collections")
    response = client.get("/api/dbms/mongo/collections", headers={"X-Role": "ADMIN"})

    assert denied.status_code == 403
    assert response.status_code == 200
    body = response.json()
    assert body["store"] == "MongoDB"
    assert body["database"] == "test_db"
    assert [entry["name"] for entry in body["collections"]] == ["events", "telemetry"]
    assert body["collections"][0]["document_count"] == 0
    assert body["collections"][1]["document_count"] == 5
    assert body["collections"][1]["indexes"] == [
        {"name": "_id_", "key": [["_id", 1]]},
        {"name": "ts_1", "key": [["ts", 1]]},
    ]
    assert body["updated_at"]


def test_factory_document_browse_applies_all_filters_then_sorts_and_paginates():
    client, _database, _telemetry, _sql_calls = make_client()

    response = client.get(
        "/api/dbms/mongo/collections/telemetry",
        params={
            "session_id": "session-a",
            "driver_id": "driver-2",
            "lap": 4,
            "sector": 2,
            "limit": 1,
            "offset": 0,
        },
        headers={"X-Role": "ADMIN"},
    )
    page = client.get(
        "/api/dbms/mongo/collections/telemetry",
        params={"session_id": "session-a", "sector": 2, "limit": 2, "offset": 1},
        headers={"X-Role": "ADMIN"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["filters"] == {
        "session_id": "session-a",
        "driver_id": "driver-2",
        "lap": 4,
        "sector": 2,
    }
    assert body["total"] == 1
    assert (body["limit"], body["offset"]) == (1, 0)
    assert body["documents"] == [
        {
            "session_id": "session-a",
            "driver_id": "driver-2",
            "lap": 4,
            "sector": 2,
            "ts": body["documents"][0]["ts"],
            "speed_kph": 204,
            "id": "doc-4",
        }
    ]
    assert "_id" not in body["documents"][0]
    assert page.status_code == 200
    assert page.json()["total"] == 4
    assert (page.json()["limit"], page.json()["offset"]) == (2, 1)
    assert [item["id"] for item in page.json()["documents"]] == ["doc-2", "doc-3"]
    assert [item["lap"] for item in page.json()["documents"]] == [2, 3]


def test_factory_empty_unknown_and_invalid_document_browse_cases():
    client, _database, _telemetry, _sql_calls = make_client()
    headers = {"X-Role": "ADMIN"}

    empty = client.get("/api/dbms/mongo/collections/events", headers=headers)
    unknown = client.get("/api/dbms/mongo/collections/system.profile", headers=headers)
    missing = client.get("/api/dbms/mongo/collections/missing", headers=headers)
    invalid = client.get("/api/dbms/mongo/collections/telemetry?limit=101", headers=headers)

    assert empty.status_code == 200
    assert empty.json()["documents"] == []
    assert empty.json()["total"] == 0
    assert unknown.status_code == missing.status_code == 404
    assert unknown.json() == missing.json() == {"detail": "MongoDB collection not found"}
    assert invalid.status_code == 422
    assert invalid.json()["detail"]


def test_factory_overview_and_telemetry_report_counts_indexes_and_recent_samples():
    client, _database, telemetry, _sql_calls = make_client()
    headers = {"X-Role": "ADMIN"}

    overview = client.get("/api/dbms/overview", headers=headers)
    telemetry_response = client.get("/api/dbms/telemetry", headers=headers)

    assert overview.status_code == 200
    assert {
        key: overview.json()[key]
        for key in (
            "active_sessions",
            "completed_sessions",
            "open_incidents",
            "reserved_pit_stops",
            "completed_pit_stops",
            "official_results",
            "telemetry_samples",
            "postgres",
            "mongodb",
        )
    } == {
        "active_sessions": 1,
        "completed_sessions": 2,
        "open_incidents": 3,
        "reserved_pit_stops": 4,
        "completed_pit_stops": 5,
        "official_results": 6,
        "telemetry_samples": 5,
        "postgres": "up",
        "mongodb": "up",
    }
    assert telemetry_response.status_code == 200
    body = telemetry_response.json()
    assert body["store"] == "MongoDB"
    assert body["count"] == 5
    assert body["indexes"] == ["_id_", "ts_1"]
    assert [row["speed_kph"] for row in body["sample"]] == [201, 202, 203]
    assert all("_id" not in row for row in body["sample"])
    assert all("id" not in row for row in body["sample"])
    assert telemetry.estimated_document_count() == 5


def test_factory_overview_reports_mongo_down_and_telemetry_inspection_failure():
    client, _database, telemetry, _sql_calls = make_client()
    telemetry.fail_count = PyMongoError("synthetic telemetry outage")
    telemetry.fail_estimated_count = PyMongoError("synthetic telemetry outage")
    headers = {"X-Role": "ADMIN"}

    overview = client.get("/api/dbms/overview", headers=headers)
    inspection = client.get("/api/dbms/telemetry", headers=headers)

    assert overview.status_code == 200
    assert overview.json()["mongodb"] == "down"
    assert overview.json()["telemetry_samples"] is None
    assert inspection.status_code == 503
    assert inspection.json() == {"detail": "Could not inspect MongoDB telemetry"}


def test_factory_polyglot_joins_rows_by_session_and_driver_with_zero_sample_fallback():
    client, _database, telemetry, sql_calls = make_client()
    telemetry.polyglot_rows = [
        {
            "_id": {"session_id": "session-a", "driver_id": "driver-1"},
            "samples": 7,
            "latest": datetime(2026, 10, 1, tzinfo=UTC),
        }
    ]

    response = client.get("/api/dbms/polyglot", headers={"X-Role": "ADMIN"})

    assert response.status_code == 200
    body = response.json()
    assert body["relational_rows"] == 3
    assert body["rows"][0]["telemetry"]["samples"] == 7
    assert body["rows"][1]["telemetry"] == {"samples": 0}
    assert body["rows"][2]["telemetry"] == {"samples": 0}
    assert "UNION SELECT session_id,driver_id FROM demo_race_entries" in sql_calls[0]
    assert telemetry.pipelines[0][0]["$match"]["ts"]["$gte"] < datetime.now(UTC)
    assert telemetry.pipelines[0][1] == {"$sort": {"ts": -1}}
    assert telemetry.pipelines[0][2] == {"$limit": 5000}


def test_factory_polyglot_returns_exact_empty_join_shape():
    client, _database, telemetry, _sql_calls = make_client()
    telemetry.polyglot_rows = []

    response = client.get("/api/dbms/polyglot", headers={"X-Role": "ADMIN"})

    assert response.status_code == 200
    assert response.json() == {
        "relational_rows": 3,
        "rows": [
            {
                "session_id": "session-a",
                "driver_id": "driver-1",
                "state": "ACTIVE",
                "telemetry": {"samples": 0},
            },
            {
                "session_id": "session-a",
                "driver_id": "driver-2",
                "state": "ACTIVE",
                "telemetry": {"samples": 0},
            },
            {
                "session_id": "session-b",
                "driver_id": "driver-9",
                "state": "COMPLETED",
                "telemetry": {"samples": 0},
            },
        ],
    }
