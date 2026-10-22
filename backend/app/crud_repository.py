from typing import Any, cast
from uuid import UUID

from psycopg.rows import dict_row

from .database import DatabaseRow, connection, fetch_all, fetch_one


class CrudDeleteError(Exception):
    """A delete could not complete and should be mapped at the API boundary."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


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


def _ensure_no_reference(cur: Any, query: str, params: tuple[UUID, ...]) -> None:
    cur.execute(query, params)
    if cur.fetchone():
        raise CrudDeleteError(409, "Resource is referenced by official records")


def _check_session_delete(cur: Any, item_id: UUID, telemetry_collection: object | None) -> None:
    cur.execute("SELECT state FROM race_sessions WHERE id=%s", (item_id,))
    existing = cur.fetchone()
    if existing and existing["state"] in ("ACTIVE", "PAUSED"):
        raise CrudDeleteError(409, "Finish or cancel an active session before deleting it")
    cur.execute("SELECT 1 FROM demo_races WHERE session_id=%s", (item_id,))
    if cur.fetchone():
        raise CrudDeleteError(409, "Generated races must be removed through the demo-race endpoint")
    if telemetry_collection is None:
        raise CrudDeleteError(503, "MongoDB telemetry store is unavailable")
    count_documents = getattr(telemetry_collection, "count_documents")
    if count_documents({"session_id": str(item_id)}, limit=1):
        raise CrudDeleteError(409, "Session has telemetry records and cannot be deleted")
    _ensure_no_reference(
        cur,
        "SELECT 1 FROM incident_reports WHERE session_id=%s UNION ALL "
        "SELECT 1 FROM pit_reservations WHERE session_id=%s LIMIT 1",
        (item_id, item_id),
    )


def _check_special_delete_reference(cur: Any, table: str, item_id: UUID) -> None:
    checks = {
        "drivers": (
            "SELECT 1 FROM incident_reports WHERE driver_id=%s UNION ALL "
            "SELECT 1 FROM team_memberships WHERE driver_id=%s LIMIT 1",
            (item_id, item_id),
        ),
        "teams": ("SELECT 1 FROM pit_reservations WHERE team_id=%s LIMIT 1", (item_id,)),
        "race_events": (
            "SELECT 1 FROM pit_reservations p JOIN pit_boxes b ON b.id=p.pit_box_id "
            "WHERE b.event_id=%s LIMIT 1",
            (item_id,),
        ),
    }
    check = checks.get(table)
    if check:
        _ensure_no_reference(cur, *check)


def delete_crud_row(
    table: str, resource: str, item_id: UUID, telemetry_collection: object | None
) -> None:
    """Delete one CRUD row after checking its official and runtime dependencies."""
    dependencies = {
        "championships": ("race_events", "championship_id"),
        "circuits": ("race_events", "circuit_id"),
        "teams": ("team_memberships", "team_id"),
        "drivers": ("session_results", "driver_id"),
        "race_events": ("race_sessions", "event_id"),
        "race_sessions": ("session_results", "session_id"),
    }
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        child = dependencies.get(table)
        if child:
            child_table, foreign_key = child
            _ensure_no_reference(
                cur,
                f"SELECT 1 FROM {child_table} WHERE {foreign_key}=%s LIMIT 1",
                (item_id,),
            )
        if table == "race_sessions":
            _check_session_delete(cur, item_id, telemetry_collection)
        else:
            _check_special_delete_reference(cur, table, item_id)
        if table == "race_events":
            cur.execute("DELETE FROM pit_boxes WHERE event_id=%s", (item_id,))
        cur.execute(f"DELETE FROM {table} WHERE id=%s", (item_id,))
        if cur.rowcount == 0:
            raise CrudDeleteError(404, f"{resource[:-1].capitalize()} not found")
