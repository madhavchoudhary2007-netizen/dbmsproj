from __future__ import annotations

from collections.abc import Callable, Mapping
from contextlib import AbstractContextManager
from typing import Annotated, Any, cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from psycopg.rows import dict_row

from ..core.events import EventBus
from ..core.request_auth import require_roles
from ..core.request_database import DatabaseRow, DatabaseSession
from ..core.runtime import get_bus, get_simulations
from ..core.serialization import jsonable
from ..schemas_competition import ResultIn
from ..simulation_core import Simulation
from .laps import get_race_db

router = APIRouter()
results_write_router = router

admin_steward_dependency = Depends(require_roles("ADMIN", "STEWARD"))


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


def _resolve_simulations(
    simulations: dict[str, Simulation] | None = None,
) -> dict[str, Simulation]:
    if simulations is not None:
        return simulations
    import sys

    main_module = sys.modules.get("backend.app.main")
    if main_module is not None and hasattr(main_module, "simulations"):
        return cast(dict[str, Simulation], main_module.simulations)
    return {}


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


def _save_results(
    session_id: UUID,
    rows: list[ResultIn],
    user: Any,
    fetch_one: Callable[..., DatabaseRow | None],
    connection: Callable[..., Any],
    simulations: Mapping[str, Any],
    publish: Callable[..., Any],
    jsonable: Callable[[Any], Any],
) -> Any:
    if len(rows) > 100:
        raise HTTPException(422, "At most 100 results per request")
    session = fetch_one(
        """SELECT s.state,EXISTS(SELECT 1 FROM demo_races d WHERE d.session_id=s.id) AS generated
        FROM race_sessions s WHERE s.id=%s""",
        (session_id,),
    )
    if not session:
        raise HTTPException(404, "Session not found")
    if session["state"] not in {"ACTIVE", "PAUSED", "COMPLETED"}:
        raise HTTPException(409, "Results cannot be recorded for a scheduled or cancelled session")
    sim = simulations.get(str(session_id))
    if session["generated"] and session["state"] == "ACTIVE" and sim and sim.status == "running":
        raise HTTPException(409, "The active demo simulator owns this session's results")
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        for r in rows:
            cur.execute(
                (
                    "INSERT INTO session_results(session_id,driver_id,position,lap_time_ms,pole,f"
                    "astest_lap,classified) VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(session_id,"
                    "driver_id) DO UPDATE SET position=excluded.position,lap_time_ms=excluded.lap"
                    "_time_ms,pole=excluded.pole,fastest_lap=excluded.fastest_lap,classified=excl"
                    "uded.classified"
                ),
                (
                    session_id,
                    r.driver_id,
                    r.position,
                    r.lap_time_ms,
                    r.pole,
                    r.fastest_lap,
                    r.classified,
                ),
            )
        cur.execute(
            (
                "SELECT r.*,u.full_name AS driver_name FROM session_results r JOIN drivers d ON d"
                ".id=r.driver_id JOIN users u ON u.id=d.user_id WHERE r.session_id=%s ORDER BY r."
                "position"
            ),
            (session_id,),
        )
        result = cur.fetchall()
        if session["state"] == "COMPLETED":
            classified_positions = [r["position"] for r in result if r["classified"]]
            if any(position is None for position in classified_positions) or sorted(
                classified_positions
            ) != list(range(1, len(classified_positions) + 1)):
                raise HTTPException(
                    422, "Classified result positions must be contiguous starting at 1"
                )
    publish(session_id, "timing.update", jsonable(result))
    return jsonable(result)


@router.post("/api/sessions/{session_id}/results", response_model=None)
def save_results(
    session_id: UUID,
    rows: list[ResultIn],
    user: Annotated[dict[str, Any] | None, admin_steward_dependency] = None,
    database: Annotated[DatabaseSession | None, Depends(get_race_db)] = None,
    simulations: Annotated[dict[str, Simulation] | None, Depends(get_simulations)] = None,
    bus: Annotated[EventBus | None, Depends(get_bus)] = None,
) -> list[dict[str, object]]:
    db = _resolve_db(database)
    sims = _resolve_simulations(simulations)
    pub = _resolve_publish(bus)
    return cast(
        list[dict[str, object]],
        _save_results(
            session_id,
            rows,
            user,
            db.fetch_one,
            lambda: _get_connection(database),
            sims,
            pub,
            jsonable,
        ),
    )


results_write_handlers: dict[str, Callable[..., Any]] = {
    "save_results": save_results,
}


def create_results_write_router(
    fetch_one: Callable[..., DatabaseRow | None],
    connection: Callable[..., Any],
    simulations_provider: Callable[[], Mapping[str, Any]],
    publish: Callable[[UUID, str, Any], Any],
    jsonable: Callable[[Any], Any],
    admin_steward_dependency: Any,
) -> tuple[APIRouter, dict[str, Callable[..., Any]]]:
    rt = APIRouter()

    @rt.post("/api/sessions/{session_id}/results", response_model=None)
    def custom_save_results(
        session_id: UUID,
        rows: list[ResultIn],
        user: dict[str, object] = admin_steward_dependency,
    ) -> list[dict[str, object]]:
        return cast(
            list[dict[str, object]],
            _save_results(
                session_id,
                rows,
                user,
                fetch_one,
                connection,
                simulations_provider(),
                publish,
                jsonable,
            ),
        )

    return rt, {"save_results": custom_save_results}


__all__ = [
    "admin_steward_dependency",
    "create_results_write_router",
    "results_write_handlers",
    "results_write_router",
    "router",
    "save_results",
]
