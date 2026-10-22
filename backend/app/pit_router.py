from __future__ import annotations

from collections.abc import Callable
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends

from .pit_repository import list_pit_boxes, list_pit_reservations


def create_pit_router(
    current_user: Callable[..., Any],
    jsonable: Callable[[Any], Any],
) -> APIRouter:
    router = APIRouter()

    @router.get("/api/pit-boxes")
    def pit_boxes(event_id: UUID, user=Depends(current_user)):
        return jsonable(list_pit_boxes(event_id))

    @router.get("/api/pit-reservations")
    def pit_reservations(session_id: UUID, user=Depends(current_user)):
        return jsonable(list_pit_reservations(session_id))

    return router
