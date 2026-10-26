from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MembershipIn(BaseModel):
    driver_id: UUID
    team_id: UUID
    start_date: date
    end_date: date | None = None


class MembershipPatch(BaseModel):
    team_id: UUID | None = None
    start_date: date | None = None
    end_date: date | None = None


class MembershipOut(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: UUID
    driver_id: UUID
    team_id: UUID
    start_date: date | str
    end_date: date | str | None = None
    team_name: str | None = None
    driver_name: str | None = None
    number: int | None = None
    licence_number: str | None = None


class ResultIn(BaseModel):
    driver_id: UUID
    position: int = Field(ge=1)
    lap_time_ms: int | None = Field(default=None, ge=0)
    pole: bool = False
    fastest_lap: bool = False
    classified: bool = True


class ChampionshipIn(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str | None = None
    season: int | None = None


class ChampionshipOut(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: UUID
    name: str
    season: int


class CircuitIn(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str | None = None
    country: str | None = None
    length_km: float | None = None


class CircuitOut(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: UUID
    name: str
    country: str
    length_km: float


class TeamIn(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str | None = None
    principal_user_id: UUID | None = None


class TeamOut(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: UUID
    name: str
    principal_user_id: UUID | None = None
    principal_name: str | None = None


class DriverIn(BaseModel):
    model_config = ConfigDict(extra="allow")

    user_id: UUID | None = None
    licence_number: str | None = None
    number: int | None = None


class DriverOut(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: UUID
    user_id: UUID | None = None
    licence_number: str
    number: int
    eligibility: str | None = "ACTIVE"
    full_name: str | None = None
    email: str | None = None
    team_name: str | None = None


class EventIn(BaseModel):
    model_config = ConfigDict(extra="allow")

    championship_id: UUID | None = None
    circuit_id: UUID | None = None
    round_number: int | None = None
    name: str | None = None
    start_date: datetime | str | None = None


class EventOut(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: UUID
    championship_id: UUID
    circuit_id: UUID
    round_number: int
    name: str
    start_date: datetime | str
    championship_name: str | None = None
    circuit_name: str | None = None
    circuit_country: str | None = None


class SessionIn(BaseModel):
    model_config = ConfigDict(extra="allow")

    event_id: UUID | None = None
    session_type: str | None = None
    scheduled_at: datetime | str | None = None
    total_laps: int | None = None
    safety_car: bool | None = None


class SessionOut(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: UUID
    event_id: UUID
    session_type: str
    state: str = "SCHEDULED"
    scheduled_at: datetime | str
    started_at: datetime | str | None = None
    ended_at: datetime | str | None = None
    total_laps: int = 0
    safety_car: bool = False
    event_name: str | None = None
    circuit_name: str | None = None


__all__ = [
    "ChampionshipIn",
    "ChampionshipOut",
    "CircuitIn",
    "CircuitOut",
    "DriverIn",
    "DriverOut",
    "EventIn",
    "EventOut",
    "MembershipIn",
    "MembershipOut",
    "MembershipPatch",
    "ResultIn",
    "SessionIn",
    "SessionOut",
    "TeamIn",
    "TeamOut",
]
