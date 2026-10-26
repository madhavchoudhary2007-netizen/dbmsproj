from collections.abc import Callable
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pymongo.collection import Collection

from ..database import DatabaseRow
from ..pit_repository import PIT_RESERVATION_SELECT


def race_lap_measurements(
    col: Collection[dict[str, Any]], match: dict[str, Any]
) -> list[dict[str, Any]]:
    # Collapse retries to one complete lap per driver, retaining the latest stored measurement.
    return list(
        col.aggregate(
            [
                {"$match": {**match, "sector": 3, "lap_time_ms": {"$gt": 0}}},
                {"$sort": {"ts": 1}},
                {
                    "$group": {
                        "_id": {"driver_id": "$driver_id", "lap": "$lap"},
                        "record": {"$last": "$$ROOT"},
                    }
                },
                {"$replaceRoot": {"newRoot": "$record"}},
                {"$project": {"_id": 0}},
                {"$sort": {"lap": 1, "position": 1}},
            ]
        )
    )


def create_laps_router(
    fetch_one: Callable[..., DatabaseRow | None],
    fetch_all: Callable[..., list[DatabaseRow]],
    jsonable: Callable[[Any], Any],
    mongo_ready: Callable[[], Collection[dict[str, Any]]],
    lap_measurements: Callable[[Collection[dict[str, Any]], dict[str, Any]], list[dict[str, Any]]],
    admin_dependency: Any,
    authenticated_user_dependency: Any,
) -> tuple[APIRouter, dict[str, Callable[..., Any]]]:
    router = APIRouter()
    race_lap_measurements = lap_measurements

    @router.get("/api/dbms/races/{session_id}/laps")
    def dbms_race_laps(session_id: UUID, user: Any = admin_dependency) -> Any:
        session = fetch_one(
            "SELECT id FROM race_sessions WHERE id=%s AND session_type='RACE'", (session_id,)
        )
        if not session:
            raise HTTPException(404, "Race not found")
        col = mongo_ready()
        match = {"session_id": str(session_id)}
        laps = race_lap_measurements(col, match)
        source = (
            "historical_demo"
            if laps and all(x.get("source") == "historical_demo" for x in laps)
            else "recorded_telemetry"
        )
        return jsonable({"session_id": session_id, "laps": laps, "lap_source": source})

    @router.get("/api/sessions/{session_id}/laps")
    def session_laps(session_id: UUID, user: Any = authenticated_user_dependency) -> Any:
        session = fetch_one("SELECT id FROM race_sessions WHERE id=%s", (session_id,))
        if not session:
            raise HTTPException(404, "Session not found")
        laps = race_lap_measurements(mongo_ready(), {"session_id": str(session_id)})
        incidents = fetch_all(
            """SELECT i.*,u.full_name AS driver_name FROM incident_reports i
        JOIN drivers d ON d.id=i.driver_id JOIN users u ON u.id=d.user_id
        WHERE i.session_id=%s ORDER BY i.lap,i.id""",
            (session_id,),
        )
        stops = fetch_all(
            PIT_RESERVATION_SELECT + " WHERE r.session_id=%s ORDER BY r.starts_at", (session_id,)
        )
        return jsonable(
            {
                "session_id": session_id,
                "laps": laps,
                "incidents": incidents,
                "pit_reservations": stops,
            }
        )

    return router, {"dbms_race_laps": dbms_race_laps, "session_laps": session_laps}
