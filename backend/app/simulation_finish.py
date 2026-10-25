from __future__ import annotations

import asyncio
from collections.abc import Callable, MutableMapping
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from .simulation_core import Simulation


async def finalize_results(
    sim: Simulation,
    ordered: list[dict[str, Any]],
    best_laps: dict[str, int],
    pole_driver_id: str | None,
    fastest_driver_id: str | None,
    championship_id: UUID,
    connection: Callable[..., Any],
    publish: Callable[..., Any],
    cancel_automatic_pit_reservations: Callable[..., Any],
    _make_demo_race: Callable[..., Any],
    launch_demo_simulation: Callable[..., Any],
    simulations: MutableMapping[str, Simulation],
) -> None:
    rows = []
    with connection() as conn, conn.cursor() as cur:
        for position, packet in enumerate(ordered, start=1):
            driver_id = packet["driver_id"]
            best_lap_ms = best_laps.get(driver_id, packet["last_lap_ms"])
            pole = driver_id == pole_driver_id
            fastest_lap = driver_id == fastest_driver_id
            cur.execute(
                "INSERT INTO session_results(session_id,driver_id,position,"
                "lap_time_ms,pole,fastest_lap,"
                "classified) VALUES (%s,%s,%s,%s,%s,%s,TRUE) "
                "ON CONFLICT(session_id,driver_id) "
                "DO UPDATE SET "
                "position=excluded.position,lap_time_ms=excluded.lap_time_ms,"
                "pole=excluded.pole,fastest_lap=excluded.fastest_lap,classified=TRUE",
                (sim.session_id, driver_id, position, best_lap_ms, pole, fastest_lap),
            )
            rows.append(
                {
                    "driver_id": driver_id,
                    "position": position,
                    "lap_time_ms": best_lap_ms,
                    "pole": pole,
                    "fastest_lap": fastest_lap,
                    "classified": True,
                }
            )
        cur.execute(
            (
                "UPDATE race_sessions SET state='COMPLETED',ended_at=%s WHERE id=%s A"
                "ND state='ACTIVE' RETURNING *"
            ),
            (datetime.now(UTC), sim.session_id),
        )
        completed = cur.fetchone()
        if completed:
            cur.execute("SELECT recalculate_standings(%s)", (championship_id,))
    sim.status = "stopped"
    publish(sim.session_id, "timing.update", rows)
    if completed:
        publish(sim.session_id, "session.state", completed)
    sim.runs_completed += 1
    cancel_automatic_pit_reservations(sim.session_id)
    if not sim.auto_repeat or not completed:
        return
    await asyncio.sleep(5)
    race = await asyncio.to_thread(_make_demo_race, None, True)
    launch_demo_simulation(race["session_id"])
    simulations.pop(str(sim.session_id), None)
