from __future__ import annotations

from typing import Any, cast
from uuid import UUID

import bcrypt
from psycopg import sql
from psycopg.rows import dict_row

from .database import connection, fetch_all, fetch_one
from .schemas_auth import UserCreate, UserPatch


class UserPatchError(ValueError):
    """A user patch failed the API's field-level validation rules."""

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


def create_user(user: UserCreate) -> dict[str, Any]:
    password_hash = bcrypt.hashpw(
        user.password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "INSERT INTO users(email,password_hash,full_name,role) "
            "VALUES (%s,%s,%s,%s) RETURNING id,email,full_name,role",
            (user.email.strip(), password_hash, user.full_name.strip(), user.role),
        )
        created = cur.fetchone()
    return cast(dict[str, Any], created)


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


def update_user(user_id: UUID, patch: UserPatch) -> dict[str, Any] | None:
    values = patch.model_dump(exclude_unset=True)
    if not values:
        raise UserPatchError("At least one field is required")

    if "password" in values:
        password = values.pop("password")
        if password is None:
            raise UserPatchError("Password cannot be null")
        values["password_hash"] = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
    if "email" in values:
        if values["email"] is None:
            raise UserPatchError("Email cannot be null")
        values["email"] = values["email"].strip()
    if "full_name" in values:
        if values["full_name"] is None:
            raise UserPatchError("Full name cannot be null")
        values["full_name"] = values["full_name"].strip()
    if "role" in values and values["role"] is None:
        raise UserPatchError("Role cannot be null")

    columns = {
        "email": "email",
        "full_name": "full_name",
        "role": "role",
        "password_hash": "password_hash",
    }
    fields = list(values)
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            sql.SQL("UPDATE users SET {} WHERE id=%s RETURNING id,email,full_name,role").format(
                sql.SQL(",").join(
                    sql.SQL("{}=%s").format(sql.Identifier(columns[field]))
                    for field in fields
                )
            ),
            [values[field] for field in fields] + [user_id],
        )
        updated = cur.fetchone()
    return updated
