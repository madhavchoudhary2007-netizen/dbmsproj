from __future__ import annotations

from collections.abc import Callable
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
