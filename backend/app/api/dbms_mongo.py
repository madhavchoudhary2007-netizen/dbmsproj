from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pymongo import DESCENDING
from pymongo.collection import Collection
from pymongo.errors import PyMongoError


def create_dbms_mongo_router(
    fetch_one: Callable[..., Any],
    jsonable: Callable[[Any], Any],
    mongo_ready: Callable[[], Collection[dict[str, Any]]],
    admin_dependency: Any,
) -> tuple[APIRouter, dict[str, Callable[..., Any]]]:
    router = APIRouter()

    @router.get("/api/dbms/overview")
    def dbms_overview(user=admin_dependency):
        counts = fetch_one("""SELECT
      (SELECT count(*) FROM race_sessions WHERE state='ACTIVE') AS active_sessions,
      (SELECT count(*) FROM race_sessions WHERE state='COMPLETED') AS completed_sessions,
      (SELECT count(*) FROM incident_reports WHERE state='OPEN') AS open_incidents,
      (SELECT count(*) FROM pit_reservations WHERE status='RESERVED') AS reserved_pit_stops,
      (SELECT count(*) FROM pit_reservations WHERE status='COMPLETED') AS completed_pit_stops,
      (SELECT count(*) FROM session_results) AS official_results""")
        try:
            telemetry_samples = mongo_ready().count_documents({})
            mongo_status = "up"
        except (HTTPException, PyMongoError):
            telemetry_samples = None
            mongo_status = "down"
        return jsonable(
            {
                **counts,
                "telemetry_samples": telemetry_samples,
                "postgres": "up",
                "mongodb": mongo_status,
                "updated_at": datetime.now(UTC),
            }
        )

    @router.get("/api/dbms/telemetry")
    def dbms_telemetry(user=admin_dependency):
        try:
            col = mongo_ready()
            return {
                "store": "MongoDB",
                "count": col.count_documents({}),
                "indexes": list(col.index_information().keys()),
                "sample": jsonable(list(col.find({}, {"_id": 0}).sort("ts", DESCENDING).limit(3))),
            }
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(503, "Could not inspect MongoDB telemetry") from exc

    return router, {"dbms_overview": dbms_overview, "dbms_telemetry": dbms_telemetry}
