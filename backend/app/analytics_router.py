from __future__ import annotations

from collections.abc import Callable
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from .analytics_repository import get_dashboard_data, get_driver_analytics


def create_analytics_router(
    current_user: Callable[..., Any],
    jsonable: Callable[[Any], Any],
) -> APIRouter:
    router = APIRouter()
    current_user_dep = Depends(current_user)

    @router.get("/api/dashboard")
    def dashboard(user=current_user_dep):
        data = get_dashboard_data()
        data["active_session"] = jsonable(data["active_session"])
        return data

    @router.get("/api/analytics/drivers")
    def driver_analytics(
        championship_id: UUID | None = None,
        season: int | None = None,
        circuit_id: UUID | None = None,
        driver_id: UUID | None = None,
        team_id: UUID | None = None,
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0),
        user=current_user_dep,
    ):
        return jsonable(
            get_driver_analytics(
                championship_id, season, circuit_id, driver_id, team_id, limit, offset
            )
        )

    return router
