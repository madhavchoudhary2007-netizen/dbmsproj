from __future__ import annotations

import random
import secrets
from collections.abc import Callable, MutableMapping
from datetime import UTC, datetime
from typing import Any
from uuid import UUID as UUID
from uuid import uuid4 as uuid4

from fastapi import HTTPException

from .demo_names import generate_demo_names
from .demo_race_repository import DemoRaceSetupError
from .simulation_core import Simulation


def build_demo_race(
    cars: int | None,
    auto_repeat: bool,
    mongo_ready: Callable[[], Any],
    create_demo_race_records: Callable[..., Any],
    simulations: MutableMapping[str, Simulation],
    demo_race_row: Callable[..., Any],
) -> Any:
    if mongo_ready() is None:
        raise HTTPException(503, "MongoDB telemetry store is unavailable")
    seed = secrets.randbits(63)
    rng = random.Random(seed)  # noqa: S311 -- seeded race choices; seed is generated securely
    car_count = cars if cars is not None else rng.randint(8, 16)
    session_id, event_id = uuid4(), uuid4()
    now = datetime.now(UTC)
    names = generate_demo_names(rng, car_count)
    try:
        generated, total_laps = create_demo_race_records(
            session_id, event_id, now, names, auto_repeat, seed=seed
        )
    except DemoRaceSetupError as exc:
        raise HTTPException(409, str(exc)) from exc
    sim = Simulation(session_id, generated, 2.0, total_laps=total_laps, seed=seed)
    sim.auto_repeat = auto_repeat
    sim.is_generated = True
    sim.pace_offsets_ms = {str(d["id"]): d["pace_offset_ms"] for d in generated}
    sim.lap_by_driver = {str(d["id"]): 1 for d in generated}
    sim.elapsed_by_driver = {str(d["id"]): 0 for d in generated}
    simulations[str(session_id)] = sim
    sim.status = "running"
    return demo_race_row(session_id)
