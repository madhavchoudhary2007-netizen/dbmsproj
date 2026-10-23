from datetime import datetime
from threading import RLock
from typing import Any, Literal, cast
from uuid import UUID

from pymongo import DESCENDING
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from .database import connection, fetch_all, fetch_one

TelemetryIngestOutcome = Literal[
    "session_not_found", "session_inactive", "driver_not_found", "write_failed",
    "out_of_order",
]

_telemetry_ingest_lock = RLock()


class TelemetryIngestResult:
    def __init__(self, document: dict[str, Any], inserted: bool):
        self.document = document
        self.inserted = inserted
        self.inserted_id = document["_id"]


class TelemetryIngestError(Exception):
    def __init__(self, outcome: TelemetryIngestOutcome):
        self.outcome = outcome
        super().__init__(outcome)


def insert_telemetry(
    collection: Collection[dict[str, Any]],
    session_id: UUID,
    driver_id: UUID,
    document: dict[str, Any],
) -> TelemetryIngestResult:
    """Validate references, then ingest one ordered, idempotent packet."""
    with _telemetry_ingest_lock:
        with connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT state FROM race_sessions WHERE id=%s FOR SHARE", (session_id,))
            session = cur.fetchone()
            if not session:
                raise TelemetryIngestError("session_not_found")
            if session["state"] != "ACTIVE":
                raise TelemetryIngestError("session_inactive")
            cur.execute("SELECT 1 FROM drivers WHERE id=%s", (driver_id,))
            if not cur.fetchone():
                raise TelemetryIngestError("driver_not_found")
        query = {"session_id": str(session_id), "driver_id": str(driver_id)}
        try:
            existing = list(collection.find(query))
            latest = max(
                existing,
                key=lambda row: (
                    row.get("lap", -1), row.get("sector", -1),
                    row.get("elapsed_ms", -1),
                ),
                default=None,
            )
            if latest is not None:
                if {key: value for key, value in latest.items() if key != "_id"} == document:
                    return TelemetryIngestResult(latest, False)
                previous_position = (latest.get("lap", -1), latest.get("sector", -1))
                incoming_position = (document["lap"], document["sector"])
                if (
                    incoming_position <= previous_position
                    or document["elapsed_ms"] <= latest.get("elapsed_ms", -1)
                ):
                    raise TelemetryIngestError("out_of_order")
            result = collection.insert_one(document)
            return TelemetryIngestResult(
                {**document, "_id": result.inserted_id}, True
            )
        except TelemetryIngestError:
            raise
        except PyMongoError as exc:
            raise TelemetryIngestError("write_failed") from exc


def session_exists(session_id: UUID) -> bool:
    return fetch_one("SELECT 1 FROM race_sessions WHERE id=%s", (session_id,)) is not None


def driver_exists(driver_id: UUID) -> bool:
    return fetch_one("SELECT 1 FROM drivers WHERE id=%s", (driver_id,)) is not None


def list_telemetry(
    collection: Collection[dict[str, Any]],
    session_id: UUID,
    driver_id: UUID | None,
    limit: int,
) -> list[dict[str, Any]]:
    query: dict[str, str] = {"session_id": str(session_id)}
    if driver_id is not None:
        query["driver_id"] = str(driver_id)
    return list(collection.find(query).sort("ts", DESCENDING).limit(limit))


def get_live_session(session_id: UUID) -> dict[str, Any] | None:
    return cast(
        dict[str, Any] | None,
        fetch_one("SELECT * FROM race_sessions WHERE id=%s", (session_id,)),
    )


def get_live_telemetry(
    collection: Collection[dict[str, Any]],
    session_id: UUID,
    scheduled_at: datetime,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    latest = list(
        collection.find({"session_id": str(session_id)})
        .sort("ts", DESCENDING)
        .limit(100)
    )
    latest.reverse()
    driver_ids = {str(doc["driver_id"]) for doc in latest if doc.get("driver_id")}
    driver_ids.update(
        str(row["driver_id"])
        for row in fetch_all(
            "SELECT driver_id FROM demo_race_entries WHERE session_id=%s "
            "UNION SELECT driver_id FROM session_results WHERE session_id=%s",
            (session_id, session_id),
        )
    )
    drivers = (
        fetch_all(
            """SELECT d.id,d.number,d.licence_number,u.full_name,t.name AS team_name
            FROM drivers d LEFT JOIN users u ON u.id=d.user_id
            LEFT JOIN LATERAL (SELECT team_id FROM team_memberships m WHERE m.driver_id=d.id
              AND m.start_date<=%s::date AND (m.end_date IS NULL OR m.end_date>=%s::date)
              ORDER BY m.start_date DESC LIMIT 1) membership ON true
            LEFT JOIN teams t ON t.id=membership.team_id WHERE d.id=ANY(%s::uuid[]) ORDER BY d.number""",
            (scheduled_at, scheduled_at, list(driver_ids)),
        )
        if driver_ids
        else []
    )
    return latest, drivers
