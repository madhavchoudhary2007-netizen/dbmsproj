from __future__ import annotations

from collections.abc import Callable, Mapping
from contextlib import AbstractContextManager
from typing import Annotated, Any, cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from ..core.events import EventBus
from ..core.request_auth import require_roles
from ..core.request_database import DatabaseSession
from ..core.runtime import get_bus, get_simulations
from ..core.serialization import jsonable
from ..pit_repository import create_automatic_reservation as repo_create_automatic_reservation
from ..pit_reservation_service import (
    run_reserve_pit,
    run_reserve_pit_auto,
    run_update_pit_reservation,
)
from ..schemas_operations import AutoReservationIn, ReservationIn, ReservationStatus
from ..simulation_core import Simulation
from .laps import get_race_db

router = APIRouter()
pit_write_router = router

admin_steward_principal_dependency = Depends(require_roles("ADMIN", "STEWARD", "PRINCIPAL"))


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


def _check_principal_own_team(
    team_id: UUID,
    user: dict[str, Any],
    database: DatabaseSession | None = None,
) -> None:
    if user.get("role") == "PRINCIPAL":
        db = _resolve_db(database)
        own_team = db.fetch_one(
            "SELECT id FROM teams WHERE id=%s AND principal_user_id=%s", (team_id, user.get("id"))
        )
        if not own_team:
            raise HTTPException(403, "Principals may reserve pit boxes only for their own team")


def _resolve_require_principal_own_team(
    database: DatabaseSession | None = None,
) -> Callable[[UUID, dict[str, Any]], None]:
    import sys

    main_module = sys.modules.get("backend.app.main")
    if main_module is not None:
        main_fn = getattr(main_module, "_require_principal_own_team", None)
        orig_fn = getattr(main_module, "_default_require_principal_own_team", None)
        if main_fn is not None and (orig_fn is None or main_fn is not orig_fn):
            return cast(Callable[[UUID, dict[str, Any]], None], main_fn)
    return lambda team_id, u: _check_principal_own_team(team_id, u, database)


def _resolve_create_automatic_reservation() -> Callable[..., Any]:
    import sys

    main_module = sys.modules.get("backend.app.main")
    if main_module is not None and hasattr(main_module, "create_automatic_reservation"):
        return cast(Callable[..., Any], main_module.create_automatic_reservation)
    return repo_create_automatic_reservation


@router.post("/api/pit-reservations", status_code=201, response_model=None)
def reserve_pit(
    body: ReservationIn,
    user: Annotated[dict[str, Any] | None, admin_steward_principal_dependency] = None,
    database: Annotated[DatabaseSession | None, Depends(get_race_db)] = None,
    bus: Annotated[EventBus | None, Depends(get_bus)] = None,
) -> Any:
    req_team = _resolve_require_principal_own_team(database)

    def conn_fn() -> AbstractContextManager[Any]:
        return _get_connection(database)

    pub_fn = _resolve_publish(bus)
    u = user if user is not None else {}
    return run_reserve_pit(
        body,
        u,
        req_team,
        conn_fn,
        jsonable,
        pub_fn,
    )


@router.post("/api/pit-reservations/auto", status_code=201, response_model=None)
def reserve_pit_auto(
    body: AutoReservationIn,
    user: Annotated[dict[str, Any] | None, admin_steward_principal_dependency] = None,
    database: Annotated[DatabaseSession | None, Depends(get_race_db)] = None,
    simulations: Annotated[dict[str, Simulation] | None, Depends(get_simulations)] = None,
    bus: Annotated[EventBus | None, Depends(get_bus)] = None,
) -> Any:
    req_team = _resolve_require_principal_own_team(database)
    db = _resolve_db(database)
    sims = _resolve_simulations(simulations)
    create_auto = _resolve_create_automatic_reservation()
    pub_fn = _resolve_publish(bus)
    u = user if user is not None else {}
    return run_reserve_pit_auto(
        body,
        u,
        req_team,
        db.fetch_one,
        sims,
        create_auto,
        jsonable,
        pub_fn,
    )


@router.patch("/api/pit-reservations/{reservation_id}", response_model=None)
def update_pit_reservation(
    reservation_id: UUID,
    body: ReservationStatus,
    user: Annotated[dict[str, Any] | None, admin_steward_principal_dependency] = None,
    database: Annotated[DatabaseSession | None, Depends(get_race_db)] = None,
    bus: Annotated[EventBus | None, Depends(get_bus)] = None,
) -> Any:
    def conn_fn() -> AbstractContextManager[Any]:
        return _get_connection(database)

    pub_fn = _resolve_publish(bus)
    u = user if user is not None else {}
    return run_update_pit_reservation(
        reservation_id,
        body,
        u,
        conn_fn,
        jsonable,
        pub_fn,
    )


pit_write_handlers: dict[str, Callable[..., Any]] = {
    "reserve_pit": reserve_pit,
    "reserve_pit_auto": reserve_pit_auto,
    "update_pit_reservation": update_pit_reservation,
}
_pit_write_handlers = pit_write_handlers


def create_pit_write_router(
    legacy_require_principal_own_team: Callable[[UUID, dict[str, Any]], None],
    connection: Callable[..., Any],
    legacy_jsonable: Callable[[Any], Any],
    publish: Callable[[UUID, str, Any], Any],
    fetch_one: Callable[..., dict[str, Any] | None],
    simulations_provider: Callable[[], Mapping[str, Any]],
    create_automatic_reservation: Callable[..., Any],
    legacy_admin_steward_principal_dependency: Any,
) -> tuple[APIRouter, dict[str, Callable[..., Any]]]:
    rt = APIRouter()

    @rt.post("/api/pit-reservations", status_code=201, response_model=None)
    def legacy_reserve_pit(
        body: ReservationIn, user: Any = legacy_admin_steward_principal_dependency
    ) -> Any:
        return run_reserve_pit(
            body,
            user,
            legacy_require_principal_own_team,
            connection,
            legacy_jsonable,
            publish,
        )

    @rt.post("/api/pit-reservations/auto", status_code=201, response_model=None)
    def legacy_reserve_pit_auto(
        body: AutoReservationIn, user: Any = legacy_admin_steward_principal_dependency
    ) -> Any:
        return run_reserve_pit_auto(
            body,
            user,
            legacy_require_principal_own_team,
            fetch_one,
            simulations_provider(),
            create_automatic_reservation,
            legacy_jsonable,
            publish,
        )

    @rt.patch("/api/pit-reservations/{reservation_id}", response_model=None)
    def legacy_update_pit_reservation(
        reservation_id: UUID,
        body: ReservationStatus,
        user: Any = legacy_admin_steward_principal_dependency,
    ) -> Any:
        return run_update_pit_reservation(
            reservation_id,
            body,
            user,
            connection,
            legacy_jsonable,
            publish,
        )

    return rt, {
        "reserve_pit": legacy_reserve_pit,
        "reserve_pit_auto": legacy_reserve_pit_auto,
        "update_pit_reservation": legacy_update_pit_reservation,
    }


__all__ = [
    "_pit_write_handlers",
    "admin_steward_principal_dependency",
    "create_pit_write_router",
    "pit_write_handlers",
    "pit_write_router",
    "reserve_pit",
    "reserve_pit_auto",
    "router",
    "update_pit_reservation",
]
