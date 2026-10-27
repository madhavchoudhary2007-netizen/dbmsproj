from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Annotated, Any, cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg.rows import dict_row

from ..core.events import EventBus
from ..core.request_auth import current_user, require_roles
from ..core.request_database import DatabaseRow, DatabaseSession
from ..core.runtime import get_bus
from ..core.serialization import jsonable
from ..core.validation import limit_offset as default_limit_offset
from ..schemas_operations import Decision, IncidentIn
from .laps import get_race_db

router = APIRouter()
stewards_router = router

admin_steward_dependency = Depends(require_roles("ADMIN", "STEWARD"))
authenticated_user_dependency = Depends(current_user)


def _set_penalty_audit_context(cur: Any, user: Any) -> None:
    if not isinstance(user, dict):
        return
    user_id = user.get("id")
    if user_id is not None:
        cur.execute(
            "SELECT set_config('apexgrid.actor', %s, true)",
            (str(user_id),),
        )
    role = user.get("role")
    if isinstance(role, str):
        normalized_role = role.strip().lower()
        if normalized_role in {"admin", "steward"}:
            cur.execute(
                "SELECT set_config('apexgrid.role', %s, true)",
                (normalized_role,),
            )


def _resolve_db(database: DatabaseSession | None = None) -> DatabaseSession:
    if database is not None:
        return database
    import sys

    from .. import database as db_module

    main_module = sys.modules.get("backend.app.main")
    cur_fetch_one = (
        getattr(main_module, "fetch_one", db_module.fetch_one)
        if main_module is not None
        else db_module.fetch_one
    )
    cur_fetch_all = (
        getattr(main_module, "fetch_all", db_module.fetch_all)
        if main_module is not None
        else db_module.fetch_all
    )
    from .laps import _MonkeypatchedDatabaseSession

    return _MonkeypatchedDatabaseSession(cur_fetch_one, cur_fetch_all)


def _get_connection(
    database: DatabaseSession | None = None,
) -> AbstractContextManager[Any]:
    import sys

    from .. import database as db_module

    main_module = sys.modules.get("backend.app.main")
    conn_fn = (
        getattr(main_module, "connection", db_module.connection)
        if main_module is not None
        else db_module.connection
    )
    is_monkeypatched = conn_fn is not db_module.connection
    if (
        not is_monkeypatched
        and database is not None
        and getattr(database, "pool", None) is not None
    ):
        pool = database.pool
        if not pool.closed:
            return cast(AbstractContextManager[Any], pool.connection())
    return cast(AbstractContextManager[Any], conn_fn())


def _resolve_bus(bus: EventBus | None = None) -> EventBus:
    if bus is not None:
        return bus
    import sys

    main_module = sys.modules.get("backend.app.main")
    if main_module is not None and hasattr(main_module, "bus"):
        return cast(EventBus, main_module.bus)

    return EventBus()


def _resolve_publish(
    bus: EventBus | None = None,
) -> Callable[[UUID | str, str, Any], None]:
    import sys

    main_module = sys.modules.get("backend.app.main")
    main_publish = getattr(main_module, "publish", None) if main_module is not None else None
    orig_publish = (
        getattr(main_module, "_default_publish", None) if main_module is not None else None
    )
    if main_publish is not None and (orig_publish is None or main_publish is not orig_publish):
        return cast(Callable[[UUID | str, str, Any], None], main_publish)

    def _publish_event(session_id: UUID | str, kind: str, data: Any) -> None:
        from datetime import UTC, datetime

        b = _resolve_bus(bus)
        b.send(
            session_id,
            {
                "type": kind,
                "ts": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                "session_id": str(session_id),
                "data": jsonable(data),
            },
        )

    return _publish_event


@router.get("/api/incidents", response_model=None)
def get_incidents(
    state: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: Annotated[dict[str, Any] | None, authenticated_user_dependency] = None,
    database: Annotated[DatabaseSession | None, Depends(get_race_db)] = None,
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
    params.extend(default_limit_offset(limit, offset))
    db = _resolve_db(database)
    return cast(list[dict[str, object]], jsonable(db.fetch_all(sql, params)))


@router.post("/api/incidents", status_code=201, response_model=None)
def create_incident(
    body: IncidentIn,
    user: Annotated[dict[str, Any] | None, admin_steward_dependency] = None,
    database: Annotated[DatabaseSession | None, Depends(get_race_db)] = None,
    bus: Annotated[EventBus | None, Depends(get_bus)] = None,
) -> dict[str, object]:
    with _get_connection(database) as conn, conn.cursor(row_factory=dict_row) as cur:
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
                "VALUES (%s,%s,%s,%s) RETURNING *"
            ),
            (body.session_id, body.driver_id, body.lap, body.description),
        )
        row = cur.fetchone()
    result = cast(dict[str, object], jsonable(row))
    publish_fn = _resolve_publish(bus)
    publish_fn(body.session_id, "incident.update", result)
    return result


