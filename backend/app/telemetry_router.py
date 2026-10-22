from __future__ import annotations

from collections.abc import Callable
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo.collection import Collection

from .telemetry_repository import (
    driver_exists,
    get_live_session,
    get_live_telemetry,
    list_telemetry,
    session_exists,
)


def create_telemetry_router(
    current_user: Callable[..., Any],
    jsonable: Callable[[Any], Any],
    mongo_ready: Callable[[], Collection[dict[str, Any]]],
) -> APIRouter:
    router = APIRouter()

    @router.get("/api/telemetry")
    def telemetry(
        session_id: UUID,
        driver_id: UUID | None = None,
        limit: int = Query(50, ge=1, le=200),
        user=Depends(current_user),
    ):
        if not session_exists(session_id):
            raise HTTPException(404, "Session not found")
        if driver_id and not driver_exists(driver_id):
            raise HTTPException(404, "Driver not found")
        collection = mongo_ready()
        documents = list_telemetry(collection, session_id, driver_id, limit)
        return [
            {**jsonable({key: value for key, value in doc.items() if key != "_id"}), "id": str(doc["_id"])}
            for doc in documents
        ]

    @router.get("/api/sessions/{session_id}/live")
    def live(session_id: UUID, user=Depends(current_user)):
        session = get_live_session(session_id)
        if not session:
            raise HTTPException(404, "Session not found")
        collection = mongo_ready()
        latest, drivers = get_live_telemetry(collection, session_id, session["scheduled_at"])
        packets = [
            {**jsonable({key: value for key, value in doc.items() if key != "_id"}), "id": str(doc["_id"])}
            for doc in latest
        ]
        return {"session": jsonable(session), "drivers": jsonable(drivers), "packets": packets}

    return router
