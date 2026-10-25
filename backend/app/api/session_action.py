from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, cast
from uuid import UUID

from fastapi import APIRouter

from ..schemas_operations import Action
from ..session_lifecycle import run_session_action


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
    router = APIRouter()

    @router.post("/api/sessions/{session_id}/action", response_model=None)
    async def session_action(
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

    return router, {"session_action": session_action}
