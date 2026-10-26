from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter

from .results_read import (
    create_results_read_router,
    recalculate,
    results,
    results_read_handlers,
    results_read_router,
    standings,
)
from .results_write import (
    create_results_write_router,
    results_write_handlers,
    results_write_router,
    save_results,
)
from .session_action import (
    create_session_action_router,
    session_action,
    session_action_handlers,
    session_action_router,
)


def register_race_operation_routers(
    app: Any,
    require_crud_record: Callable[..., Any] | None = None,
    fetch_one: Callable[..., Any] | None = None,
    ensure_session_reset_allowed: Callable[..., Any] | None = None,
    simulations_provider: Callable[..., Any] | None = None,
    connection: Callable[..., Any] | None = None,
    clear_session_measurements: Callable[..., Any] | None = None,
    sync_simulation_lifecycle: Callable[..., Any] | None = None,
    cancel_automatic_pit_reservations: Callable[..., Any] | None = None,
    jsonable: Callable[..., Any] | None = None,
    publish: Callable[..., Any] | None = None,
    admin_steward_dependency: Any = None,
    fetch_all: Callable[..., Any] | None = None,
    authenticated_user_dependency: Any = None,
) -> tuple[
    APIRouter,
    dict[str, Callable[..., Any]],
    APIRouter,
    dict[str, Callable[..., Any]],
    APIRouter,
    dict[str, Callable[..., Any]],
]:
    if (
        require_crud_record is not None
        and fetch_one is not None
        and ensure_session_reset_allowed is not None
        and simulations_provider is not None
        and connection is not None
        and clear_session_measurements is not None
        and sync_simulation_lifecycle is not None
        and cancel_automatic_pit_reservations is not None
        and jsonable is not None
        and publish is not None
        and fetch_all is not None
    ):
        sa_router, sa_handlers = create_session_action_router(
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
        rr_router, rr_handlers = create_results_read_router(
            fetch_all,
            jsonable,
            connection,
            authenticated_user_dependency,
            admin_steward_dependency,
        )
        rw_router, rw_handlers = create_results_write_router(
            fetch_one,
            connection,
            simulations_provider,
            publish,
            jsonable,
            admin_steward_dependency,
        )
    else:
        sa_router, sa_handlers = session_action_router, session_action_handlers
        rr_router, rr_handlers = results_read_router, results_read_handlers
        rw_router, rw_handlers = results_write_router, results_write_handlers

    app.include_router(sa_router)
    app.include_router(rr_router)
    app.include_router(rw_router)

    return (
        sa_router,
        sa_handlers,
        rr_router,
        rr_handlers,
        rw_router,
        rw_handlers,
    )


__all__ = [
    "create_results_read_router",
    "create_results_write_router",
    "create_session_action_router",
    "recalculate",
    "register_race_operation_routers",
    "results",
    "results_read_handlers",
    "results_read_router",
    "results_write_handlers",
    "results_write_router",
    "save_results",
    "session_action",
    "session_action_handlers",
    "session_action_router",
    "standings",
]
