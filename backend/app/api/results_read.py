from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Annotated, Any, cast
from uuid import UUID

from fastapi import APIRouter, Depends
from psycopg import Connection

from ..core.request_auth import current_user, require_roles
from ..core.request_database import DatabaseRow, DatabaseSession
from ..core.serialization import jsonable
from .laps import get_race_db

router = APIRouter()
results_read_router = router

authenticated_user_dependency = Depends(current_user)
admin_steward_dependency = Depends(require_roles("ADMIN", "STEWARD"))

RESULTS_SQL = (
    "SELECT r.*,u.full_name AS driver_name,d.number,t.name AS team_name,\n"
    "      EXISTS(SELECT 1 FROM incident_reports i JOIN penalties p ON p.incident_id=i.id\n"
    "        WHERE i.session_id=r.session_id AND (p.time_seconds>0 OR p.grid_places>0)) "
    "AS provisional\n"
    "      FROM session_results r JOIN race_sessions s ON s.id=r.session_id\n"
    "      JOIN drivers d ON d.id=r.driver_id JOIN users u ON u.id=d.user_id\n"
    "      LEFT JOIN LATERAL (SELECT team_id FROM team_memberships m WHERE m.driver_id=d.id\n"
    "        AND m.start_date<=s.scheduled_at::date AND (m.end_date IS NULL OR "
    "m.end_date>=s.scheduled_at::date)\n"
    "        ORDER BY m.start_date DESC LIMIT 1) membership ON true\n"
    "      LEFT JOIN teams t ON t.id=membership.team_id WHERE r.session_id=%s ORDER BY r.position"
)

STANDINGS_SQL = (
    "SELECT s.*,u.full_name AS driver_name,d.number,t.name AS team_name,\n"
    "      EXISTS(SELECT 1 FROM race_events re JOIN race_sessions rs ON rs.event_id=re.id\n"
    "        JOIN incident_reports i ON i.session_id=rs.id JOIN penalties p ON p.incident_id=i.id\n"
    "        WHERE re.championship_id=s.championship_id AND rs.session_type='RACE'\n"
    "          AND rs.state='COMPLETED' AND (p.time_seconds>0 OR p.grid_places>0)) "
    "AS provisional\n"
    "      FROM driver_standings s JOIN drivers d ON d.id=s.driver_id JOIN users u "
    "ON u.id=d.user_id\n"
    "      LEFT JOIN team_memberships tm ON tm.driver_id=d.id AND tm.end_date IS NULL\n"
    "      LEFT JOIN teams t ON t.id=tm.team_id WHERE s.championship_id=%s ORDER BY s.rank"
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
) -> AbstractContextManager[Connection[DatabaseRow]]:
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
            return cast(AbstractContextManager[Connection[DatabaseRow]], pool.connection())
    return cast(AbstractContextManager[Connection[DatabaseRow]], conn_fn())


@router.get("/api/sessions/{session_id}/results", response_model=None)
def results(
    session_id: UUID,
    user: Annotated[dict[str, Any] | None, authenticated_user_dependency] = None,
    database: Annotated[DatabaseSession | None, Depends(get_race_db)] = None,
) -> list[dict[str, object]]:
    db = _resolve_db(database)
    result = jsonable(db.fetch_all(RESULTS_SQL, (session_id,)))
    return cast(list[dict[str, object]], result)


@router.post("/api/championships/{championship_id}/recalculate", response_model=None)
def recalculate(
    championship_id: UUID,
    user: Annotated[dict[str, Any] | None, admin_steward_dependency] = None,
    database: Annotated[DatabaseSession | None, Depends(get_race_db)] = None,
) -> dict[str, object]:
    with _get_connection(database) as conn, conn.cursor() as cur:
        cur.execute("SELECT recalculate_standings(%s)", (championship_id,))
    return {"championship_id": str(championship_id), "recalculated": True}


@router.get("/api/championships/{championship_id}/standings", response_model=None)
def standings(
    championship_id: UUID,
    user: Annotated[dict[str, Any] | None, authenticated_user_dependency] = None,
    database: Annotated[DatabaseSession | None, Depends(get_race_db)] = None,
) -> list[dict[str, object]]:
    db = _resolve_db(database)
    result = jsonable(db.fetch_all(STANDINGS_SQL, (championship_id,)))
    return cast(list[dict[str, object]], result)


results_read_handlers: dict[str, Callable[..., Any]] = {
    "results": results,
    "standings": standings,
    "recalculate": recalculate,
}


def create_results_read_router(
    fetch_all: Callable[..., list[DatabaseRow]],
    jsonable: Callable[[Any], Any],
    connection: Callable[..., Any],
    authenticated_user_dependency: Any,
    admin_steward_dependency: Any,
) -> tuple[APIRouter, dict[str, Callable[..., Any]]]:
    rt = APIRouter()

    @rt.get("/api/sessions/{session_id}/results", response_model=None)
    def custom_results(
        session_id: UUID, user: dict[str, object] = authenticated_user_dependency
    ) -> list[dict[str, object]]:
        result = jsonable(fetch_all(RESULTS_SQL, (session_id,)))
        return cast(list[dict[str, object]], result)

    @rt.post("/api/championships/{championship_id}/recalculate", response_model=None)
    def custom_recalculate(
        championship_id: UUID, user: dict[str, object] = admin_steward_dependency
    ) -> dict[str, object]:
        with connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT recalculate_standings(%s)", (championship_id,))
        return {"championship_id": str(championship_id), "recalculated": True}

    @rt.get("/api/championships/{championship_id}/standings", response_model=None)
    def custom_standings(
        championship_id: UUID, user: dict[str, object] = authenticated_user_dependency
    ) -> list[dict[str, object]]:
        result = jsonable(fetch_all(STANDINGS_SQL, (championship_id,)))
        return cast(list[dict[str, object]], result)

    return rt, {
        "results": custom_results,
        "standings": custom_standings,
        "recalculate": custom_recalculate,
    }


__all__ = [
    "admin_steward_dependency",
    "authenticated_user_dependency",
    "create_results_read_router",
    "recalculate",
    "results",
    "results_read_handlers",
    "results_read_router",
    "router",
    "standings",
]
