from typing import Any
from uuid import UUID

from .database import fetch_all, fetch_one


def list_crud_rows(base: str, limit: int, offset: int) -> list[dict[str, Any]]:
    """Return a page of CRUD rows using the route's existing projection."""
    return fetch_all(base + " ORDER BY 1 LIMIT %s OFFSET %s", (limit, offset))


def get_crud_row(base: str, table: str, item_id: UUID) -> dict[str, Any] | None:
    """Return one CRUD row by identifier, if it exists."""
    return fetch_one(base + " WHERE " + table + ".id=%s", (item_id,))
