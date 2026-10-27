from __future__ import annotations

from collections.abc import Iterator
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from typing import Any

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

_prior_app_env = os.environ.get("APP_ENV")
os.environ.setdefault("APP_ENV", "local")
try:
    from backend.app.api import dbms_showcase
    from backend.app.api.laps import current_user, get_race_telemetry
    from backend.app.main import app
finally:
    if _prior_app_env is None:
        os.environ.pop("APP_ENV", None)
    else:
        os.environ["APP_ENV"] = _prior_app_env


SESSION_A = "00000000-0000-0000-0000-000000000101"
SESSION_B = "00000000-0000-0000-0000-000000000202"
ANALYTICS_URL = f"/api/analytics/gaps?session_id={SESSION_A}"


@pytest.fixture
def client() -> Iterator[TestClient]:
    app.dependency_overrides.clear()
    yield TestClient(app)
    app.dependency_overrides.clear()


def _as_admin() -> None:
    app.dependency_overrides[current_user] = lambda: {
        "id": "synthetic-analytics-admin",
        "email": "analytics-admin@example.invalid",
        "role": "ADMIN",
    }


def _measurement(
    session_id: str,
    driver_id: str,
    lap: int,
    elapsed_ms: int | None,
    lap_time_ms: int,
    ts: int,
    *,
    position: int,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "session_id": session_id,
        "driver_id": driver_id,
        "lap": lap,
        "position": position,
        "lap_time_ms": lap_time_ms,
        "sector": 3,
        "ts": datetime.fromtimestamp(ts, tz=timezone.utc),
    }
    if elapsed_ms is not None:
        record["elapsed_ms"] = elapsed_ms
    return record


class _MongoMeasurements:
    """Small in-memory Mongo aggregate surface for recorded sector-3 telemetry."""

    def __init__(self, records: list[dict[str, Any]]):
        self.records = deepcopy(records)
        self.pipelines: list[list[dict[str, Any]]] = []

    def aggregate(self, pipeline: list[dict[str, Any]]) -> list[dict[str, Any]]:
        self.pipelines.append(pipeline)
        match = pipeline[0]["$match"]
        matched = [
            row
            for row in self.records
            if all(row.get(key) == value for key, value in match.items())
            and row.get("lap_time_ms", 0) > 0
        ]
        # Match race_lap_measurements: latest timestamp for each completed driver/lap.
        latest: dict[tuple[str, int], dict[str, Any]] = {}
        for row in sorted(matched, key=lambda item: item["ts"]):
            latest[(row["driver_id"], row["lap"])] = row
        return sorted(
            (deepcopy(row) for row in latest.values()),
            key=lambda row: (row["lap"], row["position"]),
        )


class _AnalyticsCursor:
    def __init__(self, result_rows: list[dict[str, Any]]):
        self.result_rows = result_rows
        self.executed: list[tuple[str, Any]] = []

    def __enter__(self) -> _AnalyticsCursor:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def execute(self, sql: str, params: Any = None) -> None:
        # Simulate PostgreSQL's failure for the nonexistent legacy table.
        assert "lap_telemetry" not in sql.lower(), "analytics query uses absent lap_telemetry relation"
        self.executed.append((sql, params))

    def fetchall(self) -> list[dict[str, Any]]:
        return self.result_rows


class _AnalyticsConnection:
    def __init__(self, cursor: _AnalyticsCursor):
        self._cursor = cursor

    def __enter__(self) -> _AnalyticsConnection:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def cursor(self, *args: object, **kwargs: object) -> _AnalyticsCursor:
        return self._cursor

    def transaction(self) -> _AnalyticsConnection:
        return self


def _install_sources(
    monkeypatch: pytest.MonkeyPatch,
    records: list[dict[str, Any]],
    rows: list[dict[str, Any]],
) -> tuple[_MongoMeasurements, _AnalyticsCursor]:
    _as_admin()
    mongo = _MongoMeasurements(records)
    app.dependency_overrides[get_race_telemetry] = lambda: mongo
    cursor = _AnalyticsCursor(rows)
    monkeypatch.setattr(dbms_showcase, "connection", lambda: _AnalyticsConnection(cursor))
    return mongo, cursor


