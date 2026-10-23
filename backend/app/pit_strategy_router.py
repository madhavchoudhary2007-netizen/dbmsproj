from __future__ import annotations

from collections.abc import Callable
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pymongo.collection import Collection

from .simulation_core import Simulation

StrategyRows = tuple[dict[str, Any] | None, list[dict[str, Any]], list[dict[str, Any]]]
TelemetryRows = tuple[dict[str, dict[str, Any]], dict[str, int], dict[str, str]]


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
    router = APIRouter()

    @router.get("/api/sessions/{session_id}/pit-strategy")
    def pit_strategy(session_id: UUID, user=Depends(current_user)):  # noqa: B008
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
        return jsonable(projected)

    return router, pit_strategy
