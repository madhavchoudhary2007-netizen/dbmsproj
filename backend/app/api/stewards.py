from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from ..database import DatabaseRow


def create_stewards_router(
    fetch_all: Callable[..., list[DatabaseRow]],
    jsonable: Callable[[Any], Any],
    limit_offset: Callable[[int, int], tuple[int, int]],
    authenticated_user_dependency: Any,
) -> tuple[APIRouter, dict[str, Callable[..., Any]]]:
    router = APIRouter()

    @router.get("/api/incidents")
    def get_incidents(
        state: str | None = None,
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0),
        user=authenticated_user_dependency,
    ):
        sql = (
            "SELECT i.*,u.full_name AS driver_name,d.number,s.session_type,e.name AS event_name"
            " FROM incident_reports i JOIN drivers d ON d.id=i.driver_id JOIN users u ON u.id=d"
            ".user_id JOIN race_sessions s ON s.id=i.session_id JOIN race_events e"
            " ON e.id=s.event_id"
        )
        params: list[Any] = []
        if state:
            if state not in {"OPEN", "APPROVED", "REJECTED"}:
                raise HTTPException(422, "Invalid incident state")
            sql += " WHERE i.state=%s"
            params.append(state)
        sql += " ORDER BY i.reported_at DESC LIMIT %s OFFSET %s"
        params.extend(limit_offset(limit, offset))
        return jsonable(fetch_all(sql, params))

    return router, {"get_incidents": get_incidents}
