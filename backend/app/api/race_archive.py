from __future__ import annotations

from collections.abc import Callable
from contextlib import suppress
from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pymongo import DESCENDING
from pymongo.collection import Collection

from ..core.request_database import DatabaseRow, DatabaseSession
from ..core.serialization import jsonable
from ..pit_repository import PIT_RESERVATION_SELECT
from .laps import (
    admin,
    get_race_db,
    get_race_telemetry,
    race_lap_measurements,
)

router = APIRouter()
race_archive_router = router


def latest_driver_telemetry(col: Any, match: dict[str, Any]) -> list[dict[str, Any]]:
    latest_rows: list[dict[str, Any]] = []
    if hasattr(col, "aggregate"):
        with suppress(Exception):
            cursor = col.aggregate(
                [
                    {"$match": match},
                    {"$sort": {"ts": -1}},
                    {"$group": {"_id": "$driver_id", "latest_doc": {"$first": "$$ROOT"}}},
                    {"$replaceRoot": {"newRoot": "$latest_doc"}},
                ]
            )
            latest_rows = [row for row in cursor if row]
            return sorted(
                latest_rows, key=lambda r: (r.get("position") is None, r.get("position") or 0)
            )

    driver_ids: list[Any] = []
    with suppress(Exception):
        driver_ids = col.distinct("driver_id", match)
    for driver_id in driver_ids:
        with suppress(Exception):
            row = col.find_one({**match, "driver_id": driver_id}, sort=[("ts", DESCENDING)])
            if row:
                latest_rows.append(row)
    return sorted(latest_rows, key=lambda r: (r.get("position") is None, r.get("position") or 0))


@router.get("/api/dbms/races/{session_id}")
def dbms_race(
    session_id: UUID,
    database: Annotated[DatabaseSession, Depends(get_race_db)],
    col: Annotated[Collection[dict[str, Any]], Depends(get_race_telemetry)],
    user: Annotated[dict[str, Any], Depends(admin)],
    include_laps: bool = True,
) -> Any:
    session = database.fetch_one(
        (
            "SELECT s.*,e.name AS event_name,c.name AS circuit_name FROM race_sessions s "
            "JOIN race_events e ON e.id=s.event_id JOIN circuits c ON c.id=e.circuit_id "
            "WHERE s.id=%s AND s.session_type='RACE'"
        ),
        (session_id,),
    )
    if not session:
        raise HTTPException(404, "Race not found")
    results = database.fetch_all(
        (
            "SELECT r.*,u.full_name AS driver_name,d.number,d.licence_number FROM session_"
            "results"
            " r\n      JOIN drivers d ON d.id=r.driver_id LEFT JOIN users u ON u.id=d.user_id "
            "WHE"
            "RE r.session_id=%s ORDER BY r.position NULLS LAST"
        ),
        (session_id,),
    )
    incidents = database.fetch_all(
        """SELECT i.*,u.full_name AS driver_name FROM incident_reports i
  JOIN drivers d ON d.id=i.driver_id JOIN users u ON u.id=d.user_id
  WHERE i.session_id=%s ORDER BY i.lap,i.id""",
        (session_id,),
    )
    penalties = database.fetch_all(
        (
            "SELECT p.* FROM penalties p JOIN incident_reports i ON i.id=p.incident_id WHERE i."
            "se"
            "ssion_id=%s"
        ),
        (session_id,),
    )
    provisional = session["state"] == "COMPLETED" and any(
        (penalty.get("time_seconds") or 0) > 0 or (penalty.get("grid_places") or 0) > 0
        for penalty in penalties
    )
    for result in results:
        result["provisional"] = provisional
    reservations = database.fetch_all(
        PIT_RESERVATION_SELECT + " WHERE r.session_id=%s ORDER BY r.starts_at", (session_id,)
    )
    match = {"session_id": str(session_id)}
    # Full lap history is optional for the 1s live poll; it grows with every race lap.
    laps = race_lap_measurements(col, match) if include_laps else []
    latest_rows = latest_driver_telemetry(col, match)
    ids = {row["driver_id"] for row in latest_rows} | {str(row["driver_id"]) for row in results}
    drivers = (
        database.fetch_all(
            (
                "SELECT d.id,d.number,d.licence_number,u.full_name AS driver_name FROM drivers "
                "d "
                "LEFT JOIN users u ON u.id=d.user_id WHERE d.id=ANY(%s::uuid[])"
            ),
            (list(ids),),
        )
        if ids
        else []
    )
    if include_laps:
        lap_source = (
            "historical_demo"
            if laps and all(x.get("source") == "historical_demo" for x in laps)
            else "recorded_telemetry"
        )
    else:
        lap_source = (
            "historical_demo"
            if col.find_one(
                {**match, "sector": 3, "lap_time_ms": {"$gt": 0}, "source": "historical_demo"},
                {"_id": 1},
            )
            else "recorded_telemetry"
        )
    completed_count = list(
        col.aggregate(
            [
                {"$match": {**match, "sector": 3, "lap_time_ms": {"$gt": 0}}},
                {"$group": {"_id": {"driver_id": "$driver_id", "lap": "$lap"}}},
                {"$count": "count"},
            ]
        )
    )
    return jsonable(
        {
            "session": session,
            "results": results,
            "incidents": incidents,
            "penalties": penalties,
            "pit_reservations": reservations,
            "drivers": drivers,
            "laps": laps,
            "laps_included": include_laps,
            "completed_driver_laps": completed_count[0]["count"] if completed_count else 0,
            "latest": latest_rows,
            "telemetry_count": col.count_documents(match),
            "updated_at": datetime.now(UTC),
            "lap_source": lap_source,
        }
    )


