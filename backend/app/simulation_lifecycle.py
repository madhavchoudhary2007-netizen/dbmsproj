from __future__ import annotations

from collections.abc import MutableMapping
from uuid import UUID

from .simulation_core import Simulation


def sync_lifecycle(
    session_id: UUID,
    action: str,
    simulations: MutableMapping[str, Simulation],
) -> None:
    sim = simulations.get(str(session_id))
    if not sim:
        return
    if action == "pause" and sim.status == "running":
        sim.status = "paused"
    elif action == "resume" and sim.status == "paused":
        sim.status = "running"
    elif action in {"finish", "reset"}:
        sim.status = "stopped"
        if sim.task and not sim.task.done():
            sim.task.get_loop().call_soon_threadsafe(sim.task.cancel)
        if action == "reset":
            sim.lap_by_driver = {str(driver["id"]): 1 for driver in sim.drivers}
            sim.sector_by_driver.clear()
            sim.race_clock_ms = 0
            sim.next_sector_due_by_driver.clear()
            sim.last_lap_by_driver.clear()
            sim.elapsed_by_driver = {str(driver["id"]): 0 for driver in sim.drivers}
            sim.sector_splits_by_driver.clear()
            sim.tire_age_by_driver = {str(driver["id"]): 0 for driver in sim.drivers}
            sim.tire_wear_by_driver = {str(driver["id"]): 0.0 for driver in sim.drivers}
            sim.compound_by_driver.clear()
            sim.pit_reservations_by_driver.clear()
            sim.pit_due_tire_age_by_driver.clear()
