from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Annotated, Any, cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg.rows import dict_row
from pymongo.collection import Collection

from .api.laps import get_race_db, get_race_telemetry
from .core.request_auth import current_user, require_roles
from .core.request_database import DatabaseSession, get_database
from .core.runtime import get_simulations
from .core.serialization import jsonable
from .demo_race_repository import (
    DemoRaceDeleteConflict,
    delete_demo_race_records,
    get_demo_race_row,
    list_demo_race_ids,
    validate_demo_race_delete,
)
from .schemas_simulation import DemoRaceCreate
from .simulation_core import Simulation

DEFAULT_DEMO_RACE_CREATE = DemoRaceCreate()

router = APIRouter()
demo_race_router = router

admin_steward_dependency = Depends(require_roles("ADMIN", "STEWARD"))
authenticated_user = Depends(current_user)


def _resolve_simulations(
    simulations: dict[str, Simulation] | None = None,
) -> dict[str, Simulation]:
    if simulations is not None:
        return simulations
    import sys

    main_module = sys.modules.get("backend.app.main") or sys.modules.get("app.main")
    if main_module is not None and hasattr(main_module, "simulations"):
        return cast(dict[str, Simulation], main_module.simulations)
    return {}


def _resolve_demo_race_row(
    session_id: UUID | str,
    simulations: dict[str, Simulation] | None = None,
) -> dict[str, Any] | None:
    import sys

    main_module = sys.modules.get("backend.app.main") or sys.modules.get("app.main")
    if main_module is not None:
        custom_fn = getattr(main_module, "demo_race_row", None)
        orig_fn = getattr(main_module, "_default_demo_race_row", None)
        if custom_fn is not None and (orig_fn is None or custom_fn is not orig_fn):
            return cast(dict[str, Any] | None, custom_fn(session_id))

    row = get_demo_race_row(session_id)
    if not row:
        return None
    result = cast(dict[str, Any], jsonable(row))
    sims = _resolve_simulations(simulations)
    sim = sims.get(str(session_id))
    result["simulation_state"] = sim.status if sim else "stopped"
    return result


def _resolve_make_demo_race(
    collection: Collection[dict[str, Any]] | None = None,
    simulations: dict[str, Simulation] | None = None,
) -> Callable[[int | None], Any]:
    import sys

    main_module = sys.modules.get("backend.app.main") or sys.modules.get("app.main")
    if main_module is not None:
        fn = getattr(main_module, "_make_demo_race", None) or getattr(
            main_module, "make_demo_race", None
        )
        if fn is not None:
            return cast(Callable[[int | None], Any], fn)
    from .demo_race_repository import create_demo_race_records
    from .demo_runtime import build_demo_race

    sims = _resolve_simulations(simulations)
    return lambda cars: build_demo_race(
        cars,
        False,
        lambda: collection,
        create_demo_race_records,
        sims,
        lambda sid: _resolve_demo_race_row(sid, sims),
    )


def _resolve_launch_demo_simulation(
    simulations: dict[str, Simulation] | None = None,
) -> Callable[[Any], Any]:
    import sys

    main_module = sys.modules.get("backend.app.main") or sys.modules.get("app.main")
    if main_module is not None:
        fn = getattr(main_module, "launch_demo_simulation", None)
        if fn is not None:
            return cast(Callable[[Any], Any], fn)

    sims = _resolve_simulations(simulations)

    def _launch(session_id: Any) -> None:
        sim = sims.get(str(session_id))
        if sim is not None:
            sim.status = "running"

    return _launch


def _resolve_connection(database: DatabaseSession | None = None) -> Any:
    if database is not None and getattr(database, "pool", None) is not None:
        return database.connection
    if (
        database is not None
        and getattr(database, "pool", None) is None
        and hasattr(database, "connection")
    ):
        return database.connection
    import sys

    from . import database as db_module

    main_module = sys.modules.get("backend.app.main") or sys.modules.get("app.main")
    conn_fn = (
        getattr(main_module, "connection", db_module.connection)
        if main_module is not None
        else db_module.connection
    )
    return conn_fn


async def run_demo_race_delete(
    session_id: UUID,
    simulations: dict[str, Any],
    connection: Callable[[], Any],
    row_factory: Any,
    mongo_ready: Callable[[], Any],
    delete_conflict: type[Exception],
    validate_delete: Callable[[Any, Any, dict[str, Any]], Any],
    delete_records: Callable[[Any, Any, dict[str, Any]], Any],
) -> None:
    sim = simulations.get(str(session_id))
    with connection() as conn, conn.cursor(row_factory=row_factory) as cur:
        cur.execute(
            """SELECT d.session_id,d.event_id,e.championship_id FROM demo_races d
            JOIN race_events e ON e.id=d.event_id WHERE d.session_id=%s FOR UPDATE OF d""",
            (session_id,),
        )
        marker = cur.fetchone()
        if not marker:
            raise HTTPException(404, "Generated demo race not found")
        col = mongo_ready()
        if col is None:
            raise HTTPException(503, "MongoDB telemetry store is unavailable")
        try:
            validate_delete(cur, session_id, marker)
        except delete_conflict as exc:
            raise HTTPException(409, str(exc)) from exc
        if sim:
            sim.status = "stopped"
            if sim.task and not sim.task.done():
                sim.task.cancel()
                await asyncio.gather(sim.task, return_exceptions=True)
        delete_records(cur, session_id, marker)
    if sim:
        simulations.pop(str(session_id), None)
    col.delete_many({"session_id": str(session_id)})


