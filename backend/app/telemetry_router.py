from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo.collection import Collection

from .schemas_telemetry import Telemetry
from .telemetry_repository import (
    TelemetryIngestError,
    driver_exists,
    get_live_session,
    get_live_telemetry,
    insert_telemetry,
    list_telemetry,
    session_exists,
)

INGEST_ERROR_RESPONSES = {
    "session_not_found": (404, "Session not found"),
    "session_inactive": (
        409,
        "Telemetry can only be ingested for an active session",
    ),
    "driver_not_found": (404, "Driver not found"),
    "out_of_order": (409, "Telemetry is out of order"),
}


def create_telemetry_router(
    current_user: Callable[..., Any],
    jsonable: Callable[[Any], Any],
    mongo_ready: Callable[[], Collection[dict[str, Any]]],
    roles: Callable[..., Any],
    telemetry_ws_payload: Callable[[dict[str, Any], Any], dict[str, Any]],
    publish: Callable[[UUID, str, dict[str, Any]], Any],
) -> APIRouter:
    router = APIRouter()
    ingest_dependency = Depends(roles("ADMIN", "STEWARD"))
    authenticated_user = Depends(current_user)

    @router.post("/api/telemetry/ingest", status_code=202, response_model=None)
    def ingest(packet: Telemetry, user: dict[str, object] = ingest_dependency) -> dict[str, object]:
        collection = mongo_ready()
        document = packet.model_dump(mode="json")
        document["session_id"] = str(packet.session_id)
        document["driver_id"] = str(packet.driver_id)
        document["ts"] = packet.ts
        try:
            result = insert_telemetry(collection, packet.session_id, packet.driver_id, document)
        except TelemetryIngestError as exc:
            status_code, detail = INGEST_ERROR_RESPONSES.get(
                exc.outcome, (503, "Telemetry store write failed")
            )
            raise HTTPException(status_code, detail) from exc
        stored = {key: value for key, value in result.document.items() if key != "_id"}
        clean = telemetry_ws_payload(stored, result.inserted_id)
        if result.inserted:
            publish(packet.session_id, "telemetry.sample", clean)
        return {"accepted": True, "packet": clean}

    @router.get("/api/telemetry", response_model=None)
    def telemetry(
        session_id: UUID,
        driver_id: UUID | None = None,
        limit: int = Query(50, ge=1, le=200),
        user: dict[str, object] = authenticated_user,
    ) -> list[dict[str, object]]:
        if not session_exists(session_id):
            raise HTTPException(404, "Session not found")
        if driver_id and not driver_exists(driver_id):
            raise HTTPException(404, "Driver not found")
        collection = mongo_ready()
        documents = list_telemetry(collection, session_id, driver_id, limit)
        return [
            {
                **cast(
                    dict[str, object],
                    jsonable({key: value for key, value in doc.items() if key != "_id"}),
                ),
                "id": str(doc["_id"]),
            }
            for doc in documents
        ]

    @router.get("/api/sessions/{session_id}/live", response_model=None)
    def live(session_id: UUID, user: dict[str, object] = authenticated_user) -> dict[str, object]:
        session = get_live_session(session_id)
        if not session:
            raise HTTPException(404, "Session not found")
        collection = mongo_ready()
        latest, drivers = get_live_telemetry(collection, session_id, session["scheduled_at"])
        packets = [
            {
                **cast(
                    dict[str, object],
                    jsonable({key: value for key, value in doc.items() if key != "_id"}),
                ),
                "id": str(doc["_id"]),
            }
            for doc in latest
        ]
        return {"session": jsonable(session), "drivers": jsonable(drivers), "packets": packets}

    return router
