from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter
from pymongo.collection import Collection

from ..database import DatabaseRow
from .laps import (
    create_laps_router,
    dbms_race_laps,
    laps_router,
    session_laps,
)
from .race_archive import (
    create_race_archive_router,
    dbms_race,
    race_archive_router,
)

router = APIRouter()
router.include_router(race_archive_router)
router.include_router(laps_router)
race_history_router = router


def register_race_history_routes(
    app: Any,
    fetch_one: Callable[..., DatabaseRow | None] | None = None,
    fetch_all: Callable[..., list[DatabaseRow]] | None = None,
    jsonable: Callable[[Any], Any] | None = None,
    mongo_ready: Callable[[], Collection[dict[str, Any]]] | None = None,
    race_lap_measurements: Callable[
        [Collection[dict[str, Any]], dict[str, Any]], list[dict[str, Any]]
    ]
    | None = None,
    admin_dependency: Any = None,
    authenticated_user_dependency: Any = None,
) -> dict[str, Callable[..., Any]]:
    if (
        fetch_one is not None
        and fetch_all is not None
        and jsonable is not None
        and mongo_ready is not None
        and race_lap_measurements is not None
    ):
        race_archive_rt, race_archive_handlers = create_race_archive_router(
            fetch_one,
            fetch_all,
            jsonable,
            mongo_ready,
            race_lap_measurements,
            admin_dependency,
        )
        app.include_router(race_archive_rt)

        laps_rt, laps_handlers = create_laps_router(
            fetch_one,
            fetch_all,
            jsonable,
            mongo_ready,
            race_lap_measurements,
            admin_dependency,
            authenticated_user_dependency,
        )
        app.include_router(laps_rt)
        return {**race_archive_handlers, **laps_handlers}

    app.include_router(router)
    return {
        "dbms_race": dbms_race,
        "dbms_race_laps": dbms_race_laps,
        "session_laps": session_laps,
    }


__all__ = [
    "race_history_router",
    "register_race_history_routes",
    "router",
]
