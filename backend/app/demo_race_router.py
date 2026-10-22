from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Depends, Query

from .schemas_simulation import DemoRaceCreate

DEFAULT_DEMO_RACE_CREATE = DemoRaceCreate()


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

    return router
