from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from .simulation_core import MAX_SESSION_LAPS


class Telemetry(BaseModel):
    session_id: UUID
    driver_id: UUID
    ts: datetime
    lap: int = Field(ge=0, le=MAX_SESSION_LAPS)
    sector: int = Field(ge=0)
    elapsed_ms: int = Field(ge=0)
    lap_time_ms: int | None = Field(default=None, ge=0)
    last_lap_ms: int | None = Field(default=None, ge=0)
    sector_ms: list[int] = Field(default_factory=list)
    position: int | None = Field(default=None, ge=1)
    speed_kph: float = Field(ge=0)
    throttle_pct: float = Field(ge=0, le=100)
    brake_pct: float = Field(ge=0, le=100)
    tire_compound: Literal["SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"]
    tire_age_laps: int = Field(ge=0)
    tire_wear_pct: float = Field(ge=0, le=100)
    tire_temp_c: list[float] = Field(min_length=1, max_length=8)
    pit_state: str = Field(max_length=40)
    pit_reservation_id: UUID | None = None
    pit_box_number: int | None = Field(default=None, ge=1)
    pit_team_id: UUID | None = None
    pit_starts_at: datetime | None = None
    pit_ends_at: datetime | None = None

    @field_validator("ts")
    @classmethod
    def utc_timestamp(cls, value):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Timestamp must include a UTC offset")
        return value.astimezone(timezone.utc)

    @field_validator("pit_starts_at", "pit_ends_at")
    @classmethod
    def utc_pit_timestamp(cls, value):
        if value is None:
            return value
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Pit timestamps must include a UTC offset")
        return value.astimezone(timezone.utc)
