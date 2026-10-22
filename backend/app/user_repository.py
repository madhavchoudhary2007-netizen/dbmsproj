from __future__ import annotations

from typing import Any, cast
from uuid import UUID

from .database import fetch_all, fetch_one


def list_users(limit: int, offset: int) -> list[dict[str, Any]]:
    return fetch_all(
        "SELECT id,email,full_name,role FROM users "
        "ORDER BY full_name,email LIMIT %s OFFSET %s",
        (limit, offset),
    )


def get_user(user_id: UUID) -> dict[str, Any] | None:
    return cast(
        dict[str, Any] | None,
        fetch_one(
            "SELECT id,email,full_name,role FROM users WHERE id=%s",
            (user_id,),
        ),
    )
