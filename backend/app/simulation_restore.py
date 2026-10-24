from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable, MutableMapping
from typing import Any

from pymongo import DESCENDING

from .simulation_core import Simulation


def restore_telemetry_state(sim: Simulation, mongo_ready: Callable[[], Any]) -> None:
    """Resume an active generated race without deleting its recorded laps."""
    col = mongo_ready()
    for driver in sim.drivers:
        driver_id = str(driver["id"])
        latest = col.find_one(
            {"session_id": str(sim.session_id), "driver_id": driver_id}, sort=[("ts", DESCENDING)]
        )
        sim.lap_by_driver[driver_id] = int(latest.get("lap", 1)) if latest else 1
        sim.sector_by_driver[driver_id] = int(latest.get("sector", 0)) if latest else 0
        sim.elapsed_by_driver[driver_id] = int(latest.get("elapsed_ms", 0)) if latest else 0
        sim.sector_splits_by_driver[driver_id] = (
            list(latest.get("sector_ms") or []) if latest else []
        )
        sim.next_sector_due_by_driver[driver_id] = sim.elapsed_by_driver[driver_id]
        if latest and latest.get("last_lap_ms"):
            sim.last_lap_by_driver[driver_id] = int(latest["last_lap_ms"])
        sim.tire_age_by_driver[driver_id] = int(latest.get("tire_age_laps", 0)) if latest else 0
        sim.tire_wear_by_driver[driver_id] = (
            float(latest.get("tire_wear_pct", 0)) if latest else 0.0
        )
        if latest and latest.get("tire_compound"):
            sim.compound_by_driver[driver_id] = latest["tire_compound"]
    sim.race_clock_ms = max(sim.elapsed_by_driver.values(), default=0)


def restore_incident_state(sim: Simulation, fetch_all: Callable[..., Any]) -> None:
    """Keep a restarted simulator from duplicating reports already in the archive."""
    sim.incident_laps_recorded = {
        row["lap"]
        for row in fetch_all(
            "SELECT DISTINCT lap FROM incident_reports WHERE session_id=%s", (sim.session_id,)
        )
    }


async def restore_or_create_demo(
    create_if_missing: bool,
    fetch_all: Callable[..., Any],
    log: logging.Logger,
    restore_simulation_from_telemetry: Callable[[Simulation], Any],
    restore_simulated_incidents: Callable[[Simulation], Any],
    launch_demo_simulation: Callable[..., Any],
    _make_demo_race: Callable[..., Any],
    simulations: MutableMapping[str, Simulation],
) -> None:
    active_races = fetch_all(
        "SELECT s.id,s.total_laps,d.auto_repeat,d.simulation_seed FROM race_sessions s JOIN d"
        "emo_races d ON d.session_id=s.id WHERE s.state='ACTIVE' ORDER BY d.created_at"
    )
    for active in active_races:
        session_id = active["id"]
        entries = fetch_all(
            """SELECT d.id,d.number,de.pace_offset_ms,tm.team_id,t.name AS team_name
            FROM demo_race_entries de JOIN drivers d ON d.id=de.driver_id
            JOIN race_sessions s ON s.id=de.session_id
            JOIN team_memberships tm ON tm.driver_id=d.id AND tm.start_date<=s.scheduled_at::date
              AND (tm.end_date IS NULL OR tm.end_date>=s.scheduled_at::date)
            JOIN teams t ON t.id=tm.team_id WHERE de.session_id=%s ORDER BY d.number""",
            (session_id,),
        )
        if not entries:
            log.error("Active generated race %s has no entries", session_id)
            continue
        sim = Simulation(
            session_id,
            entries,
            2.0,
            total_laps=active["total_laps"],
            seed=active.get("simulation_seed"),
        )
        sim.pace_offsets_ms = {str(d["id"]): d["pace_offset_ms"] for d in entries}
        restore_simulation_from_telemetry(sim)
        sim.auto_repeat = active["auto_repeat"]
        sim.is_generated = True
        restore_simulated_incidents(sim)
        sim.status = "running"
        simulations[str(session_id)] = sim
        launch_demo_simulation(session_id)
    if any(race["auto_repeat"] for race in active_races) or not create_if_missing:
        return

    race = await asyncio.to_thread(_make_demo_race, None, True)
    launch_demo_simulation(race["session_id"])
