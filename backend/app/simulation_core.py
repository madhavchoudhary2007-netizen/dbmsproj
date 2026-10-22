from __future__ import annotations

from typing import Protocol


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
