from __future__ import annotations

from typing import Annotated, Any, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from .analytics_repository import get_dashboard_data, get_driver_analytics
from .core.request_auth import current_user
from .core.request_database import DatabaseSession, get_database
from .core.serialization import jsonable

router = APIRouter()


@router.get("/api/dashboard", response_model=None)
def dashboard(
    user: Annotated[dict[str, Any], Depends(current_user)],
    database: Annotated[DatabaseSession, Depends(get_database)],
) -> dict[str, Any]:
    data = get_dashboard_data(database)
    data["active_session"] = jsonable(data["active_session"])
    return data


@router.get("/api/analytics/drivers", response_model=None)
def driver_analytics(
    user: Annotated[dict[str, Any], Depends(current_user)],
    database: Annotated[DatabaseSession, Depends(get_database)],
    championship_id: UUID | None = None,
    season: int | None = None,
    circuit_id: UUID | None = None,
    driver_id: UUID | None = None,
    team_id: UUID | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[dict[str, Any]]:
    return cast(
        list[dict[str, Any]],
        jsonable(
            get_driver_analytics(
                championship_id,
                season,
                circuit_id,
                driver_id,
                team_id,
                limit,
                offset,
                database,
            )
        ),
    )
