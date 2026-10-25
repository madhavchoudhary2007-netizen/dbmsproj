import asyncio
from collections.abc import Callable, Coroutine, MutableMapping
from typing import Any
from uuid import UUID

from fastapi import HTTPException

from .schemas_simulation import SimulationControl
from .simulation_core import MAX_SESSION_LAPS, Simulation


async def start_simulation(
    session_id: UUID,
    body: SimulationControl,
    sim: Simulation | None,
    _require_crud_record: Callable[..., Any],
    fetch_one: Callable[..., Any],
    clear_session_measurements: Callable[..., Any],
    fetch_all: Callable[..., Any],
    restore_simulated_incidents: Callable[..., Any],
    simulations: MutableMapping[str, Simulation],
    simulation_loop: Callable[[Simulation], Coroutine[Any, Any, None]],
) -> Simulation:
    if sim and sim.status in {"running", "paused"}:
        raise HTTPException(409, "Simulation is already running")
    session = _require_crud_record(
        fetch_one(
            "SELECT state,total_laps,scheduled_at FROM race_sessions WHERE id=%s",
            (session_id,),
        ),
        "Session not found",
    )
    if session["state"] != "ACTIVE":
        raise HTTPException(409, "Session must be active before simulation starts")
    if sim and sim.status == "stopped":
        if sim.task and not sim.task.done():
            sim.task.cancel()
            await asyncio.gather(sim.task, return_exceptions=True)
        clear_session_measurements(session_id)
    generated_entries = fetch_all(
        """SELECT d.id,d.number,de.pace_offset_ms,tm.team_id,t.name AS team_name
        FROM demo_race_entries de JOIN drivers d ON d.id=de.driver_id
        JOIN team_memberships tm ON tm.driver_id=d.id
          AND tm.start_date<=%s::date AND (tm.end_date IS NULL OR tm.end_date>=%s::date)
        JOIN teams t ON t.id=tm.team_id WHERE de.session_id=%s ORDER BY d.number""",
        (session["scheduled_at"], session["scheduled_at"], session_id),
    )
    drivers = generated_entries or fetch_all(
        """SELECT d.id,d.number,tm.team_id,t.name AS team_name
        FROM drivers d JOIN team_memberships tm ON tm.driver_id=d.id
          AND tm.start_date<=%s::date AND (tm.end_date IS NULL OR tm.end_date>=%s::date)
        JOIN teams t ON t.id=tm.team_id WHERE d.eligibility='ACTIVE' ORDER BY """
        "d.number LIMIT %s",
        (session["scheduled_at"], session["scheduled_at"], body.cars or 10),
    )
    if not drivers:
        raise HTTPException(409, "No eligible drivers are available")
    if body.cars and len(drivers) < body.cars:
        raise HTTPException(422, "Requested car count exceeds eligible drivers")
    sim = Simulation(
        session_id,
        drivers,
        body.rate_hz or 2.0,
        total_laps=session["total_laps"] or MAX_SESSION_LAPS,
    )
    sim.pace_offsets_ms = {str(d["id"]): d["pace_offset_ms"] for d in generated_entries}
    sim.is_generated = bool(generated_entries)
    marker = fetch_one("SELECT auto_repeat FROM demo_races WHERE session_id=%s", (session_id,))
    sim.auto_repeat = bool(marker and marker["auto_repeat"])
    sim.lap_by_driver = {str(d["id"]): 1 for d in drivers}
    if sim.is_generated:
        restore_simulated_incidents(sim)
    simulations[str(session_id)] = sim
    sim.task = asyncio.create_task(simulation_loop(sim))
    sim.status = "running"
    return sim
