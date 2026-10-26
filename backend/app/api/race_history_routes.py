from collections.abc import Callable
from typing import Any

from pymongo.collection import Collection

from .laps import create_laps_router
from .race_archive import create_race_archive_router


def register_race_history_routes(
    app: Any,
    fetch_one: Callable[..., Any],
    fetch_all: Callable[..., Any],
    jsonable: Callable[[Any], Any],
    mongo_ready: Callable[[], Collection[dict[str, Any]]],
    race_lap_measurements: Callable[
        [Collection[dict[str, Any]], dict[str, Any]], list[dict[str, Any]]
    ],
    admin_dependency: Any,
    authenticated_user_dependency: Any,
) -> dict[str, Callable[..., Any]]:
    race_archive_router, race_archive_handlers = create_race_archive_router(
        lambda *a, **kw: fetch_one(*a, **kw),
        lambda *a, **kw: fetch_all(*a, **kw),
        lambda value: jsonable(value),
        lambda: mongo_ready(),
        lambda col, match: race_lap_measurements(col, match),
        admin_dependency,
    )
    app.include_router(race_archive_router)

    laps_router, laps_handlers = create_laps_router(
        lambda *a, **kw: fetch_one(*a, **kw),
        lambda *a, **kw: fetch_all(*a, **kw),
        lambda value: jsonable(value),
        lambda: mongo_ready(),
        lambda col, match: race_lap_measurements(col, match),
        admin_dependency,
        authenticated_user_dependency,
    )
    app.include_router(laps_router)
    return {**race_archive_handlers, **laps_handlers}
