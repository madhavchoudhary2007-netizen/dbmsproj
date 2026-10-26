from __future__ import annotations

from collections.abc import Callable
from typing import Annotated, Any, cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pymongo.collection import Collection

from .api.laps import get_race_db, get_race_telemetry
from .core.request_auth import current_user
from .core.request_database import DatabaseSession
from .core.runtime import get_simulations
from .core.serialization import jsonable
from .pit_repository import load_pit_strategy_rows, load_pit_telemetry
from .pit_strategy_service import (
    project_pit_strategy,
    tire_stint_target,
)
from .simulation_core import MAX_SESSION_LAPS, Simulation

StrategyRows = tuple[dict[str, Any] | None, list[dict[str, Any]], list[dict[str, Any]]]
TelemetryRows = tuple[dict[str, dict[str, Any]], dict[str, int], dict[str, str]]

router = APIRouter()
pit_strategy_router = router

authenticated_user = Depends(current_user)


def _resolve_simulations(
    simulations: dict[str, Simulation] | None = None,
) -> dict[str, Simulation]:
    if simulations is not None:
        return simulations
    import sys

    main_module = sys.modules.get("backend.app.main") or sys.modules.get("app.main")
    if main_module is not None and hasattr(main_module, "simulations"):
        return cast(dict[str, Simulation], main_module.simulations)
    return {}


def _resolve_collection(
    collection: Collection[dict[str, Any]] | None = None,
) -> Collection[dict[str, Any]] | None:
    if collection is not None:
        return collection
    import sys

    main_module = sys.modules.get("backend.app.main") or sys.modules.get("app.main")
    if main_module is not None and hasattr(main_module, "mongo_ready"):
        try:
            return cast(Collection[dict[str, Any]] | None, main_module.mongo_ready())
        except HTTPException:
            return None
    return None


@router.get("/api/sessions/{session_id}/pit-strategy", response_model=None)
def pit_strategy(
    session_id: UUID,
    user: Annotated[dict[str, Any], authenticated_user],
    collection: Annotated[Collection[dict[str, Any]], Depends(get_race_telemetry)],
    database: Annotated[DatabaseSession, Depends(get_race_db)],
    simulations: Annotated[dict[str, Simulation], Depends(get_simulations)],
) -> dict[str, object]:
    session, drivers, reservations = load_pit_strategy_rows(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    sims = _resolve_simulations(simulations)
    sim = sims.get(str(session_id))
    is_live = session["state"] in {"ACTIVE", "PAUSED"} and sim is not None and sim.is_generated
    col = _resolve_collection(collection)
    if col is not None:
        latest_by_driver, stop_lap_by_id, stop_compound_by_id = load_pit_telemetry(col, session_id)
    elif is_live:
        raise HTTPException(503, "MongoDB telemetry store is unavailable")
    else:
        latest_by_driver = {}
        stop_lap_by_id = {}
        stop_compound_by_id = {}

    stops_by_driver: dict[str, list[dict[str, Any]]] = {}
    for row in reservations:
        driver_id = str(row.get("driver_id") or "")
        if not driver_id:
            continue
        stops_by_driver.setdefault(driver_id, []).append(
            {
                "reservation_id": row["id"],
                "lap": stop_lap_by_id.get(str(row["id"])),
                "compound": stop_compound_by_id.get(str(row["id"])),
                "box_number": row.get("box_number"),
                "status": row.get("status"),
                "starts_at": row.get("starts_at"),
                "ends_at": row.get("ends_at"),
            }
        )

    projected = project_pit_strategy(
        session_id,
        session["state"],
        session["generated"],
        is_live,
        session["total_laps"],
        MAX_SESSION_LAPS,
        drivers,
        latest_by_driver,
        stops_by_driver,
        sim,
        tire_stint_target,
    )
    return cast(dict[str, object], jsonable(projected))


def create_pit_strategy_router(
    current_user: Callable[..., Any],
    load_strategy_rows: Callable[[UUID], StrategyRows],
    load_telemetry: Callable[[Collection[dict[str, Any]], UUID], TelemetryRows],
    mongo_ready: Callable[[], Collection[dict[str, Any]]],
    get_simulation: Callable[[str], Simulation | None],
    project_strategy: Callable[..., dict[str, Any]],
    max_session_laps: int,
    tire_stint_target: Callable[[str, int], int],
    jsonable: Callable[[Any], Any],
) -> tuple[APIRouter, Callable[..., Any]]:
    rt = APIRouter()
    auth_user = Depends(current_user)

    @rt.get("/api/sessions/{session_id}/pit-strategy", response_model=None)
    def pit_strategy(session_id: UUID, user: dict[str, object] = auth_user) -> dict[str, object]:
        session, drivers, reservations = load_strategy_rows(session_id)
        if not session:
            raise HTTPException(404, "Session not found")

        sim = get_simulation(str(session_id))
        is_live = session["state"] in {"ACTIVE", "PAUSED"} and sim is not None and sim.is_generated
        collection = mongo_ready()
        if collection is not None:
            latest_by_driver, stop_lap_by_id, stop_compound_by_id = load_telemetry(
                collection, session_id
            )
        elif is_live:
            raise HTTPException(503, "MongoDB telemetry store is unavailable")
        else:
            latest_by_driver = {}
            stop_lap_by_id = {}
            stop_compound_by_id = {}

        stops_by_driver: dict[str, list[dict[str, Any]]] = {}
        for row in reservations:
            driver_id = str(row.get("driver_id") or "")
            if not driver_id:
                continue
            stops_by_driver.setdefault(driver_id, []).append(
                {
                    "reservation_id": row["id"],
                    "lap": stop_lap_by_id.get(str(row["id"])),
                    "compound": stop_compound_by_id.get(str(row["id"])),
                    "box_number": row.get("box_number"),
                    "status": row.get("status"),
                    "starts_at": row.get("starts_at"),
                    "ends_at": row.get("ends_at"),
                }
            )

        projected = project_strategy(
            session_id,
            session["state"],
            session["generated"],
            is_live,
            session["total_laps"],
            max_session_laps,
            drivers,
            latest_by_driver,
            stops_by_driver,
            sim,
            tire_stint_target,
        )
        return cast(dict[str, object], jsonable(projected))

    return rt, pit_strategy
