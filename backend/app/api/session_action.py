from __future__ import annotations

from collections.abc import Callable, Mapping
from contextlib import AbstractContextManager
from typing import Annotated, Any, cast
from uuid import UUID

from fastapi import APIRouter, Depends

from ..core.events import EventBus
from ..core.request_auth import require_roles
from ..core.request_database import DatabaseSession
from ..core.runtime import get_bus, get_simulations
from ..core.serialization import jsonable
from ..core.validation import _require_crud_record
from ..schemas_operations import Action
from ..session_lifecycle import run_session_action
from ..simulation_core import Simulation
from .laps import get_race_db

router = APIRouter()
session_action_router = router

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


def _ensure_session_reset_allowed(
    session_id: UUID, database: DatabaseSession | None = None
) -> None:
    import sys

    main_module = sys.modules.get("backend.app.main")
    fn = getattr(main_module, "ensure_session_reset_allowed", None)
    if fn is not None:
        fn(session_id)
        return
    from ..session_measurements import ensure_reset_allowed

    db = _resolve_db(database)
    ensure_reset_allowed(session_id, db.fetch_one)


def _clear_session_measurements(
    session_id: UUID,
    database: DatabaseSession | None = None,
    bus: EventBus | None = None,
) -> None:
    import sys

    main_module = sys.modules.get("backend.app.main")
    fn = getattr(main_module, "clear_session_measurements", None)
    if fn is not None:
        fn(session_id)
        return
    from ..session_measurements import clear_measurements

    mongo_fn = getattr(main_module, "mongo_ready", None)
    if mongo_fn is None:
        from .laps import get_race_telemetry

        mongo_fn = get_race_telemetry
    clear_measurements(
        session_id,
        mongo_fn,
        lambda: _get_connection(database),
        _resolve_publish(bus),
    )


def _sync_simulation_lifecycle(
    session_id: UUID,
    action: str,
    simulations: dict[str, Simulation] | None = None,
) -> None:
    import sys

    main_module = sys.modules.get("backend.app.main")
    fn = getattr(main_module, "sync_simulation_lifecycle", None)
    if fn is not None:
        fn(session_id, action)
        return
    from ..simulation_lifecycle import sync_lifecycle

    sync_lifecycle(session_id, action, _resolve_simulations(simulations))


def _cancel_automatic_pit_reservations(
    session_id: UUID,
    database: DatabaseSession | None = None,
    bus: EventBus | None = None,
) -> None:
    import sys

    main_module = sys.modules.get("backend.app.main")
    fn = getattr(main_module, "cancel_automatic_pit_reservations", None)
    if fn is not None:
        fn(session_id)
        return
    from ..simulation_pit import cancel_automatic_reservations

    cancel_automatic_reservations(
        session_id,
        lambda: _get_connection(database),
        _resolve_publish(bus),
    )


@router.post("/api/sessions/{session_id}/action", response_model=None)
async def session_action(
    session_id: UUID,
    body: Action,
    user: Annotated[dict[str, Any] | None, admin_steward_dependency] = None,
    database: Annotated[DatabaseSession | None, Depends(get_race_db)] = None,
    simulations: Annotated[dict[str, Simulation] | None, Depends(get_simulations)] = None,
    bus: Annotated[EventBus | None, Depends(get_bus)] = None,
) -> dict[str, object]:
    db = _resolve_db(database)
    sims = _resolve_simulations(simulations)
    pub = _resolve_publish(bus)
    return cast(
        dict[str, object],
        await run_session_action(
            session_id,
            body,
            user,
            _require_crud_record,
            db.fetch_one,
            lambda s_id: _ensure_session_reset_allowed(s_id, database),
            sims,
            lambda: _get_connection(database),
            lambda s_id: _clear_session_measurements(s_id, database, bus),
            lambda s_id, act: _sync_simulation_lifecycle(s_id, act, simulations),
            lambda s_id: _cancel_automatic_pit_reservations(s_id, database, bus),
            jsonable,
            pub,
        ),
    )


session_action_handlers: dict[str, Callable[..., Any]] = {
    "session_action": session_action,
}


def create_session_action_router(
    _require_crud_record: Callable[[Any, str], Any],
    fetch_one: Callable[[str, tuple[Any, ...]], Any],
    ensure_session_reset_allowed: Callable[[UUID], Any],
    simulations_provider: Callable[[], Mapping[str, Any]],
    connection: Callable[[], Any],
    clear_session_measurements: Callable[[UUID], Any],
    sync_simulation_lifecycle: Callable[[UUID, str], Any],
    cancel_automatic_pit_reservations: Callable[[UUID], Any],
    jsonable: Callable[[Any], Any],
    publish: Callable[[UUID, str, Any], Any],
    admin_steward_dependency: Any,
) -> tuple[APIRouter, dict[str, Callable[..., Any]]]:
    rt = APIRouter()

    @rt.post("/api/sessions/{session_id}/action", response_model=None)
    async def custom_session_action(
        session_id: UUID,
        body: Action,
        user: dict[str, object] = admin_steward_dependency,
    ) -> dict[str, object]:
        return cast(
            dict[str, object],
            await run_session_action(
                session_id,
                body,
                user,
                _require_crud_record,
                fetch_one,
                ensure_session_reset_allowed,
                simulations_provider(),
                connection,
                clear_session_measurements,
                sync_simulation_lifecycle,
                cancel_automatic_pit_reservations,
                jsonable,
                publish,
            ),
        )

    return rt, {"session_action": custom_session_action}


__all__ = [
    "admin_steward_dependency",
    "create_session_action_router",
    "router",
    "session_action",
    "session_action_handlers",
    "session_action_router",
]
