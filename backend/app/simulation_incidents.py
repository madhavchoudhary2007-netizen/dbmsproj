from __future__ import annotations

from collections.abc import Callable
from typing import Any

from psycopg.rows import dict_row

from .simulation_core import MAX_SESSION_LAPS, Simulation


def record_generated_incidents(
    sim: Simulation,
    packets: list[dict[str, Any]],
    connection: Callable[..., Any],
    publish: Callable[..., Any],
) -> None:
    """Create a few reviewable race reports as laps complete."""
    if not sim.is_generated:
        return
    descriptions = {
        7: "Track limits observed at corner exit",
        23: "Minor wheel-to-wheel contact under review",
        41: "Unsafe rejoin reported by race control",
    }
    for lap, description in descriptions.items():
        if lap >= (sim.total_laps or MAX_SESSION_LAPS) or lap in sim.incident_laps_recorded:
            continue
        finished = [
            packet
            for packet in packets
            if packet["lap"] == lap and packet["sector"] == 3 and packet["lap_time_ms"]
        ]
        if not finished:
            continue
        packet = finished[0]
        with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """INSERT INTO incident_reports(session_id,driver_id,lap,description)
                VALUES (%s,%s,%s,%s) RETURNING *""",
                (sim.session_id, packet["driver_id"], lap, description),
            )
            row = cur.fetchone()
        sim.incident_laps_recorded.add(lap)
        publish(sim.session_id, "incident.update", row)
