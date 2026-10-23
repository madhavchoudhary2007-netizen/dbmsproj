from __future__ import annotations

from collections.abc import Callable
from typing import Any
from uuid import UUID

from .simulation_core import Simulation

_NO_AUTO_REASON = (
    "This session has no generated automatic pit strategy; showing recorded stop history."
)
_HISTORY_REASON = "Race is not running; showing recorded stop history."
Driver = dict[str, Any]
DriverMap = dict[str, Driver]
StopsMap = dict[str, list[Driver]]
DRIVER_FIELDS = ("driver_name", "driver_number", "team_id", "team_name")
PIT_TIRE_STINT_LAPS = 18


def tire_stint_target(compound: str, car_number: int) -> int:
    base = {"SOFT": 16, "MEDIUM": 20, "HARD": 24}.get(compound, PIT_TIRE_STINT_LAPS)
    return max(12, min(28, base + int(car_number) % 5 - 2))


def project_pit_strategy(
    session_id: UUID,
    session_state: str,
    session_generated: bool,
    is_live: bool,
    total_laps: Any,
    max_session_laps: int,
    drivers: list[Driver],
    latest_by_driver: DriverMap,
    stops_by_driver: StopsMap,
    sim: Simulation | None,
    tire_stint_target: Callable[[str, int], int],
) -> dict[str, Any]:
    strategy, by_driver, total_stops = [], [], 0
    for driver in drivers:
        did = str(driver["driver_id"])
        packet = latest_by_driver.get(did, {})
        compound = packet.get("tire_compound") or (sim.compound_by_driver.get(did) if sim else None)
        age = packet.get("tire_age_laps", sim.tire_age_by_driver.get(did, 0) if sim else None)
        wear = packet.get("tire_wear_pct", sim.tire_wear_by_driver.get(did) if sim else None)
        current_lap = int(packet.get("lap", sim.lap_by_driver.get(did, 0) if sim else 0) or 0)
        target = (
            sim.pit_due_tire_age_by_driver.get(did)
            if sim and did in sim.pit_due_tire_age_by_driver
            else tire_stint_target(compound, int(driver.get("driver_number") or 1))
            if compound
            else None
        )
        laps_until = max(0, int(target) - int(age or 0)) if target is not None else None
        assigned = sim.pit_reservations_by_driver.get(did) if sim else None
        if not session_generated or not is_live:
            status, reason = (
                ("NO_AUTOMATIC_STRATEGY", _NO_AUTO_REASON)
                if not session_generated
                else ("NO_FUTURE_STOP", _HISTORY_REASON)
            )
            target = laps_until = None
        elif assigned:
            status, reason = "IN_PIT", "A pit box is currently reserved for this driver."
        elif current_lap >= int(total_laps or max_session_laps):
            status, reason = "NO_FUTURE_STOP", "The race has reached its final lap."
        elif target is not None and laps_until is not None and laps_until <= 1:
            status, reason = "PENDING", "The tire stint target is due at the next completed lap."
        else:
            status, reason = "NOT_DUE", "The current tire stint is below its target age."
        completed_lap = (
            current_lap if int(packet.get("sector") or 0) == 3 else max(0, current_lap - 1)
        )
        recommended = (
            completed_lap + (laps_until or 0) if is_live and laps_until is not None else None
        )
        window_start = max(1, recommended - 1) if recommended is not None else None
        assigned_box = (
            {
                key: assigned.get(source)
                for key, source in (
                    ("reservation_id", "id"),
                    ("box_number", "box_number"),
                    ("status", "status"),
                    ("starts_at", "starts_at"),
                    ("ends_at", "ends_at"),
                )
            }
            if assigned
            else None
        )
        driver_stops = stops_by_driver.get(did, [])
        completed_stops = [stop for stop in driver_stops if stop["status"] == "COMPLETED"]
        total_stops += len(completed_stops)
        by_driver.append(
            {
                "driver_id": driver["driver_id"],
                "driver_name": driver.get("driver_name"),
                "team_name": driver.get("team_name"),
                "stop_count": len(completed_stops),
                "laps": [stop["lap"] for stop in completed_stops if stop["lap"] is not None],
            }
        )
        strategy.append(
            {
                "driver_id": driver["driver_id"],
                **{key: driver.get(key) for key in DRIVER_FIELDS},
                "current_lap": current_lap,
                "tire_compound": compound,
                "tire_age_laps": age,
                "tire_wear_pct": wear,
                "pit_window_start_lap": window_start,
                "pit_window_end_lap": recommended,
                "recommended_stop_lap": recommended,
                "laps_until_decision": laps_until,
                "status": status,
                "reason": reason,
                "assigned_box": assigned_box,
                "stops": driver_stops,
            }
        )
    return {
        "session_id": session_id,
        "session_state": session_state,
        "source": "live_simulation" if is_live else "history",
        "strategy": strategy,
        "historical_summary": {"total_stops": total_stops, "by_driver": by_driver},
    }