def _gap(
    driver_id: str,
    lap: int,
    position: int,
    gap: int,
    interval: int | None,
    rolling: float,
) -> dict[str, Any]:
    return {
        "driver_id": driver_id,
        "driver_name": None,
        "lap": lap,
        "position": position,
        "gap_to_leader_ms": gap,
        "interval_ms": interval,
        "rolling_avg_ms": rolling,
    }


def _recorded_race() -> list[dict[str, Any]]:
    return [
        _measurement(SESSION_A, "driver-a", 1, 1000, 1000, 10, position=1),
        _measurement(SESSION_A, "driver-b", 1, 1200, 1200, 11, position=2),
        _measurement(SESSION_A, "driver-c", 1, 1200, 1200, 12, position=3),
        # A retry is superseded by the latest completed-lap measurement.
        _measurement(SESSION_A, "driver-a", 1, 1050, 1050, 20, position=1),
        # Lap 2 is absent; lap 3 remains a valid completed observation.
        _measurement(SESSION_A, "driver-a", 3, 3100, 1000, 30, position=1),
        _measurement(SESSION_A, "driver-b", 3, 3500, 1100, 31, position=2),
        # A recorded lap time without elapsed time cannot produce a race gap.
        _measurement(SESSION_A, "driver-c", 3, None, 1150, 32, position=3),
        _measurement(SESSION_B, "other-race-driver", 1, 500, 500, 40, position=1),
    ]


def test_analytics_gaps_use_scoped_recorded_elapsed_windows(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    records = _recorded_race()
    expected = [
        _gap("driver-a", 1, 1, 0, None, 1050),
        _gap("driver-b", 1, 2, 150, 150, 1200),
        _gap("driver-c", 1, 2, 150, 0, 1200),
        _gap("driver-a", 3, 1, 0, None, 1025),
        _gap("driver-b", 3, 2, 400, 400, 1150),
    ]
    mongo, cursor = _install_sources(monkeypatch, records, expected)

    response = client.get(ANALYTICS_URL)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["session_id"] == SESSION_A
    assert body["gaps"] == expected
    assert len(mongo.pipelines) == 1
    assert mongo.pipelines[0][0]["$match"]["session_id"] == SESSION_A
    assert cursor.executed, "the recorded analytics query must execute through the injected SQL layer"
    sql, params = cursor.executed[0]
    assert "lap_telemetry" not in sql.lower()
    assert SESSION_A not in sql
    assert SESSION_A in json.dumps(params, default=str)
    assert "driver-a" in json.dumps(params, default=str)
    assert "other-race-driver" not in json.dumps(params, default=str)


def test_analytics_empty_session_returns_no_rows(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    mongo, cursor = _install_sources(monkeypatch, _recorded_race(), [])

    response = client.get(f"/api/analytics/gaps?session_id={SESSION_B}")

    assert response.status_code == 200, response.text
    assert response.json()["gaps"] == []
    assert mongo.pipelines[0][0]["$match"]["session_id"] == SESSION_B
    assert cursor.executed
    sql, params = cursor.executed[0]
    assert SESSION_B not in sql
    assert SESSION_B in json.dumps(params, default=str)


def test_explain_runs_the_recorded_analytics_query(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _as_admin()

    class ExplainCursor(_AnalyticsCursor):
        def __init__(self) -> None:
            super().__init__([])

        def fetchone(self) -> tuple[list[dict[str, Any]]]:
            return ([{"Plan": {"Node Type": "CTE Scan", "Actual Rows": 5}}],)

    cursor = ExplainCursor()
    monkeypatch.setattr(dbms_showcase, "connection", lambda: _AnalyticsConnection(cursor))

    response = client.get("/api/dbms/explain?query_name=lap_telemetry_window&analyze=false")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["plan"] == [{"Plan": {"Node Type": "CTE Scan", "Actual Rows": 5}}]
    assert cursor.executed
    explain_sql, _ = cursor.executed[0]
    assert explain_sql.startswith("EXPLAIN")
    assert "elapsed_ms" in body["raw_sql"].lower()
    assert "position" in body["raw_sql"].lower()
