from __future__ import annotations

from typing import Any
from uuid import UUID

from pymongo.collection import Collection

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


def load_pit_telemetry(
    collection: Collection[dict[str, Any]], session_id: UUID
) -> tuple[dict[str, dict[str, Any]], dict[str, int], dict[str, str]]:
    latest_by_driver: dict[str, dict[str, Any]] = {}
    stop_lap_by_reservation: dict[str, int] = {}
    stop_compound_by_reservation: dict[str, str] = {}
    session_key = str(session_id)

    # Keep the live sample scan bounded while recording each driver's newest packet.
    for packet in collection.find({"session_id": session_key}).sort("ts", -1).limit(2000):
        driver_id = str(packet.get("driver_id", ""))
        if driver_id and driver_id not in latest_by_driver:
            latest_by_driver[driver_id] = packet
        reservation_id = packet.get("pit_reservation_id")
        if reservation_id and packet.get("pit_state") in {"IN_PIT", "PIT", "BOX"}:
            stop_lap_by_reservation.setdefault(str(reservation_id), int(packet.get("lap") or 0))

    # This aggregation recovers the first stop sample even when it predates the scan.
    for stop in collection.aggregate([
        {"$match": {"session_id": session_key, "pit_reservation_id": {"$exists": True},
            "pit_state": {"$in": ["IN_PIT", "PIT", "BOX"]}}},
        {"$sort": {"ts": 1}},
        {"$group": {"_id": "$pit_reservation_id", "lap": {"$first": "$lap"},
            "compound": {"$first": "$tire_compound"}}},
    ]):
        reservation_id = str(stop["_id"])
        if stop.get("lap") is not None:
            stop_lap_by_reservation[reservation_id] = int(stop["lap"])
        if stop.get("compound"):
            stop_compound_by_reservation[reservation_id] = stop["compound"]
    return latest_by_driver, stop_lap_by_reservation, stop_compound_by_reservation
