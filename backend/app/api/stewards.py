from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Any, cast
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from psycopg import Connection
from psycopg.rows import dict_row

from ..database import DatabaseRow
from ..schemas_operations import Decision, IncidentIn


def _register_decide_incident(
    router: APIRouter,
    jsonable: Callable[[Any], Any],
    connection: Callable[[], AbstractContextManager[Connection[DatabaseRow]]],
    publish: Callable[[UUID | str, str, Any], Any],
    admin_steward_dependency: Any,
) -> Callable[..., Any]:
    @router.post("/api/incidents/{incident_id}/decision", response_model=None)
    def decide_incident(
        incident_id: UUID,
        body: Decision,
        user: dict[str, object] = admin_steward_dependency,
    ) -> dict[str, object]:
        with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM incident_reports WHERE id=%s FOR UPDATE", (incident_id,))
            incident = cur.fetchone()
            if not incident:
                raise HTTPException(404, "Incident not found")
            if incident["state"] != "OPEN":
                raise HTTPException(409, "Incident has already been decided")
            state = "APPROVED" if body.approve else "REJECTED"
            cur.execute(
                (
                    "UPDATE incident_reports SET state=%s,decided_by=%s,decision_notes=%s "
                    "WHERE id=%s RETURNING *"
                ),
                (state, user["id"], body.notes, incident_id),
            )
            updated = cur.fetchone()
            penalty = None
            if body.approve and (body.points or body.time_seconds or body.grid_places):
                cur.execute(
                    (
                        "INSERT INTO penalties(incident_id,driver_id,points,time_seconds,"
                        "grid_places)"
                        " VALUES (%s,%s,%s,%s,%s) RETURNING *"
                    ),
                    (
                        incident_id,
                        incident["driver_id"],
                        body.points,
                        body.time_seconds,
                        body.grid_places,
                    ),
                )
                penalty = cur.fetchone()
            cur.execute(
                (
                    "SELECT d.eligibility,COALESCE((SELECT pp.points FROM penalty_points pp JOIN "
                    "championships c ON c.season=pp.season JOIN race_events e ON "
                    "e.championship_id=c.id JOIN race_sessions s ON s.event_id=e.id WHERE "
                    "s.id=%s AND pp.driver_id=d.id LIMIT 1),0) AS season_points FROM drivers "
                    "d WHERE d.id=%s"
                ),
                (incident["session_id"], incident["driver_id"]),
            )
            driver = cur.fetchone()
        out = {
            "incident": jsonable(updated),
            "penalty": jsonable(penalty),
            "driver": jsonable(driver),
        }
        publish(incident["session_id"], "incident.update", out)
        return cast(dict[str, object], out)

    return decide_incident


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

    @router.get("/api/incidents", response_model=None)
    def get_incidents(
        state: str | None = None,
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0),
        user: dict[str, object] = authenticated_user_dependency,
    ) -> list[dict[str, object]]:
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
        return cast(list[dict[str, object]], jsonable(fetch_all(sql, params)))

    @router.post("/api/incidents", status_code=201, response_model=None)
    def create_incident(
        body: IncidentIn, user: dict[str, object] = admin_steward_dependency
    ) -> dict[str, object]:
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
        result = cast(dict[str, object], jsonable(row))
        publish(body.session_id, "incident.update", result)
        return result

    decide_incident = _register_decide_incident(
        router, jsonable, connection, publish, admin_steward_dependency
    )

    return router, {
        "get_incidents": get_incidents,
        "create_incident": create_incident,
        "decide_incident": decide_incident,
    }
