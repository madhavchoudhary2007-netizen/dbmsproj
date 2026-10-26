from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


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


__all__ = [
    "AnalyticsGapsResponse",
    "AuditLogResponse",
    "AuditLogRow",
    "DBMSSecurityResponse",
    "DeadlockDemoResponse",
    "ExplainPlanResponse",
    "IsolationDemoResponse",
    "LapGapRecord",
    "RefreshStandingsMVResponse",
    "RoleGrant",
    "SecurityPolicy",
    "ViewDefinition",
    "ViewsResponse",
    "validate_audit_query_params",
    "validate_explain_query_params",
    "validate_gaps_query_params",
    "validate_isolation_level_param",
]
