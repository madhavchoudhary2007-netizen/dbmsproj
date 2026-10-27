from __future__ import annotations

from uuid import UUID

import pytest
from app.api import laps, race_archive
from fastapi import HTTPException

SESSION_ID = UUID("00000000-0000-0000-0000-000000000101")
DRIVER_A = "00000000-0000-0000-0000-000000000201"
DRIVER_B = "00000000-0000-0000-0000-000000000202"


class InMemoryTelemetry:
    def __init__(self, lap_rows=None, latest_rows=None, completed_count=0):
        self.lap_rows = lap_rows or []
        self.latest_rows = latest_rows or []
        self.completed_count = completed_count
        self.pipelines = []
        self.find_queries = []
        self.count_queries = []

    def aggregate(self, pipeline):
        self.pipelines.append(pipeline)
        if pipeline[-1] == {"$count": "count"}:
            return [{"count": self.completed_count}] if self.completed_count else []
        if any(
            "$group" in stage and stage["$group"].get("_id") == "$driver_id" for stage in pipeline
        ):
            return list(self.latest_rows)
        return list(self.lap_rows)

    def find_one(self, query, projection=None):
        self.find_queries.append((query, projection))
        return None

    def count_documents(self, query):
        self.count_queries.append(query)
        return len(self.latest_rows) + len(self.lap_rows)


def archive_handler(session=None, results=None, telemetry=None):
    telemetry = telemetry or InMemoryTelemetry()
    queries = []

    def fetch_one(sql, params):
        queries.append((sql, params))
        return session

    def fetch_all(sql, params):
        queries.append((sql, params))
        if "session_results" in sql:
            return [dict(row) for row in (results or [])]
        if "WHERE d.id=ANY" in sql:
            ids = params[0]
            return [
                {"id": driver_id, "driver_name": f"Driver {driver_id[-1]}"} for driver_id in ids
            ]
        return []

    _router, handlers = race_archive.create_race_archive_router(
        fetch_one,
        fetch_all,
        lambda value: value,
        lambda: telemetry,
        laps.race_lap_measurements,
        lambda: {"role": "ADMIN"},
    )
    return handlers["dbms_race"], telemetry, queries


def test_completed_archive_returns_session_scoped_sorted_laps_and_driver_latest():
    lap_rows = [
        {
            "session_id": str(SESSION_ID),
            "driver_id": DRIVER_A,
            "lap": 1,
            "position": 1,
            "lap_time_ms": 85000,
        },
        {
            "session_id": str(SESSION_ID),
            "driver_id": DRIVER_B,
            "lap": 2,
            "position": 2,
            "lap_time_ms": 87000,
        },
    ]
    latest_rows = [
        {"session_id": str(SESSION_ID), "driver_id": DRIVER_B, "position": 2, "ts": 20},
        {"session_id": str(SESSION_ID), "driver_id": DRIVER_A, "position": 1, "ts": 21},
    ]
    handler, telemetry, _queries = archive_handler(
        session={"id": str(SESSION_ID), "state": "COMPLETED"},
        results=[{"driver_id": DRIVER_A, "position": 1}],
        telemetry=InMemoryTelemetry(lap_rows, latest_rows, completed_count=2),
    )

    body = handler(SESSION_ID)

    assert body["laps"] == lap_rows
    assert body["latest"] == [latest_rows[1], latest_rows[0]]
    assert body["completed_driver_laps"] == 2
    assert body["laps_included"] is True
    assert body["lap_source"] == "recorded_telemetry"
    assert body["telemetry_count"] == 4
    assert telemetry.pipelines[0][0] == {
        "$match": {"session_id": str(SESSION_ID), "sector": 3, "lap_time_ms": {"$gt": 0}}
    }
    assert telemetry.pipelines[0][1] == {"$sort": {"ts": 1}}
    assert telemetry.pipelines[0][-1] == {"$sort": {"lap": 1, "position": 1}}
    assert telemetry.pipelines[1][0] == {"$match": {"session_id": str(SESSION_ID)}}
    assert telemetry.count_queries == [{"session_id": str(SESSION_ID)}]


def test_live_archive_can_skip_lap_history_but_still_report_completed_count():
    latest_rows = [{"session_id": str(SESSION_ID), "driver_id": DRIVER_A, "position": 1, "ts": 30}]
    handler, telemetry, _queries = archive_handler(
        session={"id": str(SESSION_ID), "state": "ACTIVE"},
        telemetry=InMemoryTelemetry(latest_rows=latest_rows, completed_count=3),
    )

    body = handler(SESSION_ID, include_laps=False)

    assert body["laps"] == []
    assert body["laps_included"] is False
    assert body["latest"] == latest_rows
    assert body["completed_driver_laps"] == 3
    assert body["lap_source"] == "recorded_telemetry"
    assert len(telemetry.pipelines) == 2
    assert telemetry.find_queries == [
        (
            {
                "session_id": str(SESSION_ID),
                "sector": 3,
                "lap_time_ms": {"$gt": 0},
                "source": "historical_demo",
            },
            {"_id": 1},
        )
    ]


def test_empty_completed_archive_has_zero_laps_and_recorded_source():
    handler, telemetry, _queries = archive_handler(
        session={"id": str(SESSION_ID), "state": "COMPLETED"}
    )

    body = handler(SESSION_ID)

    assert body["laps"] == []
    assert body["latest"] == []
    assert body["completed_driver_laps"] == 0
    assert body["drivers"] == []
    assert body["lap_source"] == "recorded_telemetry"
    assert telemetry.count_queries == [{"session_id": str(SESSION_ID)}]


def test_missing_race_returns_404_before_reading_telemetry():
    handler, telemetry, _queries = archive_handler(session=None)

    with pytest.raises(HTTPException) as error:
        handler(SESSION_ID)

    assert error.value.status_code == 404
    assert error.value.detail == "Race not found"
    assert telemetry.pipelines == []
    assert telemetry.count_queries == []


def test_latest_driver_telemetry_fallback_is_driver_scoped_and_position_sorted():
    class FindOneCollection:
        def __init__(self):
            self.find_calls = []

        def distinct(self, field, match):
            assert field == "driver_id"
            assert match == {"session_id": str(SESSION_ID)}
            return [DRIVER_B, DRIVER_A]

        def find_one(self, query, projection=None, sort=None):
            self.find_calls.append((query, projection, sort))
            position = 2 if query["driver_id"] == DRIVER_B else 1
            return {"driver_id": query["driver_id"], "position": position, "ts": 99}

        def aggregate(self, pipeline):
            raise RuntimeError("aggregation fallback exercised")

    collection = FindOneCollection()

    latest = race_archive.latest_driver_telemetry(collection, {"session_id": str(SESSION_ID)})

    assert [row["driver_id"] for row in latest] == [DRIVER_A, DRIVER_B]
    assert collection.find_calls == [
        ({"session_id": str(SESSION_ID), "driver_id": DRIVER_B}, None, [("ts", -1)]),
        ({"session_id": str(SESSION_ID), "driver_id": DRIVER_A}, None, [("ts", -1)]),
    ]
