from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from psycopg.rows import dict_row

from .pit_repository import PIT_RESERVATION_SELECT
from .simulation_core import MAX_SESSION_LAPS, Simulation


def cancel_automatic_reservations(
    session_id: UUID | str,
    connection: Callable[..., Any],
    publish: Callable[..., Any],
) -> None:
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            (
                "UPDATE pit_reservations SET status='CANCELLED'\n            WHERE session_id=%s "
                "AND allocation_source='AUTOMATIC' AND status='RESERVED' RETURNING id"
            ),
            (session_id,),
        )
        ids = [row["id"] for row in cur.fetchall()]
        if ids:
            cur.execute(PIT_RESERVATION_SELECT + " WHERE r.id=ANY(%s)", (ids,))
            rows = cur.fetchall()
        else:
            rows = []
    for row in rows:
        publish(session_id, "pit.update", row)


def schedule_pit_stops(
    sim: Simulation,
    packets: list[dict[str, Any]],
    tire_stint_target: Callable[[str, int], int],
    create_automatic_reservation: Callable[..., Any],
    publish: Callable[..., Any],
    log: logging.Logger,
) -> None:
    completion_lap = min(sim.total_laps or MAX_SESSION_LAPS, MAX_SESSION_LAPS)
    for packet in packets:
        driver_id = str(packet["driver_id"])
        driver = next((row for row in sim.drivers if str(row["id"]) == driver_id), None)
        number = int((driver or {}).get("number") or 1)
        compound = sim.compound_by_driver.setdefault(
            driver_id, ("SOFT", "MEDIUM", "HARD")[number % 3]
        )
        target_age = sim.pit_due_tire_age_by_driver.setdefault(
            driver_id, tire_stint_target(compound, number)
        )
        if (
            packet["sector"] != 3
            or packet["lap"] >= completion_lap
            or packet["tire_age_laps"] < target_age
            or driver_id in sim.pit_reservations_by_driver
        ):
            continue
        if not driver or not driver.get("team_id"):
            sim.pit_due_tire_age_by_driver[driver_id] = MAX_SESSION_LAPS + 1
            continue
        duration = timedelta(seconds=max(0.6, 3.0 / max(sim.rate_hz, 0.2)))
        try:
            reservation = create_automatic_reservation(
                sim.session_id, driver["team_id"], driver["id"], duration
            )
        except Exception as exc:
            log.warning("Automatic pit stop allocation failed for %s: %s", driver_id, exc)
            sim.pit_due_tire_age_by_driver[driver_id] = MAX_SESSION_LAPS + 1
            continue
        sim.pit_reservations_by_driver[driver_id] = reservation
        sim.pit_due_tire_age_by_driver[driver_id] = tire_stint_target(compound, number)
        publish(sim.session_id, "pit.update", reservation)


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
