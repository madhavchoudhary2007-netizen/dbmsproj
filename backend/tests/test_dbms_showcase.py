from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel, ConfigDict, Field

from backend.app.main import app

# ---------------------------------------------------------------------------
# Phase 4 Showcase Contract Models / Schemas
# ---------------------------------------------------------------------------


class IsolationDemoResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    level: str
    observed_reads: list[dict[str, Any]] = Field(default_factory=list)
    anomaly_detected: bool = False
    anomaly_type: str | None = None
    timeline: list[dict[str, Any]] = Field(default_factory=list)


class DeadlockDemoResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    aborted_transaction: str | int
    sqlstate: str = "40P01"
    error_message: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class ViewDefinition(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    view_type: str  # "view" or "materialized_view"
    definition: str


class ViewsResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    views: list[ViewDefinition] = Field(default_factory=list)


class RefreshStandingsMVResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    refreshed: bool = True
    view_name: str = "mv_championship_standings"
    message: str | None = None
    duration_ms: float | None = None


class LapGapRecord(BaseModel):
    model_config = ConfigDict(extra="allow")

    driver_id: str | None = None
    driver_name: str | None = None
    lap: int
    position: int
    gap_to_leader_ms: int | float | None = None
    interval_ms: int | float | None = None
    rolling_avg_ms: int | float | None = None


class AnalyticsGapsResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    session_id: str
    gaps: list[LapGapRecord] = Field(default_factory=list)
    sql: str


class ExplainPlanResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    query_name: str | None = None
    plan: list[dict[str, Any]] | dict[str, Any] = Field(default_factory=dict)
    analyze: bool = True
    buffers: bool | None = None
    raw_sql: str | None = None


class AuditLogRow(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    table_name: str
    op: str
    row_pk: dict[str, Any] | None = None
    old: dict[str, Any] | None = None
    new: dict[str, Any] | None = None
    actor: str | None = None
    at: datetime | str


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    audit_logs: list[AuditLogRow] = Field(default_factory=list)
    total: int | None = None


class RoleGrant(BaseModel):
    model_config = ConfigDict(extra="allow")

    grantee: str
    table_name: str
    privilege_type: str


class SecurityPolicy(BaseModel):
    model_config = ConfigDict(extra="allow")

    policyname: str
    tablename: str
    roles: list[str] | str | None = None
    cmd: str | None = None


class DBMSSecurityResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    roles: list[str] = Field(default_factory=list)
    grants: list[RoleGrant] = Field(default_factory=list)
    policies: list[SecurityPolicy] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Test Helpers: Parameter & Signature Validation
# ---------------------------------------------------------------------------

VALID_ISOLATION_LEVELS = {"read_committed", "repeatable_read", "serializable"}


def validate_isolation_level_param(level: str) -> str:
    """Validate isolation level query parameter."""
    normalized = level.lower().strip()
    if normalized not in VALID_ISOLATION_LEVELS:
        msg = f"Invalid isolation level '{level}'. Must be one of {sorted(VALID_ISOLATION_LEVELS)}"
        raise ValueError(msg)
    return normalized


def validate_gaps_query_params(session_id: str | None) -> str:
    """Validate session_id query parameter for /api/analytics/gaps."""
    if not session_id or not session_id.strip():
        msg = "Missing required query parameter: session_id"
        raise ValueError(msg)
    try:
        UUID(session_id.strip())
    except ValueError as err:
        msg = f"Invalid UUID for session_id: '{session_id}'"
        raise ValueError(msg) from err
    return session_id.strip()


def validate_audit_query_params(table: str | None = None, limit: int = 50) -> dict[str, Any]:
    """Validate query parameters for /api/dbms/audit."""
    if limit <= 0 or limit > 500:
        msg = f"Limit must be between 1 and 500, got {limit}"
        raise ValueError(msg)
    return {"table": table.strip() if table else None, "limit": limit}


def validate_explain_query_params(
    analyze: bool = True, query_name: str | None = None
) -> dict[str, Any]:
    """Validate query parameters for /api/dbms/explain."""
    allowed_queries = {"standings_rollup", "lap_telemetry_window", "driver_history"}
    if query_name is not None and query_name not in allowed_queries:
        msg = f"Query '{query_name}' not in allow-list {sorted(allowed_queries)}"
        raise ValueError(msg)
    return {"analyze": analyze, "query_name": query_name}


# ---------------------------------------------------------------------------
# Schema & Helper Unit Tests
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


def test_helper_parameter_validation() -> None:
    assert validate_isolation_level_param("READ_COMMITTED") == "read_committed"
    with pytest.raises(ValueError, match="Invalid isolation level"):
        validate_isolation_level_param("invalid_level")

    valid_id = "00000000-0000-0000-0000-000000000001"
    assert validate_gaps_query_params(valid_id) == valid_id
    with pytest.raises(ValueError, match="Missing required query parameter"):
        validate_gaps_query_params("")
    with pytest.raises(ValueError, match="Invalid UUID"):
        validate_gaps_query_params("not-a-uuid")

    audit_params = validate_audit_query_params(table="penalties", limit=25)
    assert audit_params["table"] == "penalties"
    assert audit_params["limit"] == 25
    with pytest.raises(ValueError, match="Limit must be between"):
        validate_audit_query_params(limit=0)

    explain_params = validate_explain_query_params(analyze=True, query_name="standings_rollup")
    assert explain_params["analyze"] is True
    with pytest.raises(ValueError, match="not in allow-list"):
        validate_explain_query_params(query_name="drop table users")


# ---------------------------------------------------------------------------
# Route Contract Specifications (Marked xfail until Phase 4 routes mounted)
# ---------------------------------------------------------------------------


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.mark.xfail(reason="Phase 4 showcase route pending implementation", strict=False)
def test_route_isolation_demo(client: TestClient) -> None:
    response = client.get("/api/dbms/isolation-demo?level=read_committed")
    assert response.status_code == 200
    model = IsolationDemoResponse.model_validate(response.json())
    assert model.level == "read_committed"


@pytest.mark.xfail(reason="Phase 4 showcase route pending implementation", strict=False)
def test_route_deadlock_demo(client: TestClient) -> None:
    response = client.post("/api/dbms/deadlock-demo")
    assert response.status_code == 200
    model = DeadlockDemoResponse.model_validate(response.json())
    assert model.sqlstate == "40P01"


@pytest.mark.xfail(reason="Phase 4 showcase route pending implementation", strict=False)
def test_route_views(client: TestClient) -> None:
    response = client.get("/api/dbms/views")
    assert response.status_code == 200
    model = ViewsResponse.model_validate(response.json())
    assert any(v.name == "v_driver_season_summary" for v in model.views)


@pytest.mark.xfail(reason="Phase 4 showcase route pending implementation", strict=False)
def test_route_refresh_standings_mv(client: TestClient) -> None:
    response = client.post("/api/dbms/refresh-standings-mv")
    assert response.status_code == 200
    model = RefreshStandingsMVResponse.model_validate(response.json())
    assert model.refreshed is True


@pytest.mark.xfail(reason="Phase 4 showcase route pending implementation", strict=False)
def test_route_analytics_gaps(client: TestClient) -> None:
    response = client.get(
        "/api/analytics/gaps?session_id=00000000-0000-0000-0000-000000000001"
    )
    assert response.status_code == 200
    model = AnalyticsGapsResponse.model_validate(response.json())
    assert model.session_id == "00000000-0000-0000-0000-000000000001"


@pytest.mark.xfail(reason="Phase 4 showcase route pending implementation", strict=False)
def test_route_explain_plan(client: TestClient) -> None:
    response = client.get("/api/dbms/explain?analyze=true")
    assert response.status_code == 200
    model = ExplainPlanResponse.model_validate(response.json())
    assert model.analyze is True


@pytest.mark.xfail(reason="Phase 4 showcase route pending implementation", strict=False)
def test_route_audit_log(client: TestClient) -> None:
    response = client.get("/api/dbms/audit?limit=10")
    assert response.status_code == 200
    model = AuditLogResponse.model_validate(response.json())
    assert isinstance(model.audit_logs, list)


@pytest.mark.xfail(reason="Phase 4 showcase route pending implementation", strict=False)
def test_route_security(client: TestClient) -> None:
    response = client.get("/api/dbms/security")
    assert response.status_code == 200
    model = DBMSSecurityResponse.model_validate(response.json())
    assert isinstance(model.roles, list)
