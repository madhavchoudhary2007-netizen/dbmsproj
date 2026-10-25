from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends

from .core.request_auth import current_user
from .core.request_database import DatabaseSession, get_database
from .core.serialization import jsonable
from .pit_repository import list_pit_boxes, list_pit_reservations

router = APIRouter()


@router.get("/api/pit-boxes", response_model=None)
def pit_boxes(
    event_id: UUID,
    user: Annotated[dict[str, Any], Depends(current_user)],
    database: Annotated[DatabaseSession, Depends(get_database)],
) -> Any:
    return jsonable(list_pit_boxes(database, event_id))


@router.get("/api/pit-reservations", response_model=None)
def pit_reservations(
    session_id: UUID,
    user: Annotated[dict[str, Any], Depends(current_user)],
    database: Annotated[DatabaseSession, Depends(get_database)],
) -> Any:
    return jsonable(list_pit_reservations(database, session_id))
