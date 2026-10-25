from __future__ import annotations

from typing import Any, cast
from uuid import UUID

from psycopg import sql
from psycopg.rows import dict_row

from .core.request_database import DatabaseSession
from .schemas_competition import MembershipIn, MembershipPatch


def list_driver_memberships(driver_id: UUID, database: DatabaseSession) -> list[dict[str, Any]]:
    query = (
        "SELECT m.*,t.name AS team_name FROM team_memberships m "
        "JOIN teams t ON t.id=m.team_id WHERE m.driver_id=%s "
        "ORDER BY m.start_date DESC"
    )
    params = (driver_id,)
    return database.fetch_all(query, params)


def list_team_memberships(team_id: UUID, database: DatabaseSession) -> list[dict[str, Any]]:
    query = (
        "SELECT m.*,u.full_name AS driver_name,d.number,d.licence_number "
        "FROM team_memberships m JOIN drivers d ON d.id=m.driver_id "
        "LEFT JOIN users u ON u.id=d.user_id WHERE m.team_id=%s "
        "ORDER BY m.start_date DESC"
    )
    params = (team_id,)
    return database.fetch_all(query, params)


def create_membership(membership: MembershipIn, database: DatabaseSession) -> dict[str, Any]:
    with database.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "INSERT INTO team_memberships(driver_id,team_id,start_date,end_date) "
            "VALUES (%s,%s,%s,%s) RETURNING *",
            (
                membership.driver_id,
                membership.team_id,
                membership.start_date,
                membership.end_date,
            ),
        )
        row = cur.fetchone()
    return cast(dict[str, Any], row)


def update_membership(
    membership_id: UUID,
    patch: MembershipPatch,
    database: DatabaseSession,
) -> dict[str, Any] | None:
    values = patch.model_dump(exclude_unset=True)
    columns = {"team_id": "team_id", "start_date": "start_date", "end_date": "end_date"}
    fields = list(values)
    statement = sql.SQL("UPDATE team_memberships SET {} WHERE id=%s RETURNING *").format(
        sql.SQL(",").join(
            sql.SQL("{}=%s").format(sql.Identifier(columns[field])) for field in fields
        )
    )
    with database.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(statement, [values[field] for field in fields] + [membership_id])
        row = cur.fetchone()
    return row
