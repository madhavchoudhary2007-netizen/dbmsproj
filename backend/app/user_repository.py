from __future__ import annotations

from typing import Any, cast
from uuid import UUID

import bcrypt
from psycopg.rows import dict_row

from .database import connection, fetch_all, fetch_one
from .schemas_auth import UserCreate


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