async def run_demo_race_create(
    body: DemoRaceCreate,
    make_demo_race: Callable[[int | None], Any],
    launch_demo_simulation: Callable[[Any], Any],
    demo_race_row: Callable[[Any], Any],
) -> Any:
    race = await asyncio.to_thread(make_demo_race, body.cars)
    launch_demo_simulation(race["session_id"])
    return demo_race_row(race["session_id"])


@router.get("/api/demo-races")
def list_demo_races(
    user: Annotated[dict[str, Any], authenticated_user],
    database: Annotated[DatabaseSession, Depends(get_race_db)],
    simulations: Annotated[dict[str, Simulation], Depends(get_simulations)],
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[Any]:
    ids = list_demo_race_ids(limit, offset)
    return [_resolve_demo_race_row(row["session_id"], simulations) for row in ids]


@router.post("/api/demo-races", status_code=201)
async def create_demo_race(
    user: Annotated[dict[str, Any], admin_steward_dependency],
    collection: Annotated[Collection[dict[str, Any]], Depends(get_race_telemetry)],
    database: Annotated[DatabaseSession, Depends(get_race_db)],
    simulations: Annotated[dict[str, Simulation], Depends(get_simulations)],
    body: DemoRaceCreate = DEFAULT_DEMO_RACE_CREATE,
) -> Any:
    make_demo_race = _resolve_make_demo_race(collection, simulations)
    launch_demo_simulation = _resolve_launch_demo_simulation(simulations)
    return await run_demo_race_create(
        body,
        make_demo_race,
        launch_demo_simulation,
        lambda sid: _resolve_demo_race_row(sid, simulations),
    )


@router.delete("/api/demo-races/{session_id}", status_code=204)
async def delete_demo_race(
    session_id: UUID,
    database: Annotated[DatabaseSession, Depends(get_race_db)],
    user: Annotated[dict[str, Any], admin_steward_dependency],
    collection: Annotated[Collection[dict[str, Any]], Depends(get_race_telemetry)],
    simulations: Annotated[dict[str, Simulation], Depends(get_simulations)],
) -> None:
    sims = _resolve_simulations(simulations)
    conn_fn = _resolve_connection(database)

    def col_fn() -> Any:
        return collection

    get_col: Callable[[], Any] = col_fn
    if collection is None:
        import sys

        main_module = sys.modules.get("backend.app.main") or sys.modules.get("app.main")
        if main_module is not None and hasattr(main_module, "mongo_ready"):
            get_col = main_module.mongo_ready

    await run_demo_race_delete(
        session_id,
        sims,
        conn_fn,
        dict_row,
        get_col,
        DemoRaceDeleteConflict,
        validate_demo_race_delete,
        delete_demo_race_records,
    )


def create_demo_race_router(
    current_user: Callable[..., Any],
    admin_steward: Callable[..., Any],
    demo_race_row: Callable[[Any], Any],
    list_demo_race_ids: Callable[[int, int], list[dict[str, Any]]],
    make_demo_race: Callable[[int | None], Any],
    launch_demo_simulation: Callable[[Any], Any],
    get_simulations: Callable[[], dict[str, Any]],
    row_factory: Any,
    mongo_ready: Callable[[], Any],
    delete_conflict: type[Exception],
    validate_delete: Callable[[Any, Any, dict[str, Any]], Any],
    delete_records: Callable[[Any, Any, dict[str, Any]], Any],
) -> APIRouter:
    rt = APIRouter()
    user_dependency = Depends(current_user)
    admin_steward_dependency = Depends(admin_steward)

    @rt.get("/api/demo-races")
    def list_demo_races(
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0),
        user: Any = user_dependency,
    ) -> list[Any]:
        ids = list_demo_race_ids(limit, offset)
        return [demo_race_row(row["session_id"]) for row in ids]

    @rt.post("/api/demo-races", status_code=201)
    async def create_demo_race(
        body: DemoRaceCreate = DEFAULT_DEMO_RACE_CREATE,
        user: Any = admin_steward_dependency,
    ) -> Any:
        return await run_demo_race_create(
            body, make_demo_race, launch_demo_simulation, demo_race_row
        )

    @rt.delete("/api/demo-races/{session_id}", status_code=204)
    async def delete_demo_race(
        session_id: UUID,
        database: Annotated[DatabaseSession, Depends(get_database)],
        user: Any = admin_steward_dependency,
    ) -> None:
        await run_demo_race_delete(
            session_id,
            get_simulations(),
            database.connection,
            row_factory,
            mongo_ready,
            delete_conflict,
            validate_delete,
            delete_records,
        )

    return rt
