from __future__ import annotations

import sys
from collections.abc import Callable
from typing import Any, cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from .auth_router import current_user
from .core.auth_dependencies import create_role_check
from .core.serialization import jsonable
from .schemas_auth import UserCreate, UserPatch
from .user_repository import (
    UserPatchError,
    list_users,
)
from .user_repository import (
    create_user as create_user_record,
)
from .user_repository import (
    delete_user as delete_user_record,
)
from .user_repository import (
    get_user as get_user_record,
)
from .user_repository import (
    update_user as update_user_record,
)

router = APIRouter()
user_router = router


def require_roles(*allowed: str) -> Callable[..., Any]:
    main_module = sys.modules.get("backend.app.main")
    if main_module is not None and hasattr(main_module, "roles"):
        return cast(Callable[..., Any], main_module.roles(*allowed))
    return create_role_check(allowed, Depends(current_user))


admin_role_dependency = Depends(require_roles("ADMIN"))
admin_user = admin_role_dependency


@router.get("/api/users")
def users(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: dict[str, Any] = admin_user,
) -> object:
    return jsonable(list_users(limit, offset))


@router.get("/api/users/{user_id}")
def get_user(
    user_id: UUID,
    user: dict[str, Any] = admin_user,
) -> object:
    result = get_user_record(user_id)
    if not result:
        raise HTTPException(404, "User not found")
    return jsonable(result)


@router.post("/api/users", status_code=201)
def create_user(
    body: UserCreate,
    user: dict[str, Any] = admin_user,
) -> object:
    return jsonable(create_user_record(body))


@router.patch("/api/users/{user_id}")
def update_user(
    user_id: UUID,
    body: UserPatch,
    user: dict[str, Any] = admin_user,
) -> object:
    try:
        updated = update_user_record(user_id, body)
    except UserPatchError as exc:
        raise HTTPException(422, exc.detail) from exc
    if not updated:
        raise HTTPException(404, "User not found")
    return jsonable(updated)


@router.delete("/api/users/{user_id}", status_code=204)
def delete_user(
    user_id: UUID,
    user: dict[str, Any] = admin_user,
) -> None:
    result = delete_user_record(user_id)
    errors = {
        "not_found": (404, "User not found"),
        "referenced": (409, "User is referenced by official records"),
    }
    if error := errors.get(result):
        raise HTTPException(*error)
    return None


def create_user_router(
    roles: Callable[..., Callable[..., Any]],
    jsonable: Callable[[Any], Any],
) -> APIRouter:
    rt = APIRouter()
    legacy_admin_user = Depends(roles("ADMIN"))

    @rt.get("/api/users")
    def legacy_users(
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0),
        user: object = legacy_admin_user,
    ) -> object:
        return jsonable(list_users(limit, offset))

    @rt.get("/api/users/{user_id}")
    def legacy_get_user(user_id: UUID, user: object = legacy_admin_user) -> object:
        result = get_user_record(user_id)
        if not result:
            raise HTTPException(404, "User not found")
        return jsonable(result)

    @rt.post("/api/users", status_code=201)
    def legacy_create_user(body: UserCreate, user: object = legacy_admin_user) -> object:
        return jsonable(create_user_record(body))

    @rt.patch("/api/users/{user_id}")
    def legacy_update_user(
        user_id: UUID, body: UserPatch, user: object = legacy_admin_user
    ) -> object:
        try:
            updated = update_user_record(user_id, body)
        except UserPatchError as exc:
            raise HTTPException(422, exc.detail) from exc
        if not updated:
            raise HTTPException(404, "User not found")
        return jsonable(updated)

    @rt.delete("/api/users/{user_id}", status_code=204)
    def legacy_delete_user(user_id: UUID, user: object = legacy_admin_user) -> None:
        result = delete_user_record(user_id)
        errors = {
            "not_found": (404, "User not found"),
            "referenced": (409, "User is referenced by official records"),
        }
        if error := errors.get(result):
            raise HTTPException(*error)
        return None

    return rt


__all__ = [
    "admin_role_dependency",
    "admin_user",
    "create_user",
    "create_user_router",
    "delete_user",
    "get_user",
    "require_roles",
    "router",
    "update_user",
    "user_router",
    "users",
]
