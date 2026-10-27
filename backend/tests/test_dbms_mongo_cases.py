from __future__ import annotations

import os
import sys
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
_prior_app_env = os.environ.get("APP_ENV")
os.environ.setdefault("APP_ENV", "local")
try:
    from backend.app.api.dbms_mongo import get_mongo_db
    from backend.app.api.laps import current_user
    from backend.app.main import app
finally:
    if _prior_app_env is None:
        os.environ.pop("APP_ENV", None)
    else:
        os.environ["APP_ENV"] = _prior_app_env


class _Cursor:
    def __init__(self, documents: list[dict[str, Any]]) -> None:
        self.documents = documents

    def sort(self, key: str, direction: int) -> _Cursor:
        self.documents.sort(key=lambda doc: doc[key], reverse=direction == -1)
        return self

    def skip(self, offset: int) -> _Cursor:
        self.documents = self.documents[offset:]
        return self

    def limit(self, limit: int) -> _Cursor:
        self.documents = self.documents[:limit]
        return self

    def __iter__(self) -> Iterator[dict[str, Any]]:
        return iter(self.documents)


class _Collection:
    def __init__(self, documents: list[dict[str, Any]], indexes: dict[str, Any]) -> None:
        self.documents = documents
        self.indexes = indexes

    def index_information(self) -> dict[str, Any]:
        return self.indexes

    def count_documents(self, filters: dict[str, Any]) -> int:
        return len(self._matching(filters))

    def find(self, filters: dict[str, Any]) -> _Cursor:
        return _Cursor(self._matching(filters))

    def _matching(self, filters: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            dict(document)
            for document in self.documents
            if all(document.get(key) == value for key, value in filters.items())
        ]


class _Database:
    def __init__(self, collections: dict[str, _Collection]) -> None:
        self.collections = collections

    def list_collection_names(self) -> list[str]:
        return list(self.collections)

    def __getitem__(self, name: str) -> _Collection:
        return self.collections[name]


def _telemetry_documents() -> list[dict[str, Any]]:
    base = datetime(2026, 10, 26, 12, tzinfo=UTC)
    return [
        {
            "_id": f"doc-{index}",
            "session_id": "session-a" if index < 4 else "session-b",
            "driver_id": "driver-1" if index % 2 == 0 else "driver-2",
            "lap": index,
            "sector": 2,
            "ts": base + timedelta(minutes=index),
            "speed_kph": 210 + index,
        }
        for index in range(1, 6)
    ]


@pytest.fixture
def client() -> Iterator[TestClient]:
    documents = _telemetry_documents()
    database = _Database(
        {
            "telemetry": _Collection(
                documents,
                {"_id_": {"key": [("_id", 1)]}, "ts_1": {"key": [("ts", 1)]}},
            ),
            "empty_events": _Collection([], {"_id_": {"key": [("_id", 1)]}}),
            "system.profile": _Collection([], {}),
        }
    )
    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[current_user] = lambda: {
        "id": "synthetic-admin",
        "email": "admin@example.invalid",
        "role": "ADMIN",
    }
    app.dependency_overrides[get_mongo_db] = lambda: database
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)


def test_collection_listing_returns_sorted_metadata_and_hides_system_collections(
    client: TestClient,
) -> None:
    response = client.get("/api/dbms/mongo/collections")

    assert response.status_code == 200
    body = response.json()
    assert body["store"] == "MongoDB"
    assert [item["name"] for item in body["collections"]] == ["empty_events", "telemetry"]
    assert body["collections"][0]["document_count"] == 0
    assert body["collections"][1] == {
        "name": "telemetry",
        "document_count": 5,
        "indexes": [
            {"name": "_id_", "key": [["_id", 1]]},
            {"name": "ts_1", "key": [["ts", 1]]},
        ],
    }
    assert body["updated_at"]


def test_document_browse_filters_sorts_and_paginates_with_stable_ids(client: TestClient) -> None:
    response = client.get(
        "/api/dbms/mongo/collections/telemetry",
        params={"session_id": "session-a", "sector": 2, "limit": 2, "offset": 1},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["filters"] == {"session_id": "session-a", "sector": 2}
    assert body["total"] == 3
    assert (body["limit"], body["offset"]) == (2, 1)
    assert [item["id"] for item in body["documents"]] == ["doc-2", "doc-1"]
    assert [item["lap"] for item in body["documents"]] == [2, 1]
    assert all("_id" not in item for item in body["documents"])


def test_empty_collection_page_and_unknown_collection_responses(client: TestClient) -> None:
    empty = client.get("/api/dbms/mongo/collections/empty_events")
    unknown = client.get("/api/dbms/mongo/collections/system.profile")
    missing = client.get("/api/dbms/mongo/collections/not_registered")

    assert empty.status_code == 200
    assert empty.json()["documents"] == []
    assert empty.json()["total"] == 0
    assert unknown.status_code == missing.status_code == 404
    assert unknown.json()["detail"] == missing.json()["detail"] == "MongoDB collection not found"


@pytest.mark.parametrize(
    "params",
    [{"limit": 0}, {"limit": 101}, {"offset": -1}, {"lap": 0}, {"sector": 4}],
)
def test_document_browse_rejects_invalid_pagination_and_filters(
    client: TestClient, params: dict[str, int]
) -> None:
    response = client.get("/api/dbms/mongo/collections/telemetry", params=params)

    assert response.status_code == 422
    assert response.json()["detail"]


def test_collection_service_failure_returns_specific_unavailable_response(
    client: TestClient,
) -> None:
    class _BrokenDatabase:
        def list_collection_names(self) -> list[str]:
            raise RuntimeError("synthetic mongo outage")

    app.dependency_overrides[get_mongo_db] = lambda: _BrokenDatabase()

    response = client.get("/api/dbms/mongo/collections")

    assert response.status_code == 503
    assert response.json() == {"detail": "Could not inspect MongoDB collections"}
