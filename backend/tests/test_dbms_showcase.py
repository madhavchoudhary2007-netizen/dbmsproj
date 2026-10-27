from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timezone
import os
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

_prior_app_env = os.environ.get("APP_ENV")
os.environ.setdefault("APP_ENV", "local")
try:
    from backend.app.api.laps import current_user, get_race_telemetry
    from backend.app.main import app
    from backend.app.schemas_showcase import (
        AnalyticsGapsResponse,
        AuditLogResponse,
        DBMSSecurityResponse,
        DeadlockDemoResponse,
        ExplainPlanResponse,
        IsolationDemoResponse,
        RefreshStandingsMVResponse,
        ViewsResponse,
        validate_audit_query_params,
        validate_explain_query_params,
        validate_gaps_query_params,
        validate_isolation_level_param,
    )
finally:
    if _prior_app_env is None:
        os.environ.pop("APP_ENV", None)
    else:
        os.environ["APP_ENV"] = _prior_app_env


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    global _showcase_database
    _showcase_database = _ShowcaseDatabase()
    missing = object()
    previous = app.dependency_overrides.get(current_user, missing)
    previous_telemetry = app.dependency_overrides.get(get_race_telemetry, missing)
    app.dependency_overrides[current_user] = lambda: {
        "id": "synthetic-admin-user",
        "email": "admin@example.invalid",
        "role": "ADMIN",
    }
    app.dependency_overrides[get_race_telemetry] = lambda: _ShowcaseTelemetry()
    monkeypatch.setattr("backend.app.api.dbms_showcase.connection", _showcase_connection)
    try:
        yield TestClient(app)
    finally:
        if previous is missing:
            app.dependency_overrides.pop(current_user, None)
        else:
            app.dependency_overrides[current_user] = previous
        if previous_telemetry is missing:
            app.dependency_overrides.pop(get_race_telemetry, None)
        else:
            app.dependency_overrides[get_race_telemetry] = previous_telemetry


class _ShowcaseTelemetry:
    def aggregate(self, _pipeline: list[dict[str, object]]) -> list[dict[str, object]]:
        return [
            {
                "session_id": "00000000-0000-0000-0000-000000000001",
                "driver_id": "driver-1",
                "lap": 1,
                "position": 1,
                "elapsed_ms": 84250,
                "lap_time_ms": 84250,
                "sector": 3,
                "ts": datetime(2026, 10, 26, 12, 0, tzinfo=timezone.utc),
            }
        ]


class _ShowcaseCursor:
    def __init__(self) -> None:
        self.sql = ""

    def __enter__(self) -> _ShowcaseCursor:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def execute(self, sql: str, params: object = None) -> None:
        self.sql = sql

    def fetchall(self) -> list[dict[str, object]]:
        if "pg_views" in self.sql:
            return [
                {
                    "name": "v_driver_season_summary",
                    "view_type": "view",
                    "def": "SELECT driver_id, season_id FROM driver_standings",
                },
                {
                    "name": "mv_championship_standings",
                    "view_type": "materialized_view",
                    "def": "SELECT championship_id, driver_id FROM standings",
                },
            ]
        if "lap_telemetry" in self.sql or "jsonb_to_recordset" in self.sql:
            return [
                {
                    "driver_id": "driver-1",
                    "lap": 1,
                    "position": 1,
                    "gap_to_leader_ms": 0,
                    "interval_ms": 0,
                    "rolling_avg_ms": 84250,
                }
            ]
        if "audit_log" in self.sql:
            return [
                {
                    "id": 1,
                    "table_name": "penalties",
                    "op": "INSERT",
                    "row_pk": {"id": 10},
                    "old": None,
                    "new": {"severity": "5s"},
                    "actor": "steward_1",
                    "at": "2026-10-26T12:00:00Z",
                }
            ]
        if "pg_roles" in self.sql:
            return [{"rolname": "apexgrid_app"}, {"rolname": "apexgrid_readonly"}]
        if "role_table_grants" in self.sql:
            return [
                {
                    "grantee": "apexgrid_app",
                    "table_name": "championships",
                    "privilege_type": "SELECT",
                }
            ]
        if "pg_policies" in self.sql:
            return [
                {
                    "policyname": "audit_stewards_penalties",
                    "tablename": "audit_log",
                    "roles": ["stewards"],
                    "cmd": "SELECT",
                }
            ]
        return []

    def fetchone(self) -> tuple[list[dict[str, object]]]:
        return ([{"Plan": {"Node Type": "Aggregate", "Total Cost": 25.5}}],)


