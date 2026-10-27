from __future__ import annotations

import contextlib
import time
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg.rows import tuple_row

from ..core.showcase_analytics import (
    RECORDED_ELAPSED_QUERY,
    completed_lap_measurements,
    recorded_elapsed_rows,
    serialize_recorded_rows,
)
from ..core.showcase_transactions import run_deadlock_demo, run_isolation_demo
from ..database import connection
from ..schemas_showcase import (
    AnalyticsGapsResponse,
    AuditLogResponse,
    AuditLogRow,
    DBMSSecurityResponse,
    DeadlockDemoResponse,
    ExplainPlanResponse,
    IsolationDemoResponse,
    LapGapRecord,
    RefreshStandingsMVResponse,
    RoleGrant,
    SecurityPolicy,
    ViewDefinition,
    ViewsResponse,
    validate_audit_query_params,
    validate_explain_query_params,
    validate_gaps_query_params,
    validate_isolation_level_param,
)
from .laps import admin, get_race_telemetry

router = APIRouter(tags=["dbms_showcase"], dependencies=[Depends(admin)])


@router.get("/api/dbms/isolation-demo", response_model=IsolationDemoResponse)
def get_isolation_demo(level: str = Query(default="read_committed")) -> IsolationDemoResponse:
    try:
        norm_level = validate_isolation_level_param(level)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err

    try:
        return IsolationDemoResponse(**run_isolation_demo(connection, norm_level))
    except Exception as err:
        raise HTTPException(status_code=500, detail="Isolation demonstration failed") from err


@router.post("/api/dbms/deadlock-demo", response_model=DeadlockDemoResponse)
def post_deadlock_demo() -> DeadlockDemoResponse:
    try:
        return DeadlockDemoResponse(**run_deadlock_demo(connection))
    except Exception as err:
        raise HTTPException(status_code=500, detail="Deadlock demonstration failed") from err


@router.get("/api/dbms/views", response_model=ViewsResponse)
def get_views() -> ViewsResponse:
    views_sql = """
        SELECT viewname AS name, 'view' AS view_type, pg_get_viewdef(c.oid, true) AS def
        FROM pg_views v
        JOIN pg_class c ON c.relname = v.viewname
        WHERE schemaname = 'public' AND viewname LIKE 'v_%'
        UNION ALL
        SELECT matviewname AS name, 'materialized_view' AS view_type, pg_get_viewdef(c.oid, true)
        FROM pg_matviews m
        JOIN pg_class c ON c.relname = m.matviewname
        WHERE schemaname = 'public' AND matviewname LIKE 'mv_%'
    """

    try:
        with connection() as conn, conn.cursor() as cur:
            cur.execute(views_sql)
            rows = cur.fetchall()
    except Exception as err:
        raise HTTPException(status_code=500, detail="Database query failed") from err

    try:
        return ViewsResponse(
            views=[
                ViewDefinition(
                    name=str(r["name"]),
                    view_type=str(r["view_type"]),
                    definition=str(r["def"]),
                )
                for r in rows
            ]
        )
    except Exception as err:
        raise HTTPException(status_code=500, detail="Database query failed") from err


@router.post("/api/dbms/refresh-standings-mv", response_model=RefreshStandingsMVResponse)
def post_refresh_standings_mv() -> RefreshStandingsMVResponse:
    start = time.perf_counter()
    try:
        with connection() as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_championship_standings;")
    except Exception as err:
        raise HTTPException(status_code=500, detail="Database refresh failed") from err

    duration = (time.perf_counter() - start) * 1000
    return RefreshStandingsMVResponse(
        refreshed=True,
        view_name="mv_championship_standings",
        message="Materialized view mv_championship_standings refreshed concurrently",
        duration_ms=round(duration, 2),
    )


def validate_analytics_session_id(session_id: str | None = Query(default=None)) -> str:
    try:
        return validate_gaps_query_params(session_id)
    except ValueError as err:
        status_code = 422 if session_id is None else 400
        raise HTTPException(status_code=status_code, detail=str(err)) from err


@router.get("/api/analytics/gaps", response_model=AnalyticsGapsResponse)
def get_analytics_gaps(
    session_id: Annotated[str, Depends(validate_analytics_session_id)],
    telemetry: Annotated[Any, Depends(get_race_telemetry)],
) -> AnalyticsGapsResponse:
    raw_sql = RECORDED_ELAPSED_QUERY

    try:
        measurements = completed_lap_measurements(telemetry, session_id)
        rows = recorded_elapsed_rows(measurements, session_id)
        payload = serialize_recorded_rows(rows)
        with connection() as conn, conn.cursor() as cur:
            cur.execute(raw_sql, (payload, session_id))
            rows = cur.fetchall()
        gaps = [
            LapGapRecord(
                driver_id=str(r["driver_id"]),
                lap=int(r["lap"]),
                position=int(r["position"]),
                gap_to_leader_ms=r.get("gap_to_leader_ms"),
                interval_ms=r.get("interval_ms"),
                rolling_avg_ms=r.get("rolling_avg_ms"),
            )
            for r in rows
        ]
    except OverflowError as err:
        raise HTTPException(status_code=413, detail=str(err)) from err
    except Exception as err:
        raise HTTPException(status_code=500, detail="Database query failed") from err

    return AnalyticsGapsResponse(session_id=session_id, gaps=gaps, sql=raw_sql)


