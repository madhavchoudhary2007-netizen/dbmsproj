from __future__ import annotations

from collections.abc import Callable
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from pymongo.errors import PyMongoError

from .pit_repository import PIT_RESERVATION_SELECT


def ensure_reset_allowed(session_id: UUID | str, fetch_one: Callable[..., Any]) -> None:
    row = fetch_one(
        """SELECT EXISTS(SELECT 1 FROM incident_reports i JOIN penalties p ON p.incident_id=i.id
        WHERE i.session_id=s.id) AS has_penalties FROM race_sessions s WHERE s.id=%s""",
        (session_id,),
    )
    if not row:
        raise HTTPException(404, "Session not found")
    if row["has_penalties"]:
        raise HTTPException(409, "A session with official penalties cannot be reset")


def clear_measurements(
    session_id: UUID | str,
    mongo_ready: Callable[..., Any],
    connection: Callable[..., Any],
    publish: Callable[..., Any],
) -> None:
    """Clear stored measurements after an explicit reset, preserving penalty history."""
    col = mongo_ready()
    cancelled = []
    with connection() as conn, conn.cursor() as cur:
        cur.execute(
            """SELECT e.championship_id,
            EXISTS(SELECT 1 FROM incident_reports i JOIN penalties p ON """
            """p.incident_id=i.id WHERE i.session_id=s.id) AS has_penalties
            FROM race_sessions s JOIN race_events e ON e.id=s.event_id WHERE s.id=%s""",
            (session_id,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Session not found")
        championship_id = row["championship_id"]
        if row["has_penalties"]:
            raise HTTPException(409, "A session with official penalties cannot be reset")
        try:
            col.delete_many({"session_id": str(session_id)})
        except PyMongoError as exc:
            raise HTTPException(503, "Telemetry store reset failed") from exc
        cur.execute("DELETE FROM session_results WHERE session_id=%s", (session_id,))
        cur.execute("SELECT recalculate_standings(%s)", (championship_id,))
        cur.execute(
            (
                "UPDATE pit_reservations SET status='CANCELLED'\n            WHERE session_id=%s "
                "AND allocation_source='AUTOMATIC' AND status='RESERVED' RETURNING id"
            ),
            (session_id,),
        )
        cancelled_ids = [item["id"] for item in cur.fetchall()]
        if cancelled_ids:
            cur.execute(PIT_RESERVATION_SELECT + " WHERE r.id=ANY(%s)", (cancelled_ids,))
            cancelled = cur.fetchall()
        cur.execute(
            "DELETE FROM pit_reservations WHERE session_id=%s AND allocation_source='AUTOMATIC'",
            (session_id,),
        )
    for reservation in cancelled:
        publish(session_id, "pit.update", reservation)
