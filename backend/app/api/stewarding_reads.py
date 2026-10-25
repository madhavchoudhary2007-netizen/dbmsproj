from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from ..core.request_auth import current_user
from ..core.request_database import DatabaseSession, get_database

router = APIRouter(prefix="/api/stewarding", tags=["stewarding"])


class PenaltyRead(BaseModel):
    id: UUID
    incident_id: UUID
    driver_id: UUID
    driver_name: str | None
    session_id: UUID
    lap: int
    points: int
    time_seconds: int
    grid_places: int
    created_at: datetime


class LicenceRead(BaseModel):
    driver_id: UUID
    driver_name: str | None
    licence_number: str
    eligibility: str
    season: int
    points: int


@router.get("/penalties", response_model=list[PenaltyRead])
def read_penalties(
    database: Annotated[DatabaseSession, Depends(get_database)],
    user: Annotated[dict[str, object], Depends(current_user)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[PenaltyRead]:
    rows = database.fetch_all(
        """SELECT p.id, p.incident_id, p.driver_id, u.full_name AS driver_name,
                  i.session_id, i.lap, p.points, p.time_seconds, p.grid_places, p.created_at
           FROM penalties p
           JOIN incident_reports i ON i.id = p.incident_id
           JOIN drivers d ON d.id = p.driver_id
           LEFT JOIN users u ON u.id = d.user_id
           ORDER BY p.created_at DESC, p.id DESC LIMIT %s OFFSET %s""",
        (limit, offset),
    )
    return [PenaltyRead.model_validate(row) for row in rows]


@router.get("/licences", response_model=list[LicenceRead])
def read_licences(
    database: Annotated[DatabaseSession, Depends(get_database)],
    user: Annotated[dict[str, object], Depends(current_user)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    season: Annotated[int | None, Query(ge=1, le=9999)] = None,
) -> list[LicenceRead]:
    selected_season = season if season is not None else datetime.now(UTC).year
    rows = database.fetch_all(
        """SELECT d.id AS driver_id, u.full_name AS driver_name, d.licence_number,
                  d.eligibility, %s AS season, COALESCE(pp.points, 0) AS points
           FROM drivers d
           LEFT JOIN users u ON u.id = d.user_id
           LEFT JOIN penalty_points pp ON pp.driver_id = d.id AND pp.season = %s
           ORDER BY d.id ASC LIMIT %s OFFSET %s""",
        (selected_season, selected_season, limit, offset),
    )
    return [LicenceRead.model_validate(row) for row in rows]
