from typing import Literal

from pydantic import BaseModel, Field


class DemoRaceCreate(BaseModel):
    cars: int | None = Field(default=None, ge=6, le=20)


class SimulationControl(BaseModel):
    action: Literal["start", "pause", "resume", "stop", "reset"]
    cars: int | None = Field(default=None, ge=1, le=20)
    rate_hz: float | None = Field(default=None, ge=0.2, le=20)
