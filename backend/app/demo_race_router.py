from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from .core.request_database import DatabaseSession, get_database
from .schemas_simulation import DemoRaceCreate

DEFAULT_DEMO_RACE_CREATE = DemoRaceCreate()


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
    router = APIRouter()
    user_dependency = Depends(current_user)
    admin_steward_dependency = Depends(admin_steward)

    @router.get("/api/demo-races")
    def list_demo_races(
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0),
        user: Any = user_dependency,
    ) -> list[Any]:
        ids = list_demo_race_ids(limit, offset)
        return [demo_race_row(row["session_id"]) for row in ids]

    @router.post("/api/demo-races", status_code=201)
    async def create_demo_race(
        body: DemoRaceCreate = DEFAULT_DEMO_RACE_CREATE,
        user: Any = admin_steward_dependency,
    ) -> Any:
        return await run_demo_race_create(
            body, make_demo_race, launch_demo_simulation, demo_race_row
        )

    @router.delete("/api/demo-races/{session_id}", status_code=204)
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

    return router
