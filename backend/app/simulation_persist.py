from collections.abc import Callable
from typing import Any

from pymongo.collection import Collection

from .core.serialization import telemetry_ws_payload
from .simulation_core import Simulation


def persist_tick(
    col: Collection[dict[str, Any]],
    sim: Simulation,
    packets: list[dict[str, Any]],
    timing: dict[str, Any],
    publish: Callable[..., Any],
    schedule_simulation_pit_stops: Callable[..., Any],
    record_simulated_incidents: Callable[..., Any],
) -> None:
    for packet in packets:
        inserted = col.insert_one(dict(packet))
        publish(
            sim.session_id,
            "telemetry.sample",
            telemetry_ws_payload(packet, inserted.inserted_id),
        )
    publish(sim.session_id, "timing.update", timing)
    schedule_simulation_pit_stops(sim, packets)
    record_simulated_incidents(sim, packets)
