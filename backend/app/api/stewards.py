from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from psycopg import Connection
from psycopg.rows import dict_row

from ..database import DatabaseRow
from ..schemas_operations import IncidentIn


def create_stewards_router(
    fetch_all: Callable[..., list[DatabaseRow]],
    jsonable: Callable[[Any], Any],
    limit_offset: Callable[[int, int], tuple[int, int]],
    authenticated_user_dependency: Any,
    connection: Callable[[], AbstractContextManager[Connection[DatabaseRow]]],
    publish: Callable[[UUID | str, str, Any], Any],
    admin_steward_dependency: Any,
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

    @router.post("/api/incidents", status_code=201)
    def create_incident(body: IncidentIn, user=admin_steward_dependency):
        with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT total_laps FROM race_sessions WHERE id=%s", (body.session_id,))
            session = cur.fetchone()
            if not session:
                raise HTTPException(404, "Session not found")
            if session["total_laps"] and body.lap > session["total_laps"]:
                raise HTTPException(422, "Incident lap exceeds the session lap count")
            cur.execute("SELECT 1 FROM demo_races WHERE session_id=%s", (body.session_id,))
            if cur.fetchone():
                cur.execute(
                    "SELECT 1 FROM demo_race_entries WHERE session_id=%s AND driver_id=%s",
                    (body.session_id, body.driver_id),
                )
                if not cur.fetchone():
                    raise HTTPException(422, "Driver is not entered in this generated race")
            cur.execute(
                (
                    "INSERT INTO incident_reports(session_id,driver_id,lap,description) "
                    "VALUES (%s,%s"
                    ",%s,%s) RETURNING *"
                ),
                (body.session_id, body.driver_id, body.lap, body.description),
            )
            row = cur.fetchone()
        result = jsonable(row)
        publish(body.session_id, "incident.update", result)
        return result

    return router, {"get_incidents": get_incidents, "create_incident": create_incident}
