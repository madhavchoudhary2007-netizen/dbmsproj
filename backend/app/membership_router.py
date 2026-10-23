from __future__ import annotations

from collections.abc import Callable
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from .membership_repository import (
    create_membership as create_membership_row,
)
from .membership_repository import (
    list_driver_memberships,
    list_team_memberships,
)
from .membership_repository import (
    update_membership as update_membership_row,
)
from .schemas_competition import MembershipIn, MembershipPatch


def create_membership_router(
    current_user: Callable[..., Any],
    roles: Callable[..., Callable[..., Any]],
    jsonable: Callable[[Any], Any],
) -> APIRouter:
    router = APIRouter()
    authenticated_user = Depends(current_user)
    admin_user = Depends(roles("ADMIN"))

    @router.get("/api/drivers/{driver_id}/memberships")
    def driver_memberships(driver_id: UUID, user=authenticated_user):
        return jsonable(list_driver_memberships(driver_id))

    @router.get("/api/teams/{team_id}/memberships")
    def team_memberships(team_id: UUID, user=authenticated_user):
        return jsonable(list_team_memberships(team_id))

    @router.post("/api/team-memberships", status_code=201)
    def create_membership(body: MembershipIn, user=admin_user):
        return jsonable(create_membership_row(body))

    @router.patch("/api/team-memberships/{membership_id}")
    def update_membership(
        membership_id: UUID,
        body: MembershipPatch,
        user=admin_user,
    ):
        if not body.model_dump(exclude_unset=True):
            raise HTTPException(422, "At least one field is required")
        row = update_membership_row(membership_id, body)
        if not row:
            raise HTTPException(404, "Membership not found")
        return jsonable(row)

    return router
