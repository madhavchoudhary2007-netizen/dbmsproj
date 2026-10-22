from __future__ import annotations

from collections.abc import Callable
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from .schemas_auth import UserCreate, UserPatch
from .user_repository import (
    UserPatchError,
    create_user as create_user_record,
    delete_user as delete_user_record,
    get_user as get_user_record,
    list_users,
    update_user as update_user_record,
)


def create_user_router(
    roles: Callable[..., Callable[..., Any]],
    jsonable: Callable[[Any], Any],
) -> APIRouter:
    router = APIRouter()

    @router.get("/api/users")
    def users(
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0),
        user=Depends(roles("ADMIN")),
    ):
        return jsonable(list_users(limit, offset))

    @router.get("/api/users/{user_id}")
    def get_user(user_id: UUID, user=Depends(roles("ADMIN"))):
        result = get_user_record(user_id)
        if not result:
            raise HTTPException(404, "User not found")
        return jsonable(result)

    @router.post("/api/users", status_code=201)
    def create_user(body: UserCreate, user=Depends(roles("ADMIN"))):
        return jsonable(create_user_record(body))

    @router.patch("/api/users/{user_id}")
    def update_user(user_id: UUID, body: UserPatch, user=Depends(roles("ADMIN"))):
        try:
            updated = update_user_record(user_id, body)
        except UserPatchError as exc:
            raise HTTPException(422, exc.detail) from exc
        if not updated:
            raise HTTPException(404, "User not found")
        return jsonable(updated)

    @router.delete("/api/users/{user_id}", status_code=204)
    def delete_user(user_id: UUID, user=Depends(roles("ADMIN"))):
        result = delete_user_record(user_id)
        if result == "not_found":
            raise HTTPException(404, "User not found")
        if result == "referenced":
            raise HTTPException(409, "User is referenced by official records")
        return None

    return router
