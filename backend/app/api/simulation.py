from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException

from ..schemas_simulation import SimulationControl


def create_simulation_router(
    mongo_ready: Callable[..., Any],
    get_simulations: Callable[[], Any],
    _start_session_simulation: Callable[..., Any],
    _reset_session_simulation: Callable[..., Any],
    cancel_automatic_pit_reservations: Callable[..., Any],
    admin_steward_dependency: Any,
) -> tuple[APIRouter, Callable[..., Any]]:
    router = APIRouter()

    @router.post("/api/sessions/{session_id}/simulate")
    async def control_simulation(
        session_id: UUID,
        body: SimulationControl,
        user: object = admin_steward_dependency,
    ) -> dict[str, object]:
        if mongo_ready() is None:
            raise HTTPException(503, "MongoDB telemetry store is unavailable")
        sim = get_simulations().get(str(session_id))
        if body.action == "start":
            sim = await _start_session_simulation(session_id, body, sim)
        elif body.action in {"pause", "resume"}:
            expected, next_status, detail = {
                "pause": ("running", "paused", "Simulation is not running"),
                "resume": ("paused", "running", "Simulation is not paused"),
            }[body.action]
            if not sim or sim.status != expected:
                raise HTTPException(409, detail)
            sim.status = next_status
        elif body.action == "stop":
            if not sim:
                raise HTTPException(409, "Simulation has not started")
            sim.status = "stopped"
            if sim.task and not sim.task.done():
                sim.task.cancel()
                await asyncio.gather(sim.task, return_exceptions=True)
            cancel_automatic_pit_reservations(session_id)
            sim.pit_reservations_by_driver.clear()
        elif body.action == "reset":
            sim = await _reset_session_simulation(session_id, body, sim)
        return {
            "session_id": str(session_id),
            "state": sim.status,
            "cars": len(sim.drivers),
            "rate_hz": sim.rate_hz,
        }

    return router, control_simulation