def create_race_archive_router(
    fetch_one: Callable[..., DatabaseRow | None],
    fetch_all: Callable[..., list[DatabaseRow]],
    jsonable: Callable[[Any], Any],
    mongo_ready: Callable[[], Collection[dict[str, Any]]],
    race_lap_measurements: Callable[
        [Collection[dict[str, Any]], dict[str, Any]], list[dict[str, Any]]
    ],
    admin_dependency: Any,
) -> tuple[APIRouter, dict[str, Callable[..., Any]]]:
    rt = APIRouter()

    @rt.get("/api/dbms/races/{session_id}")
    def dbms_race(session_id: UUID, include_laps: bool = True, user: Any = admin_dependency) -> Any:
        session = fetch_one(
            (
                "SELECT s.*,e.name AS event_name,c.name AS circuit_"
                "name FROM race_sessions s\n      J"
                "OIN race_events e ON e.id=s.event_id JOIN circuits c ON c.id=e.circuit_id WHERE s."
                "id"
                "=%s AND s.session_type='RACE'"
            ),
            (session_id,),
        )
        if not session:
            raise HTTPException(404, "Race not found")
        results = fetch_all(
            (
                "SELECT r.*,u.full_name AS driver_name,d.number,d.licence_number FROM session_"
                "results"
                " r\n      JOIN drivers d ON d.id=r.driver_id LEFT JOIN users u ON u.id=d.user_id "
                "WHE"
                "RE r.session_id=%s ORDER BY r.position NULLS LAST"
            ),
            (session_id,),
        )
        incidents = fetch_all(
            """SELECT i.*,u.full_name AS driver_name FROM incident_reports i
      JOIN drivers d ON d.id=i.driver_id JOIN users u ON u.id=d.user_id
      WHERE i.session_id=%s ORDER BY i.lap,i.id""",
            (session_id,),
        )
        penalties = fetch_all(
            (
                "SELECT p.* FROM penalties p JOIN incident_reports i ON i.id=p.incident_id WHERE i."
                "se"
                "ssion_id=%s"
            ),
            (session_id,),
        )
        provisional = session["state"] == "COMPLETED" and any(
            (penalty.get("time_seconds") or 0) > 0 or (penalty.get("grid_places") or 0) > 0
            for penalty in penalties
        )
        for result in results:
            result["provisional"] = provisional
        reservations = fetch_all(
            PIT_RESERVATION_SELECT + " WHERE r.session_id=%s ORDER BY r.starts_at", (session_id,)
        )
        col = mongo_ready()
        match = {"session_id": str(session_id)}
        laps = race_lap_measurements(col, match) if include_laps else []
        latest_rows = latest_driver_telemetry(col, match)
        ids = {row["driver_id"] for row in latest_rows} | {str(row["driver_id"]) for row in results}
        drivers = (
            fetch_all(
                (
                    "SELECT d.id,d.number,d.licence_number,u.full_name AS driver_name FROM drivers "
                    "d "
                    "LEFT JOIN users u ON u.id=d.user_id WHERE d.id=ANY(%s::uuid[])"
                ),
                (list(ids),),
            )
            if ids
            else []
        )
        if include_laps:
            lap_source = (
                "historical_demo"
                if laps and all(x.get("source") == "historical_demo" for x in laps)
                else "recorded_telemetry"
            )
        else:
            lap_source = (
                "historical_demo"
                if col.find_one(
                    {**match, "sector": 3, "lap_time_ms": {"$gt": 0}, "source": "historical_demo"},
                    {"_id": 1},
                )
                else "recorded_telemetry"
            )
        completed_count = list(
            col.aggregate(
                [
                    {"$match": {**match, "sector": 3, "lap_time_ms": {"$gt": 0}}},
                    {"$group": {"_id": {"driver_id": "$driver_id", "lap": "$lap"}}},
                    {"$count": "count"},
                ]
            )
        )
        return jsonable(
            {
                "session": session,
                "results": results,
                "incidents": incidents,
                "penalties": penalties,
                "pit_reservations": reservations,
                "drivers": drivers,
                "laps": laps,
                "laps_included": include_laps,
                "completed_driver_laps": completed_count[0]["count"] if completed_count else 0,
                "latest": latest_rows,
                "telemetry_count": col.count_documents(match),
                "updated_at": datetime.now(UTC),
                "lap_source": lap_source,
            }
        )

    return rt, {"dbms_race": dbms_race}


__all__ = [
    "create_race_archive_router",
    "dbms_race",
    "race_archive_router",
    "router",
]
