from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field


class MembershipIn(BaseModel):
    driver_id: UUID
    team_id: UUID
    start_date: date
    end_date: date | None = None


class MembershipPatch(BaseModel):
    team_id: UUID | None = None
    start_date: date | None = None
    end_date: date | None = None


class ResultIn(BaseModel):
    driver_id: UUID
    position: int = Field(ge=1)
    lap_time_ms: int | None = Field(default=None, ge=0)
    pole: bool = False
    fastest_lap: bool = False
    classified: bool = True
