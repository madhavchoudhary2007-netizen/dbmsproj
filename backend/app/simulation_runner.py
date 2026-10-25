from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from datetime import UTC as UTC
from datetime import datetime as datetime
from datetime import tzinfo
from typing import Any

from pymongo.errors import PyMongoError

from .simulation_core import Simulation


async def run_simulation_loop(
    sim: Simulation,
    *,
    _simulation_lease_is_valid: Callable[..., Any],
    mongo_ready: Callable[..., Any],
    fetch_one: Callable[..., Any],
    refresh_simulation_pit_state: Callable[..., Any],
    advance_simulation_tick: Callable[..., Any],
    _persist_simulation_tick: Callable[..., Any],
    _finalize_simulation_results: Callable[..., Any],
    log: logging.Logger,
    MAX_SESSION_LAPS: int,
    datetime: type[datetime],
    UTC: tzinfo,
) -> None:
    if not _simulation_lease_is_valid(sim):
        return
    col = mongo_ready()
    while sim.status in {"running", "paused"}:
        if not _simulation_lease_is_valid(sim):
            return
        if sim.status == "paused":
            await asyncio.sleep(0.05)
            continue
        try:
            session = fetch_one(
                """SELECT s.state,s.safety_car,e.championship_id
                FROM race_sessions s JOIN race_events e ON e.id=s.event_id WHERE s.id=%s""",
                (sim.session_id,),
            )
            if not session or session["state"] != "ACTIVE":
                if session and session["state"] == "PAUSED":
                    sim.status = "paused"
                    continue
                sim.status = "error" if not session else "stopped"
                return
            timestamp = datetime.now(UTC)
            pit_assignments = refresh_simulation_pit_state(sim, timestamp)
            packets, timing = advance_simulation_tick(
                sim, timestamp, safety_car=session["safety_car"], pit_assignments=pit_assignments
            )
            _persist_simulation_tick(col, sim, packets, timing)
            completion_lap = min(sim.total_laps or MAX_SESSION_LAPS, MAX_SESSION_LAPS)
            if all(packet["lap"] == completion_lap and packet["sector"] == 3 for packet in packets):
                ordered = sorted(packets, key=lambda packet: packet["elapsed_ms"])
                best_laps = {
                    row["_id"]: row["best_lap_ms"]
                    for row in col.aggregate(
                        [
                            {
                                "$match": {
                                    "session_id": str(sim.session_id),
                                    "lap_time_ms": {"$gt": 0},
                                }
                            },
                            {
                                "$group": {
                                    "_id": "$driver_id",
                                    "best_lap_ms": {"$min": "$lap_time_ms"},
                                }
                            },
                        ]
                    )
                }
                fastest_driver_id = (
                    min(best_laps, key=lambda driver_id: best_laps[driver_id])
                    if best_laps
                    else None
                )
                pole_driver_id = (
                    min(sim.pace_offsets_ms, key=lambda driver_id: sim.pace_offsets_ms[driver_id])
                    if sim.is_generated and sim.pace_offsets_ms
                    else None
                )
                await _finalize_simulation_results(
                    sim,
                    ordered,
                    best_laps,
                    pole_driver_id,
                    fastest_driver_id,
                    session["championship_id"],
                )
                return
        except PyMongoError:
            sim.status = "error"
            log.exception("Telemetry simulator could not write packet")
            return
        except Exception:
            sim.status = "error"
            log.exception("Telemetry simulator could not advance state")
            return
        await asyncio.sleep(1 / sim.rate_hz)
