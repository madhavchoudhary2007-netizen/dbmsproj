from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, FastAPI

from .pit_write import create_pit_write_router
from .stewards import create_stewards_router


def register_operations_routes(
    app: FastAPI,
    pit_router: APIRouter,
    *,
    fetch_all: Callable[..., Any],
    jsonable: Callable[..., Any],
    limit_offset: Callable[..., Any],
    authenticated_user_dependency: Any,
    steward_connection: Callable[..., Any],
    pit_write_connection: Callable[..., Any],
    publish: Callable[..., Any],
    admin_steward_dependency: Any,
    require_principal_own_team: Callable[..., Any],
    fetch_one: Callable[..., Any],
    simulations: Callable[..., Any],
    create_automatic_reservation: Callable[..., Any],
    admin_steward_principal_dependency: Any,
) -> tuple[APIRouter, dict[str, Callable[..., Any]], APIRouter, dict[str, Callable[..., Any]]]:
    stewards_router, stewards_handlers = create_stewards_router(
        fetch_all,
        jsonable,
        limit_offset,
        authenticated_user_dependency,
        steward_connection,
        publish,
        admin_steward_dependency,
    )
    pit_write_router, pit_write_handlers = create_pit_write_router(
        require_principal_own_team,
        pit_write_connection,
        jsonable,
        publish,
        fetch_one,
        simulations,
        create_automatic_reservation,
        admin_steward_principal_dependency,
    )

    app.include_router(stewards_router)
    app.include_router(pit_router)
    app.include_router(pit_write_router)
    return stewards_router, stewards_handlers, pit_write_router, pit_write_handlers
