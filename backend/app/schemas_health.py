from typing import Literal, TypedDict

from pydantic import BaseModel


class HealthReport(TypedDict):
    status: Literal["ok", "degraded"]
    services: dict[str, Literal["up", "down"]]


class LivenessReport(BaseModel):
    status: Literal["alive"]


class ReadinessReport(BaseModel):
    status: Literal["ready", "not_ready"]
    services: dict[str, Literal["up", "down"]]