@router.post("/api/incidents/{incident_id}/decision", response_model=None)
def decide_incident(
    incident_id: UUID,
    body: Decision,
    user: Annotated[dict[str, Any] | None, admin_steward_dependency] = None,
    database: Annotated[DatabaseSession | None, Depends(get_race_db)] = None,
    bus: Annotated[EventBus | None, Depends(get_bus)] = None,
) -> dict[str, object]:
    user_id = user["id"] if user is not None and "id" in user else None
    with _get_connection(database) as conn, conn.cursor(row_factory=dict_row) as cur:
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
            (state, user_id, body.notes, incident_id),
        )
        updated = cur.fetchone()
        penalty = None
        if body.approve and (body.points or body.time_seconds or body.grid_places):
            _set_penalty_audit_context(cur, user)
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
    publish_fn = _resolve_publish(bus)
    publish_fn(incident["session_id"], "incident.update", out)
    return cast(dict[str, object], out)


stewards_handlers: dict[str, Callable[..., Any]] = {
    "get_incidents": get_incidents,
    "create_incident": create_incident,
    "decide_incident": decide_incident,
}


def _register_decide_incident(
    target_router: APIRouter,
    legacy_jsonable: Callable[[Any], Any],
    connection: Callable[..., Any],
    publish: Callable[[UUID | str, str, Any], Any],
    legacy_admin_steward_dependency: Any,
) -> Callable[..., Any]:
    @target_router.post("/api/incidents/{incident_id}/decision", response_model=None)
    def custom_decide_incident(
        incident_id: UUID,
        body: Decision,
        user: dict[str, object] = legacy_admin_steward_dependency,
    ) -> dict[str, object]:
        user_id = user.get("id") if isinstance(user, dict) else None
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
                (state, user_id, body.notes, incident_id),
            )
            updated = cur.fetchone()
            penalty = None
            if body.approve and (body.points or body.time_seconds or body.grid_places):
                _set_penalty_audit_context(cur, user)
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
            "incident": legacy_jsonable(updated),
            "penalty": legacy_jsonable(penalty),
            "driver": legacy_jsonable(driver),
        }
        publish(incident["session_id"], "incident.update", out)
        return cast(dict[str, object], out)

    return custom_decide_incident


def create_stewards_router(
    fetch_all: Callable[..., list[DatabaseRow]],
    legacy_jsonable: Callable[[Any], Any],
    limit_offset_fn: Callable[[int, int], tuple[int, int]],
    legacy_authenticated_user_dependency: Any,
    connection: Callable[..., Any],
    publish: Callable[[UUID | str, str, Any], Any],
    legacy_admin_steward_dependency: Any,
) -> tuple[APIRouter, dict[str, Callable[..., Any]]]:
    rt = APIRouter()

    @rt.get("/api/incidents", response_model=None)
    def legacy_get_incidents(
        state: str | None = None,
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0),
        user: dict[str, object] = legacy_authenticated_user_dependency,
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
        params.extend(limit_offset_fn(limit, offset))
        return cast(list[dict[str, object]], legacy_jsonable(fetch_all(sql, params)))

    @rt.post("/api/incidents", status_code=201, response_model=None)
    def legacy_create_incident(
        body: IncidentIn, user: dict[str, object] = legacy_admin_steward_dependency
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
                    "VALUES (%s,%s,%s,%s) RETURNING *"
                ),
                (body.session_id, body.driver_id, body.lap, body.description),
            )
            row = cur.fetchone()
        result = cast(dict[str, object], legacy_jsonable(row))
        publish(body.session_id, "incident.update", result)
        return result

    legacy_decide_incident = _register_decide_incident(
        rt, legacy_jsonable, connection, publish, legacy_admin_steward_dependency
    )

    return rt, {
        "get_incidents": legacy_get_incidents,
        "create_incident": legacy_create_incident,
        "decide_incident": legacy_decide_incident,
    }


__all__ = [
    "admin_steward_dependency",
    "authenticated_user_dependency",
    "create_incident",
    "create_stewards_router",
    "decide_incident",
    "get_incidents",
    "router",
    "stewards_handlers",
    "stewards_router",
]
