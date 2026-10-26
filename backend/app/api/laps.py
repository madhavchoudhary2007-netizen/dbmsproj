from __future__ import annotations

from collections.abc import Callable, Iterator, Sequence
from typing import TYPE_CHECKING, Annotated, Any, cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pymongo.collection import Collection

from ..core.request_auth import current_user, require_roles
from ..core.request_database import DatabaseRow, DatabaseSession, get_database
from ..core.runtime import RuntimeState, get_telemetry
from ..core.serialization import jsonable
from ..pit_repository import PIT_RESERVATION_SELECT

router = APIRouter()
laps_router = router

admin_role_dependency = Depends(require_roles("ADMIN", "admin"))


def admin(
    user: Annotated[dict[str, Any], admin_role_dependency],
) -> dict[str, Any]:
    return user


class _MonkeypatchedDatabaseSession(DatabaseSession):
    def __init__(
        self,
        fetch_one_fn: Callable[..., Any],
        fetch_all_fn: Callable[..., Any],
    ) -> None:
        self.pool = cast(Any, None)
        self._fetch_one_fn = fetch_one_fn
        self._fetch_all_fn = fetch_all_fn

    def fetch_one(self, sql: str, params: Sequence[Any] = ()) -> DatabaseRow | None:
        try:
            row = self._fetch_one_fn(sql, params)
        except TypeError:
            row = self._fetch_one_fn(sql)
        return dict(row) if row is not None else None

    def fetch_all(self, sql: str, params: Sequence[Any] = ()) -> list[DatabaseRow]:
        try:
            rows = self._fetch_all_fn(sql, params)
        except TypeError:
            rows = self._fetch_all_fn(sql)
        return [dict(r) for r in rows] if rows is not None else []


def get_race_db(request: Request) -> Iterator[DatabaseSession]:
    if get_database in getattr(request.app, "dependency_overrides", {}):
        yield cast(DatabaseSession, request.app.dependency_overrides[get_database]())
        return

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

    is_monkeypatched = (cur_fetch_one is not db_module.fetch_one) or (
        cur_fetch_all is not db_module.fetch_all
    )
    runtime = getattr(request.app.state, "runtime", None)
    pool = runtime.pool if isinstance(runtime, RuntimeState) else None
    if is_monkeypatched or pool is None or pool.closed:
        yield _MonkeypatchedDatabaseSession(cur_fetch_one, cur_fetch_all)
    else:
        yield DatabaseSession(pool)


def get_race_telemetry(request: Request) -> Collection[dict[str, Any]]:
    if get_telemetry in getattr(request.app, "dependency_overrides", {}):
        return cast(Collection[dict[str, Any]], request.app.dependency_overrides[get_telemetry]())

    import sys

    main_module = sys.modules.get("backend.app.main")
    m_mongo_ready = getattr(main_module, "mongo_ready", None) if main_module is not None else None
    orig_mongo_ready = (
        getattr(main_module, "_default_mongo_ready", None) if main_module is not None else None
    )

    if (
        m_mongo_ready is not None
        and orig_mongo_ready is not None
        and m_mongo_ready is not orig_mongo_ready
    ):
        return cast(Collection[dict[str, Any]], m_mongo_ready())

    runtime = getattr(request.app.state, "runtime", None)
    if isinstance(runtime, RuntimeState) and runtime.telemetry_collection is not None:
        return runtime.telemetry_collection

    if m_mongo_ready is not None:
        try:
            return cast(Collection[dict[str, Any]], m_mongo_ready())
        except HTTPException:
            pass

    if isinstance(runtime, RuntimeState):
        return get_telemetry(runtime)

    raise HTTPException(status_code=503, detail="MongoDB telemetry store is unavailable")


def race_lap_measurements(
    col: Collection[dict[str, Any]], match: dict[str, Any]
) -> list[dict[str, Any]]:
    # Collapse retries to one complete lap per driver, retaining the latest stored measurement.
    return list(
        col.aggregate(
            [
                {"$match": {**match, "sector": 3, "lap_time_ms": {"$gt": 0}}},
                {"$sort": {"ts": 1}},
                {
                    "$group": {
                        "_id": {"driver_id": "$driver_id", "lap": "$lap"},
                        "record": {"$last": "$$ROOT"},
                    }
                },
                {"$replaceRoot": {"newRoot": "$record"}},
                {"$project": {"_id": 0}},
                {"$sort": {"lap": 1, "position": 1}},
            ]
        )
    )


