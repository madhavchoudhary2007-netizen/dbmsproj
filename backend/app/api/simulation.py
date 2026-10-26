from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Annotated, Any, cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from ..core.request_auth import require_roles
from ..core.runtime import get_simulations
from ..schemas_simulation import SimulationControl
from ..simulation_core import Simulation

router = APIRouter()
simulation_router = router

admin_steward_dependency = Depends(require_roles("ADMIN", "STEWARD"))


def _resolve_simulations(
    simulations: dict[str, Simulation] | None = None,
) -> dict[str, Simulation]:
    if simulations is not None:
        return simulations
    import sys

    main_module = sys.modules.get("backend.app.main")
    if main_module is not None and hasattr(main_module, "simulations"):
        return cast(dict[str, Simulation], main_module.simulations)
    return {}


def _resolve_mongo_ready() -> None:
    import sys

    main_module = sys.modules.get("backend.app.main")
    if main_module is not None:
        m_mongo_ready = getattr(main_module, "mongo_ready", None)
        if m_mongo_ready is not None:
            res = m_mongo_ready()
            if res is None:
                raise HTTPException(503, "MongoDB telemetry store is unavailable")
            return
    raise HTTPException(503, "MongoDB telemetry store is unavailable")


def _resolve_start_simulation() -> Callable[..., Any]:
    import sys

    main_module = sys.modules.get("backend.app.main")
    if main_module is not None and hasattr(main_module, "_start_session_simulation"):
        return cast(Callable[..., Any], main_module._start_session_simulation)
    from ..simulation_start import start_simulation

    return cast(Callable[..., Any], start_simulation)


def _resolve_reset_simulation() -> Callable[..., Any]:
    import sys

    main_module = sys.modules.get("backend.app.main")
    if main_module is not None and hasattr(main_module, "_reset_session_simulation"):
        return cast(Callable[..., Any], main_module._reset_session_simulation)
    from ..simulation_reset import reset_simulation

    return cast(Callable[..., Any], reset_simulation)


def _resolve_cancel_automatic_pit_reservations() -> Callable[[UUID | str], None]:
    import sys

    main_module = sys.modules.get("backend.app.main")
    if main_module is not None and hasattr(main_module, "cancel_automatic_pit_reservations"):
        return cast(Callable[[UUID | str], None], main_module.cancel_automatic_pit_reservations)
    return lambda _sid: None


@router.post("/api/sessions/{session_id}/simulate")
async def control_simulation(
    session_id: UUID,
    body: SimulationControl,
    user: Annotated[dict[str, Any] | None, admin_steward_dependency] = None,
    simulations: Annotated[dict[str, Simulation] | None, Depends(get_simulations)] = None,
) -> dict[str, object]:
    _resolve_mongo_ready()
    sims = _resolve_simulations(simulations)
    sim = sims.get(str(session_id))
    if body.action == "start":
        start_fn = _resolve_start_simulation()
        sim = await start_fn(session_id, body, sim)
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
        cancel_pit = _resolve_cancel_automatic_pit_reservations()
        cancel_pit(session_id)
        sim.pit_reservations_by_driver.clear()
    elif body.action == "reset":
        reset_fn = _resolve_reset_simulation()
        sim = await reset_fn(session_id, body, sim)
    if sim is None:
        raise HTTPException(500, "Simulation failed to transition state")
    return {
        "session_id": str(session_id),
        "state": sim.status,
        "cars": len(sim.drivers),
        "rate_hz": sim.rate_hz,
    }


def create_simulation_router(  # noqa: C901
    mongo_ready: Callable[..., Any],
    get_simulations: Callable[[], Any],
    _start_session_simulation: Callable[..., Any],
    _reset_session_simulation: Callable[..., Any],
    cancel_automatic_pit_reservations: Callable[..., Any],
    admin_steward_dependency: Any,
) -> tuple[APIRouter, Callable[..., Any]]:
    legacy_router = APIRouter()

    @legacy_router.post("/api/sessions/{session_id}/simulate")
    async def control_simulation(  # noqa: C901
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
        if sim is None:
            raise HTTPException(500, "Simulation failed to transition state")
        return {
            "session_id": str(session_id),
            "state": sim.status,
            "cars": len(sim.drivers),
            "rate_hz": sim.rate_hz,
        }

    return legacy_router, control_simulation
