from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, FastAPI

from .pit_write import (
    create_pit_write_router,
    pit_write_handlers,
    pit_write_router,
    reserve_pit,
    reserve_pit_auto,
    update_pit_reservation,
)
from .stewards import (
    create_incident,
    create_stewards_router,
    decide_incident,
    get_incidents,
    stewards_handlers,
    stewards_router,
)


def register_operations_routes(
    app: FastAPI,
    pit_router: APIRouter,
    *,
    fetch_all: Callable[..., Any] | None = None,
    jsonable: Callable[..., Any] | None = None,
    limit_offset: Callable[..., Any] | None = None,
    authenticated_user_dependency: Any = None,
    steward_connection: Callable[..., Any] | None = None,
    pit_write_connection: Callable[..., Any] | None = None,
    publish: Callable[..., Any] | None = None,
    admin_steward_dependency: Any = None,
    require_principal_own_team: Callable[..., Any] | None = None,
    fetch_one: Callable[..., Any] | None = None,
    simulations: Callable[..., Any] | None = None,
    create_automatic_reservation: Callable[..., Any] | None = None,
    admin_steward_principal_dependency: Any = None,
) -> tuple[APIRouter, dict[str, Callable[..., Any]], APIRouter, dict[str, Callable[..., Any]]]:
    if (
        fetch_all is not None
        or steward_connection is not None
        or pit_write_connection is not None
        or require_principal_own_team is not None
    ):
        s_router, s_handlers = create_stewards_router(
            fetch_all or (lambda *a, **kw: []),
            jsonable or (lambda v: v),
            limit_offset or (lambda lim, off: (lim, off)),
            authenticated_user_dependency,
            steward_connection or (lambda: None),
            publish or (lambda *a, **kw: None),
            admin_steward_dependency,
        )
        p_router, p_handlers = create_pit_write_router(
            require_principal_own_team or (lambda t, u: None),
            pit_write_connection or (lambda *a, **kw: None),
            jsonable or (lambda v: v),
            publish or (lambda *a, **kw: None),
            fetch_one or (lambda *a, **kw: None),
            simulations or (lambda: {}),
            create_automatic_reservation or (lambda *a, **kw: None),
            admin_steward_principal_dependency,
        )
    else:
        s_router, s_handlers = stewards_router, stewards_handlers
        p_router, p_handlers = pit_write_router, pit_write_handlers

    app.include_router(s_router)
    app.include_router(pit_router)
    app.include_router(p_router)
    return s_router, s_handlers, p_router, p_handlers


__all__ = [
    "create_incident",
    "create_pit_write_router",
    "create_stewards_router",
    "decide_incident",
    "get_incidents",
    "pit_write_handlers",
    "pit_write_router",
    "register_operations_routes",
    "reserve_pit",
    "reserve_pit_auto",
    "stewards_handlers",
    "stewards_router",
    "update_pit_reservation",
]