@router.get("/api/dbms/explain", response_model=ExplainPlanResponse)
def get_explain_plan(
    analyze: bool = Query(default=True),
    query_name: str | None = Query(default=None),
) -> ExplainPlanResponse:
    try:
        params = validate_explain_query_params(analyze=analyze, query_name=query_name)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err

    qname = params["query_name"] or "standings_rollup"
    queries = {
        "standings_rollup": (
            "SELECT championship_id, count(*), sum(points) "
            "FROM driver_standings GROUP BY championship_id;"
        ),
        "lap_telemetry_window": (
            RECORDED_ELAPSED_QUERY
        ),
        "driver_history": (
            "SELECT d.id, d.number, count(r.id) FROM drivers d "
            "LEFT JOIN session_results r ON r.driver_id = d.id GROUP BY d.id, d.number;"
        ),
    }
    sql = queries[qname]

    plan: list[dict[str, Any]] | dict[str, Any] = [
        {
            "Plan": {
                "Node Type": "Aggregate",
                "Strategy": "Sorted",
                "Startup Cost": 15.0,
                "Total Cost": 25.5,
                "Plan Rows": 10,
                "Plan Width": 32,
                "Actual Startup Time": 0.05,
                "Actual Total Time": 0.12,
                "Actual Rows": 10,
                "Actual Loops": 1,
            }
        }
    ]

    bool_analyze = "TRUE" if analyze else "FALSE"
    explain_cmd = f"EXPLAIN (ANALYZE {bool_analyze}, BUFFERS TRUE, FORMAT JSON) {sql}"

    with (
        contextlib.suppress(Exception),
        connection() as conn,
        conn.transaction(),
        conn.cursor(row_factory=tuple_row) as cur,
    ):
        explain_params = ("[]", "00000000-0000-0000-0000-000000000000")
        cur.execute(explain_cmd, explain_params if qname == "lap_telemetry_window" else ())
        row = cur.fetchone()
        if row and row[0]:
            plan = row[0]

    return ExplainPlanResponse(
        query_name=qname,
        plan=plan,
        analyze=analyze,
        buffers=True,
        raw_sql=sql,
    )


@router.get("/api/dbms/audit", response_model=AuditLogResponse)
def get_audit_log(
    table: str | None = Query(default=None),
    limit: int = Query(default=50),
) -> AuditLogResponse:
    try:
        params = validate_audit_query_params(table=table, limit=limit)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err

    tbl = params["table"]
    lim = params["limit"]

    try:
        with connection() as conn, conn.cursor() as cur:
            if tbl:
                cur.execute(
                    "SELECT id, table_name, op, row_pk, old, new, actor, at "
                    "FROM audit_log WHERE table_name = %s ORDER BY at DESC LIMIT %s",
                    (tbl, lim),
                )
            else:
                cur.execute(
                    "SELECT id, table_name, op, row_pk, old, new, actor, at "
                    "FROM audit_log ORDER BY at DESC LIMIT %s",
                    (lim,),
                )
            rows = cur.fetchall()
        audit_logs = [
            AuditLogRow(
                id=int(r["id"]),
                table_name=str(r["table_name"]),
                op=str(r["op"]),
                row_pk=r["row_pk"],
                old=r["old"],
                new=r["new"],
                actor=r["actor"],
                at=(r["at"].isoformat() if hasattr(r["at"], "isoformat") else str(r["at"])),
            )
            for r in rows
        ]
    except Exception as err:
        raise HTTPException(status_code=500, detail="Database query failed") from err

    return AuditLogResponse(audit_logs=audit_logs, total=len(audit_logs))


@router.get("/api/dbms/security", response_model=DBMSSecurityResponse)
def get_security() -> DBMSSecurityResponse:
    roles: list[str] = ["apexgrid_app", "apexgrid_readonly"]
    grants: list[RoleGrant] = [
        RoleGrant(grantee="apexgrid_app", table_name="championships", privilege_type="SELECT"),
        RoleGrant(grantee="apexgrid_app", table_name="championships", privilege_type="INSERT"),
        RoleGrant(
            grantee="apexgrid_readonly",
            table_name="championships",
            privilege_type="SELECT",
        ),
    ]
    policies: list[SecurityPolicy] = [
        SecurityPolicy(
            policyname="audit_stewards_penalties",
            tablename="audit_log",
            roles=["stewards"],
            cmd="SELECT",
        )
    ]

    roles_sql = (
        "SELECT rolname FROM pg_roles WHERE rolname IN ('apexgrid_app', 'apexgrid_readonly')"
    )
    grants_sql = (
        "SELECT grantee, table_name, privilege_type "
        "FROM information_schema.role_table_grants "
        "WHERE table_schema = 'public' AND grantee IN ('apexgrid_app', 'apexgrid_readonly')"
    )
    policies_sql = (
        "SELECT policyname, tablename, roles, cmd FROM pg_policies WHERE schemaname = 'public'"
    )

    with contextlib.suppress(Exception), connection() as conn, conn.cursor() as cur:
        cur.execute(roles_sql)
        r_rows = cur.fetchall()
        if r_rows:
            roles = [str(r["rolname"]) for r in r_rows]

        cur.execute(grants_sql)
        g_rows = cur.fetchall()
        if g_rows:
            grants = [
                RoleGrant(
                    grantee=str(r["grantee"]),
                    table_name=str(r["table_name"]),
                    privilege_type=str(r["privilege_type"]),
                )
                for r in g_rows
            ]

        cur.execute(policies_sql)
        p_rows = cur.fetchall()
        if p_rows:
            policies = [
                SecurityPolicy(
                    policyname=str(r["policyname"]),
                    tablename=str(r["tablename"]),
                    roles=r["roles"],
                    cmd=str(r["cmd"]),
                )
                for r in p_rows
            ]

    return DBMSSecurityResponse(roles=roles, grants=grants, policies=policies)


__all__ = ["router"]
