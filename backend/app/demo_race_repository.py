from __future__ import annotations

from typing import Any, cast
from uuid import UUID

from .database import fetch_all, fetch_one


def get_demo_race_row(session_id: UUID | str) -> dict[str, Any] | None:
    return cast(
        dict[str, Any] | None,
        fetch_one(
            """SELECT s.id AS session_id,e.id AS event_id,e.name AS event_name,c.name AS circuit_name,
            s.state,s.total_laps,(SELECT count(*) FROM demo_race_entries de WHERE de.session_id=s.id)::int AS car_count,
            d.created_at FROM demo_races d JOIN race_sessions s ON s.id=d.session_id
            JOIN race_events e ON e.id=d.event_id JOIN circuits c ON c.id=e.circuit_id WHERE s.id=%s""",
            (session_id,),
        ),
    )


def list_demo_race_ids(limit: int, offset: int) -> list[dict[str, Any]]:
    return fetch_all(
        "SELECT session_id FROM demo_races ORDER BY created_at DESC LIMIT %s OFFSET %s",
        (limit, offset),
    )
