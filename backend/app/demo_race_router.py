from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Depends, Query


def create_demo_race_router(
    current_user: Callable[..., Any],
    demo_race_row: Callable[[Any], Any],
    list_demo_race_ids: Callable[[int, int], list[dict[str, Any]]],
) -> APIRouter:
    router = APIRouter()
    user_dependency = Depends(current_user)

    @router.get("/api/demo-races")
    def list_demo_races(
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0),
        user: Any = user_dependency,
    ) -> list[Any]:
        ids = list_demo_race_ids(limit, offset)
        return [demo_race_row(row["session_id"]) for row in ids]

    return router