class _ShowcaseConnection:
    def __init__(self, database: _ShowcaseDatabase, identity: int) -> None:
        self.database = database
        self.identity = identity
        self.autocommit = False
        self.isolation = "read committed"
        self.snapshot: dict[str, float] | None = None
        self.locked_rows: set[str] = set()
        self.pending: dict[str, float | None] = {}
        self.statements: list[str] = []

    def __enter__(self) -> _ShowcaseConnection:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def cursor(self, *args: object, **kwargs: object) -> _ShowcaseCursor:
        return _ShowcaseCursor()

    def transaction(self) -> _ShowcaseTransaction:
        return _ShowcaseTransaction(self)

    def execute(self, sql: str, params: object = None) -> _ShowcaseConnection:
        normalized = " ".join(sql.lower().split())
        self.statements.append(normalized)
        values = params if isinstance(params, tuple) else ()
        if normalized.startswith("set transaction isolation level"):
            self.isolation = normalized.removeprefix("set transaction isolation level ")
        elif normalized.startswith("insert into circuits"):
            row_id, _name, length = values
            self.pending[str(row_id)] = float(length)
        elif "select (length_km * 1000)" in normalized:
            row_id = str(values[0])
            if self.snapshot is None:
                self.snapshot = self.database.rows.copy()
            rows = self.snapshot if self.isolation in {"repeatable read", "serializable"} else self.database.rows
            value = self.pending.get(row_id, rows.get(row_id))
            self._result = (int(float(value) * 1000),)
            if normalized.endswith("for update"):
                self.locked_rows.add(row_id)
        elif normalized.startswith("select id from circuits"):
            row_id = str(values[0])
            self.locked_rows.add(row_id)
            self._result = (row_id,)
        elif normalized.startswith("update circuits"):
            row_id = str(values[-1])
            if self.identity == 1 and self.locked_rows:
                raise _ShowcaseDeadlock()
            self.pending[row_id] = 1.5 if "1.500" in normalized else 0.999
        elif normalized.startswith("delete from circuits"):
            for row_id in values[0]:
                self.pending[str(row_id)] = None
        return self

    def fetchone(self) -> tuple[object, ...] | None:
        return getattr(self, "_result", None)


class _ShowcaseDatabase:
    def __init__(self) -> None:
        self.rows: dict[str, float] = {}
        self.connections = 0


class _ShowcaseDeadlock(Exception):
    sqlstate = "40P01"


class _ShowcaseTransaction:
    def __init__(self, connection: _ShowcaseConnection) -> None:
        self.connection = connection

    def __enter__(self) -> _ShowcaseTransaction:
        self.connection.snapshot = None
        self.connection.isolation = "read committed"
        self.connection.pending = {}
        return self

    def __exit__(self, exc_type: object, *_: object) -> None:
        if exc_type is None:
            for row_id, value in self.connection.pending.items():
                if value is None:
                    self.connection.database.rows.pop(row_id, None)
                else:
                    self.connection.database.rows[row_id] = value
        self.connection.pending = {}
        return None


_showcase_database = _ShowcaseDatabase()


def _showcase_connection() -> _ShowcaseConnection:
    identity = _showcase_database.connections
    _showcase_database.connections += 1
    return _ShowcaseConnection(_showcase_database, identity)


# ---------------------------------------------------------------------------
# Schema Unit Tests
# ---------------------------------------------------------------------------


def test_schema_isolation_demo_response() -> None:
    data = {
        "level": "repeatable_read",
        "observed_reads": [{"t": 1, "val": 10}, {"t": 2, "val": 10}],
        "anomaly_detected": False,
        "anomaly_type": None,
        "timeline": [{"event": "start"}, {"event": "commit"}],
    }
    model = IsolationDemoResponse.model_validate(data)
    assert model.level == "repeatable_read"
    assert model.anomaly_detected is False
    assert len(model.observed_reads) == 2


