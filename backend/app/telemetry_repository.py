from typing import Any
from uuid import UUID

from pymongo import DESCENDING
from pymongo.collection import Collection

from .database import fetch_one


def session_exists(session_id: UUID) -> bool:
    return fetch_one("SELECT 1 FROM race_sessions WHERE id=%s", (session_id,)) is not None


def driver_exists(driver_id: UUID) -> bool:
    return fetch_one("SELECT 1 FROM drivers WHERE id=%s", (driver_id,)) is not None


def list_telemetry(
    collection: Collection[dict[str, Any]],
    session_id: UUID,
    driver_id: UUID | None,
    limit: int,
) -> list[dict[str, Any]]:
    query: dict[str, str] = {"session_id": str(session_id)}
    if driver_id is not None:
        query["driver_id"] = str(driver_id)
    return list(collection.find(query).sort("ts", DESCENDING).limit(limit))
