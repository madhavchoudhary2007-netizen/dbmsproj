"""Bounded SQL bridge for completed race-lap telemetry recorded in MongoDB."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

MAX_ANALYTICS_ROWS = 5_000

RECORDED_ELAPSED_QUERY = """
WITH recorded AS (
    SELECT source.driver_id, source.lap, source.lap_time_ms,
           source.elapsed_ms, source.source_position
    FROM jsonb_to_recordset(%s::jsonb) AS source(
        driver_id text, session_id text, lap integer, lap_time_ms bigint,
        elapsed_ms bigint, source_position integer
    )
    WHERE source.session_id = %s
), ranked AS (
    SELECT driver_id, lap,
           RANK() OVER (PARTITION BY lap ORDER BY elapsed_ms) AS position,
           elapsed_ms - FIRST_VALUE(elapsed_ms) OVER (
               PARTITION BY lap ORDER BY elapsed_ms, driver_id
           ) AS gap_to_leader_ms,
           elapsed_ms - LAG(elapsed_ms) OVER (
               PARTITION BY lap ORDER BY elapsed_ms, driver_id
           ) AS interval_ms,
           AVG(lap_time_ms) OVER (
               PARTITION BY driver_id ORDER BY lap
               ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
           ) AS rolling_avg_ms
    FROM recorded
)
SELECT driver_id, lap, position, gap_to_leader_ms, interval_ms, rolling_avg_ms
FROM ranked
ORDER BY lap, position, driver_id;
""".strip()


def recorded_elapsed_rows(
    records: Sequence[Mapping[str, Any]], session_id: str
) -> list[dict[str, Any]]:
    """Return valid completed observations, rejecting oversized source sets."""
    if len(records) > MAX_ANALYTICS_ROWS:
        raise OverflowError("Too many completed laps for analytics")

    rows: list[dict[str, Any]] = []
    for record in records:
        elapsed = record.get("elapsed_ms")
        lap = record.get("lap")
        lap_time = record.get("lap_time_ms")
        driver_id = record.get("driver_id")
        source_position = record.get("position")
        if (
            isinstance(elapsed, bool)
            or not isinstance(elapsed, int)
            or elapsed < 0
            or isinstance(lap, bool)
            or not isinstance(lap, int)
            or lap < 1
            or isinstance(lap_time, bool)
            or not isinstance(lap_time, int)
            or lap_time <= 0
            or driver_id is None
        ):
            continue
        rows.append(
            {
                "driver_id": str(driver_id),
                "session_id": session_id,
                "lap": lap,
                "lap_time_ms": lap_time,
                "elapsed_ms": elapsed,
                "source_position": source_position
                if isinstance(source_position, int) and not isinstance(source_position, bool)
                else None,
            }
        )
    return rows


def completed_lap_measurements(collection: Any, session_id: str) -> list[dict[str, Any]]:
    """Load the latest completed sector-three observation for each driver lap."""
    records = collection.aggregate(
        [
            {"$match": {"session_id": session_id, "sector": 3}},
            {"$sort": {"ts": 1}},
        ]
    )
    latest: dict[tuple[Any, Any], dict[str, Any]] = {}
    for index, record in enumerate(records):
        if index >= MAX_ANALYTICS_ROWS:
            raise OverflowError("Too many completed laps for analytics")
        lap_time = record.get("lap_time_ms")
        if record.get("sector") != 3 or not isinstance(lap_time, int) or lap_time <= 0:
            continue
        latest[(record.get("driver_id"), record.get("lap"))] = dict(record)
    return list(latest.values())


def serialize_recorded_rows(rows: Sequence[Mapping[str, Any]]) -> str:
    return json.dumps(rows, separators=(",", ":"))