def test_schema_isolation_demo_default_fields() -> None:
    model = IsolationDemoResponse(level="serializable")
    assert model.level == "serializable"
    assert model.observed_reads == []
    assert model.anomaly_detected is False
    assert model.anomaly_type is None
    assert model.timeline == []


def test_schema_deadlock_demo_response() -> None:
    data = {
        "aborted_transaction": "T2",
        "sqlstate": "40P01",
        "error_message": "deadlock detected",
        "details": {"wait_queue": ["T1", "T2"]},
    }
    model = DeadlockDemoResponse.model_validate(data)
    assert model.aborted_transaction == "T2"
    assert model.sqlstate == "40P01"


def test_schema_views_response() -> None:
    data = {
        "views": [
            {
                "name": "v_driver_season_summary",
                "view_type": "view",
                "definition": "SELECT * FROM results",
            },
            {
                "name": "mv_championship_standings",
                "view_type": "materialized_view",
                "definition": "SELECT * FROM standings",
            },
        ]
    }
    model = ViewsResponse.model_validate(data)
    assert len(model.views) == 2
    assert model.views[0].name == "v_driver_season_summary"
    assert model.views[1].view_type == "materialized_view"


def test_schema_refresh_standings_mv_response() -> None:
    data = {
        "refreshed": True,
        "view_name": "mv_championship_standings",
        "message": "Refreshed concurrently",
        "duration_ms": 12.5,
    }
    model = RefreshStandingsMVResponse.model_validate(data)
    assert model.refreshed is True
    assert model.view_name == "mv_championship_standings"
    assert model.duration_ms == 12.5


def test_schema_analytics_gaps_response() -> None:
    data = {
        "session_id": "00000000-0000-0000-0000-000000000001",
        "gaps": [
            {
                "driver_id": "d1",
                "lap": 1,
                "position": 1,
                "gap_to_leader_ms": 0,
                "interval_ms": 0,
                "rolling_avg_ms": 84250,
            }
        ],
        "sql": "SELECT RANK() OVER ...",
    }
    model = AnalyticsGapsResponse.model_validate(data)
    assert model.session_id == "00000000-0000-0000-0000-000000000001"
    assert len(model.gaps) == 1
    assert "RANK()" in model.sql


def test_schema_explain_plan_response() -> None:
    data = {
        "query_name": "standings_rollup",
        "plan": [{"Node Type": "Seq Scan", "Total Cost": 15.0}],
        "analyze": True,
        "buffers": True,
    }
    model = ExplainPlanResponse.model_validate(data)
    assert model.analyze is True
    assert model.query_name == "standings_rollup"


def test_schema_audit_log_response() -> None:
    data = {
        "audit_logs": [
            {
                "id": 1,
                "table_name": "penalties",
                "op": "INSERT",
                "row_pk": {"id": 10},
                "old": None,
                "new": {"severity": "5s"},
                "actor": "steward_1",
                "at": "2026-10-26T12:00:00Z",
            }
        ],
        "total": 1,
    }
    model = AuditLogResponse.model_validate(data)
    assert len(model.audit_logs) == 1
    assert model.audit_logs[0].actor == "steward_1"


def test_schema_dbms_security_response() -> None:
    data = {
        "roles": ["apexgrid_app", "apexgrid_readonly"],
        "grants": [
            {
                "grantee": "apexgrid_app",
                "table_name": "championships",
                "privilege_type": "SELECT",
            }
        ],
        "policies": [
            {
                "policyname": "audit_stewards_penalties",
                "tablename": "audit_log",
                "roles": ["stewards"],
                "cmd": "SELECT",
            }
        ],
    }
    model = DBMSSecurityResponse.model_validate(data)
    assert "apexgrid_app" in model.roles
    assert len(model.grants) == 1
    assert len(model.policies) == 1


# ---------------------------------------------------------------------------
# Helper Parameter Validation Unit Tests
# ---------------------------------------------------------------------------


def test_helper_isolation_level_validation_valid() -> None:
    assert validate_isolation_level_param("READ_COMMITTED") == "read_committed"
    assert validate_isolation_level_param("repeatable_read") == "repeatable_read"
    assert validate_isolation_level_param("SERIALIZABLE") == "serializable"


