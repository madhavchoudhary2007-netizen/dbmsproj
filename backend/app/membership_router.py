from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from .core.request_auth import current_user, require_roles
from .core.request_database import DatabaseSession, get_database
from .core.serialization import jsonable
from .membership_repository import create_membership as create_membership_row
from .membership_repository import list_driver_memberships, list_team_memberships
from .membership_repository import update_membership as update_membership_row
from .schemas_competition import MembershipIn, MembershipPatch

router = APIRouter()


@router.get("/api/drivers/{driver_id}/memberships")
def driver_memberships(
    driver_id: UUID,
    user: Annotated[dict[str, Any], Depends(current_user)],
    database: Annotated[DatabaseSession, Depends(get_database)],
):
    return jsonable(list_driver_memberships(driver_id, database=database))


@router.get("/api/teams/{team_id}/memberships")
def team_memberships(
    team_id: UUID,
    user: Annotated[dict[str, Any], Depends(current_user)],
    database: Annotated[DatabaseSession, Depends(get_database)],
):
    return jsonable(list_team_memberships(team_id, database=database))


@router.post("/api/team-memberships", status_code=201)
def create_membership(
    body: MembershipIn,
    user: Annotated[dict[str, Any], Depends(require_roles("ADMIN"))],
    database: Annotated[DatabaseSession, Depends(get_database)],
):
    return jsonable(create_membership_row(body, database=database))


@router.patch("/api/team-memberships/{membership_id}")
def update_membership(
    membership_id: UUID,
    body: MembershipPatch,
    user: Annotated[dict[str, Any], Depends(require_roles("ADMIN"))],
    database: Annotated[DatabaseSession, Depends(get_database)],
):
    if not body.model_dump(exclude_unset=True):
        raise HTTPException(422, "At least one field is required")
    row = update_membership_row(membership_id, body, database=database)
    if not row:
        raise HTTPException(404, "Membership not found")
    return jsonable(row)
