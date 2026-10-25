import asyncio
from collections.abc import Callable, MutableMapping
from typing import Any
from uuid import UUID

from fastapi import HTTPException

from .schemas_simulation import SimulationControl
from .simulation_core import Simulation


async def reset_simulation(
    session_id: UUID,
    body: SimulationControl,
    sim: Simulation | None,
    fetch_one: Callable[..., Any],
    ensure_session_reset_allowed: Callable[..., Any],
    sync_simulation_lifecycle: Callable[..., Any],
    clear_session_measurements: Callable[..., Any],
    simulations: MutableMapping[str, Simulation],
) -> Simulation:
    session = fetch_one("SELECT state FROM race_sessions WHERE id=%s", (session_id,))
    if not session:
        raise HTTPException(404, "Session not found")
    if session["state"] != "PAUSED":
        raise HTTPException(409, "Pause the session before resetting its simulation")
    ensure_session_reset_allowed(session_id)
    if sim:
        sync_simulation_lifecycle(session_id, "reset")
        if sim.task and not sim.task.done():
            await asyncio.gather(sim.task, return_exceptions=True)
    clear_session_measurements(session_id)
    if not sim:
        sim = Simulation(session_id, [], body.rate_hz or 2.0)
        simulations[str(session_id)] = sim
    return sim