@pytest.mark.parametrize("invalid_level", ["phantom_read", "dirty_read", "invalid", "", "123"])
def test_helper_isolation_level_validation_invalid(invalid_level: str) -> None:
    with pytest.raises(ValueError, match="Invalid isolation level"):
        validate_isolation_level_param(invalid_level)


def test_helper_gaps_query_params_valid() -> None:
    valid_id = "00000000-0000-0000-0000-000000000001"
    assert validate_gaps_query_params(valid_id) == valid_id


def test_helper_gaps_query_params_missing() -> None:
    with pytest.raises(ValueError, match="Missing required query parameter"):
        validate_gaps_query_params("")


@pytest.mark.parametrize("malformed_uuid", ["not-a-uuid", "12345", "xyz"])
def test_helper_gaps_query_params_malformed(malformed_uuid: str) -> None:
    with pytest.raises(ValueError, match="Invalid UUID"):
        validate_gaps_query_params(malformed_uuid)


def test_helper_audit_query_params_valid() -> None:
    params = validate_audit_query_params(table="penalties", limit=25)
    assert params["table"] == "penalties"
    assert params["limit"] == 25

    default_params = validate_audit_query_params()
    assert default_params["table"] is None
    assert default_params["limit"] == 50


@pytest.mark.parametrize("invalid_limit", [0, -1, -50, 501, 1000])
def test_helper_audit_query_params_invalid_limit(invalid_limit: int) -> None:
    with pytest.raises(ValueError, match="Limit must be between"):
        validate_audit_query_params(limit=invalid_limit)


def test_helper_explain_query_params_valid() -> None:
    params = validate_explain_query_params(analyze=True, query_name="standings_rollup")
    assert params["analyze"] is True
    assert params["query_name"] == "standings_rollup"

    params_none = validate_explain_query_params(analyze=False, query_name=None)
    assert params_none["analyze"] is False
    assert params_none["query_name"] is None


@pytest.mark.parametrize(
    "disallowed_query",
    ["drop table users", "select * from audit_log", "random_query"],
)
def test_helper_explain_query_params_disallowed(disallowed_query: str) -> None:
    with pytest.raises(ValueError, match="not in allow-list"):
        validate_explain_query_params(query_name=disallowed_query)


# ---------------------------------------------------------------------------
# Route Contract Tests (Active, Verified Green)
# ---------------------------------------------------------------------------


def test_route_isolation_demo(client: TestClient) -> None:
    response = client.get("/api/dbms/isolation-demo")
    assert response.status_code == 200
    model = IsolationDemoResponse.model_validate(response.json())
    assert model.level == "read_committed"
    assert model.anomaly_detected is True
    assert len(model.observed_reads) >= 2


def test_route_isolation_demo_repeatable_read(client: TestClient) -> None:
    response = client.get("/api/dbms/isolation-demo?level=repeatable_read")
    assert response.status_code == 200
    model = IsolationDemoResponse.model_validate(response.json())
    assert model.level == "repeatable_read"
    assert model.anomaly_detected is False


def test_route_isolation_demo_serializable(client: TestClient) -> None:
    response = client.get("/api/dbms/isolation-demo?level=serializable")
    assert response.status_code == 200
    model = IsolationDemoResponse.model_validate(response.json())
    assert model.level == "serializable"
    assert model.anomaly_detected is False


@pytest.mark.parametrize("invalid_level", ["snapshot", "dirty_read", "unknown"])
def test_route_isolation_demo_invalid_level(client: TestClient, invalid_level: str) -> None:
    response = client.get(f"/api/dbms/isolation-demo?level={invalid_level}")
    assert response.status_code in (400, 422)


def test_route_deadlock_demo(client: TestClient) -> None:
    response = client.post("/api/dbms/deadlock-demo")
    assert response.status_code == 200
    model = DeadlockDemoResponse.model_validate(response.json())
    assert model.sqlstate == "40P01"
    assert model.aborted_transaction == "T2"
    assert "transaction_1" in model.details


def test_route_deadlock_demo_method_not_allowed(client: TestClient) -> None:
    response = client.get("/api/dbms/deadlock-demo")
    assert response.status_code == 405


