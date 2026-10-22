from __future__ import annotations

from typing import Any
from uuid import UUID

from .database import fetch_all

PIT_RESERVATION_SELECT = """SELECT r.*,b.number AS box_number,t.name AS team_name,
    d.full_name AS driver_name,dr.number AS driver_number
    FROM pit_reservations r JOIN pit_boxes b ON b.id=r.pit_box_id
    JOIN teams t ON t.id=r.team_id LEFT JOIN drivers dr ON dr.id=r.driver_id
    LEFT JOIN users d ON d.id=dr.user_id"""


def list_pit_boxes(event_id: UUID) -> list[dict[str, Any]]:
    return fetch_all("""SELECT b.*,r.id AS reservation_id,r.session_id,r.driver_id,r.allocation_source,
        r.starts_at,r.ends_at,r.status,t.name AS team_name,du.full_name AS driver_name,d.number AS driver_number
        FROM pit_boxes b
        LEFT JOIN LATERAL (SELECT pr.* FROM pit_reservations pr WHERE pr.pit_box_id=b.id AND pr.status='RESERVED'
          AND pr.ends_at>now() ORDER BY (pr.starts_at<=now()) DESC,pr.starts_at LIMIT 1) r ON TRUE
        LEFT JOIN teams t ON t.id=r.team_id LEFT JOIN drivers d ON d.id=r.driver_id
        LEFT JOIN users du ON du.id=d.user_id WHERE b.event_id=%s ORDER BY b.number""", (event_id,))


def list_pit_reservations(session_id: UUID) -> list[dict[str, Any]]:
    return fetch_all(
        PIT_RESERVATION_SELECT + " WHERE r.session_id=%s ORDER BY r.starts_at", (session_id,)
    )
