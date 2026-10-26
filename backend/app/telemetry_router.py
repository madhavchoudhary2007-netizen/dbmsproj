from __future__ import annotations

from collections.abc import Callable
from typing import Annotated, Any, cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo.collection import Collection

from .api.laps import get_race_db, get_race_telemetry
from .core.events import EventBus
from .core.request_auth import current_user, require_roles
from .core.request_database import DatabaseSession
from .core.runtime import get_bus
from .core.serialization import jsonable, telemetry_ws_payload
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

router = APIRouter()
telemetry_router = router

admin_steward_dependency = Depends(require_roles("ADMIN", "STEWARD"))
authenticated_user = Depends(current_user)


def _resolve_bus(bus: EventBus | None = None) -> EventBus:
    if bus is not None:
        return bus
    import sys

    main_module = sys.modules.get("backend.app.main") or sys.modules.get("app.main")
    if main_module is not None and hasattr(main_module, "bus"):
        return cast(EventBus, main_module.bus)

    return EventBus()


def _resolve_publish(
    bus: EventBus | None = None,
) -> Callable[[UUID | str, str, Any], None]:
    import sys

    main_module = sys.modules.get("backend.app.main") or sys.modules.get("app.main")
    main_publish = getattr(main_module, "publish", None) if main_module is not None else None
    orig_publish = (
        getattr(main_module, "_default_publish", None) if main_module is not None else None
    )
    if main_publish is not None and (orig_publish is None or main_publish is not orig_publish):
        return cast(Callable[[UUID | str, str, Any], None], main_publish)

    def _publish_event(session_id: UUID | str, kind: str, data: Any) -> None:
        from datetime import UTC, datetime

        b = _resolve_bus(bus)
        b.send(
            session_id,
            {
                "type": kind,
                "ts": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                "session_id": str(session_id),
                "data": jsonable(data),
            },
        )

    return _publish_event


@router.post("/api/telemetry/ingest", status_code=202, response_model=None)
def ingest(
    packet: Telemetry,
    user: Annotated[dict[str, Any], admin_steward_dependency],
    collection: Annotated[Collection[dict[str, Any]], Depends(get_race_telemetry)],
    bus: Annotated[EventBus, Depends(get_bus)],
) -> dict[str, object]:
    col = collection
    if col is None:
        import sys

        main_module = sys.modules.get("backend.app.main") or sys.modules.get("app.main")
        if main_module is not None and hasattr(main_module, "mongo_ready"):
            col = main_module.mongo_ready()
    if col is None:
        raise HTTPException(503, "MongoDB telemetry store is unavailable")

    document = packet.model_dump(mode="json")
    document["session_id"] = str(packet.session_id)
    document["driver_id"] = str(packet.driver_id)
    document["ts"] = packet.ts
    try:
        result = insert_telemetry(col, packet.session_id, packet.driver_id, document)
    except TelemetryIngestError as exc:
        status_code, detail = INGEST_ERROR_RESPONSES.get(
            exc.outcome, (503, "Telemetry store write failed")
        )
        raise HTTPException(status_code, detail) from exc
    stored = {key: value for key, value in result.document.items() if key != "_id"}
    clean = telemetry_ws_payload(stored, result.inserted_id)
    if result.inserted:
        _resolve_publish(bus)(packet.session_id, "telemetry.sample", clean)
    return {"accepted": True, "packet": clean}


@router.get("/api/telemetry", response_model=None)
def telemetry(
    session_id: UUID,
    user: Annotated[dict[str, Any], authenticated_user],
    collection: Annotated[Collection[dict[str, Any]], Depends(get_race_telemetry)],
    database: Annotated[DatabaseSession, Depends(get_race_db)],
    driver_id: UUID | None = None,
    limit: int = Query(50, ge=1, le=200),
) -> list[dict[str, object]]:
    if database is not None:
        has_session = (
            database.fetch_one("SELECT 1 FROM race_sessions WHERE id=%s", (session_id,)) is not None
        )
    else:
        has_session = session_exists(session_id)
    if not has_session:
        raise HTTPException(404, "Session not found")
    if driver_id:
        if database is not None:
            has_driver = (
                database.fetch_one("SELECT 1 FROM drivers WHERE id=%s", (driver_id,)) is not None
            )
        else:
            has_driver = driver_exists(driver_id)
        if not has_driver:
            raise HTTPException(404, "Driver not found")

    col = collection
    if col is None:
        import sys

        main_module = sys.modules.get("backend.app.main") or sys.modules.get("app.main")
        if main_module is not None and hasattr(main_module, "mongo_ready"):
            col = main_module.mongo_ready()
    if col is None:
        raise HTTPException(503, "MongoDB telemetry store is unavailable")

    documents = list_telemetry(col, session_id, driver_id, limit)
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
def live(
    session_id: UUID,
    user: Annotated[dict[str, Any], authenticated_user],
    collection: Annotated[Collection[dict[str, Any]], Depends(get_race_telemetry)],
    database: Annotated[DatabaseSession, Depends(get_race_db)],
) -> dict[str, object]:
    if database is not None:
        session = database.fetch_one("SELECT * FROM race_sessions WHERE id=%s", (session_id,))
    else:
        session = get_live_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    col = collection
    if col is None:
        import sys

        main_module = sys.modules.get("backend.app.main") or sys.modules.get("app.main")
        if main_module is not None and hasattr(main_module, "mongo_ready"):
            col = main_module.mongo_ready()
    if col is None:
        raise HTTPException(503, "MongoDB telemetry store is unavailable")

    latest, drivers = get_live_telemetry(col, session_id, session["scheduled_at"])
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


def create_telemetry_router(
    current_user: Callable[..., Any],
    jsonable: Callable[[Any], Any],
    mongo_ready: Callable[[], Collection[dict[str, Any]]],
    roles: Callable[..., Any],
    telemetry_ws_payload: Callable[[dict[str, Any], Any], dict[str, Any]],
    publish: Callable[[UUID, str, dict[str, Any]], Any],
) -> APIRouter:
    rt = APIRouter()
    ingest_dependency = Depends(roles("ADMIN", "STEWARD"))
    auth_user = Depends(current_user)

    @rt.post("/api/telemetry/ingest", status_code=202, response_model=None)
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

    @rt.get("/api/telemetry", response_model=None)
    def telemetry(
        session_id: UUID,
        driver_id: UUID | None = None,
        limit: int = Query(50, ge=1, le=200),
        user: dict[str, object] = auth_user,
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

    @rt.get("/api/sessions/{session_id}/live", response_model=None)
    def live(session_id: UUID, user: dict[str, object] = auth_user) -> dict[str, object]:
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

    return rt