@router.get("/api/dbms/races/{session_id}/laps")
def dbms_race_laps(
    session_id: UUID,
    database: Annotated[DatabaseSession, Depends(get_race_db)],
    col: Annotated[Collection[dict[str, Any]], Depends(get_race_telemetry)],
    user: Annotated[dict[str, Any], Depends(admin)],
) -> Any:
    session = database.fetch_one(
        "SELECT id FROM race_sessions WHERE id=%s AND session_type='RACE'", (session_id,)
    )
    if not session:
        raise HTTPException(404, "Race not found")
    match = {"session_id": str(session_id)}
    laps = race_lap_measurements(col, match)
    source = (
        "historical_demo"
        if laps and all(x.get("source") == "historical_demo" for x in laps)
        else "recorded_telemetry"
    )
    return jsonable({"session_id": session_id, "laps": laps, "lap_source": source})


@router.get("/api/sessions/{session_id}/laps")
def session_laps(
    session_id: UUID,
    database: Annotated[DatabaseSession, Depends(get_race_db)],
    col: Annotated[Collection[dict[str, Any]], Depends(get_race_telemetry)],
    user: Annotated[dict[str, Any], Depends(current_user)],
) -> Any:
    session = database.fetch_one("SELECT id FROM race_sessions WHERE id=%s", (session_id,))
    if not session:
        raise HTTPException(404, "Session not found")
    laps = race_lap_measurements(col, {"session_id": str(session_id)})
    incidents = database.fetch_all(
        """SELECT i.*,u.full_name AS driver_name FROM incident_reports i
    JOIN drivers d ON d.id=i.driver_id JOIN users u ON u.id=d.user_id
    WHERE i.session_id=%s ORDER BY i.lap,i.id""",
        (session_id,),
    )
    stops = database.fetch_all(
        PIT_RESERVATION_SELECT + " WHERE r.session_id=%s ORDER BY r.starts_at", (session_id,)
    )
    return jsonable(
        {
            "session_id": session_id,
            "laps": laps,
            "incidents": incidents,
            "pit_reservations": stops,
        }
    )


def create_laps_router(
    fetch_one: Callable[..., DatabaseRow | None],
    fetch_all: Callable[..., list[DatabaseRow]],
    jsonable: Callable[[Any], Any],
    mongo_ready: Callable[[], Collection[dict[str, Any]]],
    lap_measurements: Callable[[Collection[dict[str, Any]], dict[str, Any]], list[dict[str, Any]]],
    admin_dependency: Any,
    authenticated_user_dependency: Any,
) -> tuple[APIRouter, dict[str, Callable[..., Any]]]:
    rt = APIRouter()
    measurements = lap_measurements

    @rt.get("/api/dbms/races/{session_id}/laps")
    def dbms_race_laps(session_id: UUID, user: Any = admin_dependency) -> Any:
        session = fetch_one(
            "SELECT id FROM race_sessions WHERE id=%s AND session_type='RACE'", (session_id,)
        )
        if not session:
            raise HTTPException(404, "Race not found")
        col = mongo_ready()
        match = {"session_id": str(session_id)}
        laps = measurements(col, match)
        source = (
            "historical_demo"
            if laps and all(x.get("source") == "historical_demo" for x in laps)
            else "recorded_telemetry"
        )
        return jsonable({"session_id": session_id, "laps": laps, "lap_source": source})

    @rt.get("/api/sessions/{session_id}/laps")
    def session_laps(session_id: UUID, user: Any = authenticated_user_dependency) -> Any:
        session = fetch_one("SELECT id FROM race_sessions WHERE id=%s", (session_id,))
        if not session:
            raise HTTPException(404, "Session not found")
        laps = measurements(mongo_ready(), {"session_id": str(session_id)})
        incidents = fetch_all(
            """SELECT i.*,u.full_name AS driver_name FROM incident_reports i
        JOIN drivers d ON d.id=i.driver_id JOIN users u ON u.id=d.user_id
        WHERE i.session_id=%s ORDER BY i.lap,i.id""",
            (session_id,),
        )
        stops = fetch_all(
            PIT_RESERVATION_SELECT + " WHERE r.session_id=%s ORDER BY r.starts_at", (session_id,)
        )
        return jsonable(
            {
                "session_id": session_id,
                "laps": laps,
                "incidents": incidents,
                "pit_reservations": stops,
            }
        )

    return rt, {"dbms_race_laps": dbms_race_laps, "session_laps": session_laps}


if TYPE_CHECKING:
    from .race_archive import dbms_race as dbms_race


def __getattr__(name: str) -> Any:
    if name == "dbms_race":
        from .race_archive import dbms_race

        return dbms_race
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "admin",
    "create_laps_router",
    "dbms_race",
    "dbms_race_laps",
    "get_race_db",
    "get_race_telemetry",
    "laps_router",
    "race_lap_measurements",
    "router",
    "session_laps",
]
