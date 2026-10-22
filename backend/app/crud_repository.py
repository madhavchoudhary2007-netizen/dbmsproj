from typing import cast
from uuid import UUID

from psycopg.rows import dict_row

from .database import DatabaseRow, connection, fetch_all, fetch_one


def list_crud_rows(base: str, limit: int, offset: int) -> list[DatabaseRow]:
    """Return a page of CRUD rows using the route's existing projection."""
    return fetch_all(base + " ORDER BY 1 LIMIT %s OFFSET %s", (limit, offset))


def get_crud_row(base: str, table: str, item_id: UUID) -> DatabaseRow | None:
    """Return one CRUD row by identifier, if it exists."""
    return cast(DatabaseRow | None, fetch_one(base + " WHERE " + table + ".id=%s", (item_id,)))


def create_crud_row(table: str, values: dict[str, object]) -> DatabaseRow:
    """Insert one CRUD row and create default pit boxes for a race event."""
    keys = list(values)
    sql = (
        f"INSERT INTO {table} ({','.join(keys)}) "
        f"VALUES ({','.join(['%s'] * len(keys))}) RETURNING *"
    )
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, [values[key] for key in keys])
        row = cast(DatabaseRow, cur.fetchone())
        if table == "race_events":
            cur.execute(
                "INSERT INTO pit_boxes(event_id,number) SELECT %s,n FROM generate_series(1,4) AS n "
                "ON CONFLICT(event_id,number) DO NOTHING",
                (row["id"],),
            )
    return row


def update_crud_row(table: str, item_id: UUID, values: dict[str, object]) -> DatabaseRow | None:
    """Update one CRUD row by identifier, returning the updated row when present."""
    keys = list(values)
    sql = (
        f"UPDATE {table} SET " + ",".join(f"{key}=%s" for key in keys) + " WHERE id=%s RETURNING *"
    )
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, [values[key] for key in keys] + [item_id])
        return cast(DatabaseRow | None, cur.fetchone())
