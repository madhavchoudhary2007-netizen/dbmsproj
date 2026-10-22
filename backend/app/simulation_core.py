from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Protocol
from uuid import UUID

MAX_SESSION_LAPS = 72


@dataclass
class Simulation:
    session_id: UUID
    drivers: list[dict[str, object]]
    rate_hz: float
    task: asyncio.Task[None] | None = None
    status: str = "stopped"
    lap_by_driver: dict[str, int] = field(default_factory=dict)
    sector_by_driver: dict[str, int] = field(default_factory=dict)
    race_clock_ms: int = 0
    next_sector_due_by_driver: dict[str, int] = field(default_factory=dict)
    last_lap_by_driver: dict[str, int] = field(default_factory=dict)
    elapsed_by_driver: dict[str, int] = field(default_factory=dict)
    sector_splits_by_driver: dict[str, list[int]] = field(default_factory=dict)
    tire_age_by_driver: dict[str, int] = field(default_factory=dict)
    tire_wear_by_driver: dict[str, float] = field(default_factory=dict)
    compound_by_driver: dict[str, str] = field(default_factory=dict)
    pace_offsets_ms: dict[str, int] = field(default_factory=dict)
    total_laps: int | None = None
    auto_repeat: bool = False
    runs_completed: int = 0
    is_generated: bool = False
    incident_laps_recorded: set[int] = field(default_factory=set)
    pit_reservations_by_driver: dict[str, dict[str, object]] = field(default_factory=dict)
    pit_due_tire_age_by_driver: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.total_laps is not None:
            self.total_laps = min(max(int(self.total_laps), 0), MAX_SESSION_LAPS)


class SimulationRandom(Protocol):
    def gauss(self, mu: float, sigma: float) -> float: ...

    def uniform(self, a: float, b: float) -> float: ...


def calculate_sector_performance(
    sector: int,
    pace_offset_ms: int,
    safety_car: bool,
    in_pit: bool,
    rng: SimulationRandom,
) -> tuple[int, float, float, float]:
    """Calculate sector duration and telemetry controls using the supplied RNG."""
    base_sector_ms = (28600, 30200, 27800)[sector - 1] + int(pace_offset_ms / 3)
    jitter_limit = base_sector_ms * 0.025
    sector_ms = int(
        max(
            base_sector_ms - jitter_limit,
            min(
                base_sector_ms + jitter_limit,
                rng.gauss(base_sector_ms, base_sector_ms * 0.009),
            ),
        )
    )
    if safety_car:
        sector_ms = int(sector_ms * 1.18)
        throttle = rng.uniform(28, 58)
        brake = rng.uniform(14, 38)
        speed = 95 + throttle * 0.75 - brake * 0.45
    elif in_pit:
        sector_ms = int(sector_ms * 1.3)
        throttle = rng.uniform(18, 42)
        brake = rng.uniform(12, 38)
        speed = 58 + throttle * 0.7 - brake * 0.35
    else:
        throttle = rng.uniform(42, 100)
        brake = rng.uniform(0, 34)
        speed = 105 + throttle * 1.9 - brake * 1.15
    speed = round(max(35, min(330, speed + rng.uniform(-7, 7))), 1)
    return sector_ms, throttle, brake, speed
