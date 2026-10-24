from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any

from psycopg.rows import dict_row

from .pit_repository import PIT_RESERVATION_SELECT
from .simulation_core import Simulation


def refresh_pit_state(
    sim: Simulation,
    timestamp: datetime,
    connection: Callable[..., Any],
    publish: Callable[..., Any],
    tire_stint_target: Callable[[str, int], int],
) -> dict[str, Any]:
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """UPDATE pit_reservations SET status='COMPLETED'
            WHERE session_id=%s AND status='RESERVED' AND ends_at<=%s RETURNING id""",
            (sim.session_id, timestamp),
        )
        expired_ids = [row["id"] for row in cur.fetchall()]
        if expired_ids:
            cur.execute(PIT_RESERVATION_SELECT + " WHERE r.id=ANY(%s)", (expired_ids,))
            expired = cur.fetchall()
        else:
            expired = []
        cur.execute(
            PIT_RESERVATION_SELECT
            + """ WHERE r.session_id=%s AND r.driver_id IS NOT NULL
            AND r.status='RESERVED' AND r.ends_at>%s ORDER BY r.starts_at""",
            (sim.session_id, timestamp),
        )
        active = cur.fetchall()
    for reservation in expired:
        publish(sim.session_id, "pit.update", reservation)
        driver_id = reservation.get("driver_id")
        if driver_id and reservation.get("allocation_source") == "AUTOMATIC":
            key = str(driver_id)
            sim.pit_reservations_by_driver.pop(key, None)
            sim.tire_age_by_driver[key] = 0
            sim.tire_wear_by_driver[key] = 0.0
            current = sim.compound_by_driver.get(key)
            base = current or "SOFT"
            compounds = ("SOFT", "MEDIUM", "HARD")
            sim.compound_by_driver[key] = compounds[(compounds.index(base) + 1) % len(compounds)]
            car = next((row for row in sim.drivers if str(row["id"]) == key), {})
            sim.pit_due_tire_age_by_driver[key] = tire_stint_target(
                sim.compound_by_driver[key], int(car.get("number") or 1)
            )
    sim.pit_reservations_by_driver = {str(row["driver_id"]): row for row in active}
    return sim.pit_reservations_by_driver
