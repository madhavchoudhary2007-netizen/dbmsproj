from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter

from .results_read import create_results_read_router
from .results_write import create_results_write_router
from .session_action import create_session_action_router


def register_race_operation_routers(
    app: Any,
    require_crud_record: Callable[..., Any],
    fetch_one: Callable[..., Any],
    ensure_session_reset_allowed: Callable[..., Any],
    simulations_provider: Callable[..., Any],
    connection: Callable[..., Any],
    clear_session_measurements: Callable[..., Any],
    sync_simulation_lifecycle: Callable[..., Any],
    cancel_automatic_pit_reservations: Callable[..., Any],
    jsonable: Callable[..., Any],
    publish: Callable[..., Any],
    admin_steward_dependency: Any,
    fetch_all: Callable[..., Any],
    authenticated_user_dependency: Any,
) -> tuple[
    APIRouter,
    dict[str, Callable[..., Any]],
    APIRouter,
    dict[str, Callable[..., Any]],
    APIRouter,
    dict[str, Callable[..., Any]],
]:
    session_action_router, session_action_handlers = create_session_action_router(
        require_crud_record,
        fetch_one,
        ensure_session_reset_allowed,
        simulations_provider,
        connection,
        clear_session_measurements,
        sync_simulation_lifecycle,
        cancel_automatic_pit_reservations,
        jsonable,
        publish,
        admin_steward_dependency,
    )
    app.include_router(session_action_router)

    results_read_router, results_read_handlers = create_results_read_router(
        fetch_all,
        jsonable,
        connection,
        authenticated_user_dependency,
        admin_steward_dependency,
    )
    app.include_router(results_read_router)

    results_write_router, results_write_handlers = create_results_write_router(
        fetch_one,
        connection,
        simulations_provider,
        publish,
        jsonable,
        admin_steward_dependency,
    )
    app.include_router(results_write_router)

    return (
        session_action_router,
        session_action_handlers,
        results_read_router,
        results_read_handlers,
        results_write_router,
        results_write_handlers,
    )