def test_route_views(client: TestClient) -> None:
    response = client.get("/api/dbms/views")
    assert response.status_code == 200
    model = ViewsResponse.model_validate(response.json())
    assert any(v.name == "v_driver_season_summary" for v in model.views)
    assert any(v.name == "mv_championship_standings" for v in model.views)


def test_route_views_types(client: TestClient) -> None:
    response = client.get("/api/dbms/views")
    assert response.status_code == 200
    model = ViewsResponse.model_validate(response.json())
    for view in model.views:
        assert view.view_type in ("view", "materialized_view")
        assert len(view.definition) > 0


def test_route_refresh_standings_mv(client: TestClient) -> None:
    response = client.post("/api/dbms/refresh-standings-mv")
    assert response.status_code == 200
    model = RefreshStandingsMVResponse.model_validate(response.json())
    assert model.refreshed is True
    assert model.view_name == "mv_championship_standings"


def test_route_refresh_standings_mv_method_not_allowed(client: TestClient) -> None:
    response = client.get("/api/dbms/refresh-standings-mv")
    assert response.status_code == 405


def test_route_analytics_gaps(client: TestClient) -> None:
    response = client.get("/api/analytics/gaps?session_id=00000000-0000-0000-0000-000000000001")
    assert response.status_code == 200
    model = AnalyticsGapsResponse.model_validate(response.json())
    assert model.session_id == "00000000-0000-0000-0000-000000000001"
    assert len(model.gaps) >= 1
    assert "RANK()" in model.sql


@pytest.mark.parametrize("malformed_uuid", ["not-a-valid-uuid", "12345", "xyz"])
def test_route_analytics_gaps_invalid_session_id(client: TestClient, malformed_uuid: str) -> None:
    response = client.get(f"/api/analytics/gaps?session_id={malformed_uuid}")
    assert response.status_code in (400, 422)


def test_route_analytics_gaps_missing_session_id(client: TestClient) -> None:
    response = client.get("/api/analytics/gaps")
    assert response.status_code in (400, 422)


def test_route_explain_plan(client: TestClient) -> None:
    response = client.get("/api/dbms/explain?analyze=true")
    assert response.status_code == 200
    model = ExplainPlanResponse.model_validate(response.json())
    assert model.analyze is True
    assert model.query_name == "standings_rollup"


def test_route_explain_plan_named_query(client: TestClient) -> None:
    response = client.get("/api/dbms/explain?query_name=lap_telemetry_window")
    assert response.status_code == 200
    model = ExplainPlanResponse.model_validate(response.json())
    assert model.query_name == "lap_telemetry_window"


@pytest.mark.parametrize("disallowed", ["drop_table", "user_passwords", "select_all_arbitrary"])
def test_route_explain_plan_disallowed_query(client: TestClient, disallowed: str) -> None:
    response = client.get(f"/api/dbms/explain?query_name={disallowed}")
    assert response.status_code in (400, 422)


def test_route_audit_log(client: TestClient) -> None:
    response = client.get("/api/dbms/audit?limit=10")
    assert response.status_code == 200
    model = AuditLogResponse.model_validate(response.json())
    assert isinstance(model.audit_logs, list)


def test_route_audit_log_with_table(client: TestClient) -> None:
    response = client.get("/api/dbms/audit?table=penalties&limit=5")
    assert response.status_code == 200
    model = AuditLogResponse.model_validate(response.json())
    assert isinstance(model.audit_logs, list)


@pytest.mark.parametrize("invalid_limit", [0, -10, 501, 10000])
def test_route_audit_log_invalid_limit(client: TestClient, invalid_limit: int) -> None:
    response = client.get(f"/api/dbms/audit?limit={invalid_limit}")
    assert response.status_code in (400, 422)


def test_route_security(client: TestClient) -> None:
    response = client.get("/api/dbms/security")
    assert response.status_code == 200
    model = DBMSSecurityResponse.model_validate(response.json())
    assert isinstance(model.roles, list)
    assert any("apexgrid" in r for r in model.roles)


def test_route_security_grants_and_policies(client: TestClient) -> None:
    response = client.get("/api/dbms/security")
    assert response.status_code == 200
    model = DBMSSecurityResponse.model_validate(response.json())
    assert isinstance(model.grants, list)
    assert isinstance(model.policies, list)
    assert len(model.grants) >= 1
    assert len(model.policies) >= 1
