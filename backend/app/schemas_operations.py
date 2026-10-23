from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator

from .simulation_core import MAX_SESSION_LAPS


class Action(BaseModel):
    action: Literal["start", "pause", "resume", "finish", "reset"]


class IncidentIn(BaseModel):
    session_id: UUID
    driver_id: UUID
    lap: int = Field(ge=1, le=MAX_SESSION_LAPS)
    description: str = Field(min_length=3, max_length=2000)


class Decision(BaseModel):
    approve: bool
    notes: str | None = Field(default=None, max_length=2000)
    points: int = Field(default=0, ge=0, le=12)
    time_seconds: int = Field(default=0, ge=0)
    grid_places: int = Field(default=0, ge=0)

    @field_validator("time_seconds", "grid_places")
    @classmethod
    def reject_unsupported_sanctions(cls, value: int, info: ValidationInfo) -> int:
        if value > 0:
            raise ValueError(
                f"Unsupported {info.field_name} sanction. Use penalty points and notes "
                "until official timing and grid enforcement exists."
            )
        return value


class ReservationIn(BaseModel):
    pit_box_id: UUID
    session_id: UUID
    team_id: UUID
    starts_at: datetime
    ends_at: datetime

    @field_validator("starts_at", "ends_at")
    @classmethod
    def utc_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Timestamps must include a UTC offset")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def ordered(self) -> ReservationIn:
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be after starts_at")
        return self


class AutoReservationIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: UUID
    team_id: UUID
    driver_id: UUID | None = None
