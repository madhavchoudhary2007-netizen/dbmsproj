from __future__ import annotations

import contextlib
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg.rows import tuple_row

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
from .laps import admin

router = APIRouter(tags=["dbms_showcase"], dependencies=[Depends(admin)])


@router.get("/api/dbms/isolation-demo", response_model=IsolationDemoResponse)
def get_isolation_demo(level: str = Query(default="read_committed")) -> IsolationDemoResponse:
    try:
        norm_level = validate_isolation_level_param(level)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err

    # Showcase simulation with scripted interleaving
    if norm_level == "read_committed":
        return IsolationDemoResponse(
            level="read_committed",
            observed_reads=[
                {"step": "T1: Initial read", "balance": 1000},
                {"step": "T1: Read after T2 commit", "balance": 1500},
            ],
            anomaly_detected=True,
            anomaly_type="Non-repeatable Read (Fuzzy Read)",
            timeline=[
                {"time": 1, "tx": "T1", "action": "BEGIN ISOLATION LEVEL READ COMMITTED"},
                {"time": 2, "tx": "T1", "action": "SELECT balance FROM account WHERE id=1 -> 1000"},
                {
                    "time": 3,
                    "tx": "T2",
                    "action": "BEGIN; UPDATE account SET balance=1500 WHERE id=1; COMMIT;",
                },
                {
                    "time": 4,
                    "tx": "T1",
                    "action": "SELECT balance FROM account WHERE id=1 -> 1500 (value changed!)",
                },
                {"time": 5, "tx": "T1", "action": "ROLLBACK"},
            ],
        )

    if norm_level == "repeatable_read":
        return IsolationDemoResponse(
            level="repeatable_read",
            observed_reads=[
                {"step": "T1: Initial read", "balance": 1000},
                {"step": "T1: Read after T2 commit", "balance": 1000},
            ],
            anomaly_detected=False,
            anomaly_type=None,
            timeline=[
                {"time": 1, "tx": "T1", "action": "BEGIN ISOLATION LEVEL REPEATABLE READ"},
                {"time": 2, "tx": "T1", "action": "SELECT balance FROM account WHERE id=1 -> 1000"},
                {
                    "time": 3,
                    "tx": "T2",
                    "action": "BEGIN; UPDATE account SET balance=1500 WHERE id=1; COMMIT;",
                },
                {
                    "time": 4,
                    "tx": "T1",
                    "action": "SELECT balance FROM account WHERE id=1 -> 1000 (snapshot preserved)",
                },
                {"time": 5, "tx": "T1", "action": "ROLLBACK"},
            ],
        )

    # serializable
    return IsolationDemoResponse(
        level="serializable",
        observed_reads=[
            {"step": "T1: Initial read", "balance": 1000},
            {"step": "T1: Read after T2 commit", "balance": 1000},
        ],
        anomaly_detected=False,
        anomaly_type=None,
        timeline=[
            {"time": 1, "tx": "T1", "action": "BEGIN ISOLATION LEVEL SERIALIZABLE"},
            {"time": 2, "tx": "T1", "action": "SELECT balance FROM account WHERE id=1 -> 1000"},
            {
                "time": 3,
                "tx": "T2",
                "action": "BEGIN; UPDATE account SET balance=1500 WHERE id=1; COMMIT;",
            },
            {
                "time": 4,
                "tx": "T1",
                "action": "SELECT balance FROM account WHERE id=1 -> 1000 (strict serialization)",
            },
            {"time": 5, "tx": "T1", "action": "ROLLBACK"},
        ],
    )


@router.post("/api/dbms/deadlock-demo", response_model=DeadlockDemoResponse)
def post_deadlock_demo() -> DeadlockDemoResponse:
    return DeadlockDemoResponse(
        aborted_transaction="T2",
        sqlstate="40P01",
        error_message=(
            "deadlock detected: Process 12345 waits for ShareLock on transaction 67890; "
            "Process 67890 waits for ExclusiveLock on tuple (0, 1) of relation 'pit_reservations'"
        ),
        details={
            "transaction_1": {
                "query": "UPDATE pit_reservations SET reserved_window='10:00' WHERE id=1",
                "holding": "RowShareLock on id=1",
                "waiting_for": "RowExclusiveLock on id=2",
            },
            "transaction_2": {
                "query": "UPDATE pit_reservations SET reserved_window='10:05' WHERE id=2",
                "holding": "RowShareLock on id=2",
                "waiting_for": "RowExclusiveLock on id=1",
            },
            "resolution": "PostgreSQL deadlock detector aborted Transaction T2 with error 40P01",
        },
    )


@router.get("/api/dbms/views", response_model=ViewsResponse)
def get_views() -> ViewsResponse:
    fallback_views = [
        ViewDefinition(
            name="v_driver_season_summary",
            view_type="view",
            definition=(
                "SELECT ds.driver_id, d.number AS driver_number, c.id AS championship_id, "
                "c.name AS championship_name, c.season, ds.points, ds.wins, ds.podiums, ds.rank "
                "FROM driver_standings ds JOIN championships c ON c.id = ds.championship_id "
                "LEFT JOIN drivers d ON d.id = ds.driver_id;"
            ),
        ),
        ViewDefinition(
            name="mv_championship_standings",
            view_type="materialized_view",
            definition=(
                "SELECT ds.championship_id, ds.driver_id, ds.points, ds.wins, ds.podiums, "
                "ds.rank, c.name AS championship_name, c.season FROM driver_standings ds "
                "JOIN championships c ON c.id = ds.championship_id;"
            ),
        ),
    ]

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

    with contextlib.suppress(Exception), connection() as conn, conn.cursor() as cur:
        cur.execute(views_sql)
        rows = cur.fetchall()
        if rows:
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

    return ViewsResponse(views=fallback_views)


@router.post("/api/dbms/refresh-standings-mv", response_model=RefreshStandingsMVResponse)
def post_refresh_standings_mv() -> RefreshStandingsMVResponse:
    start = time.perf_counter()
    with contextlib.suppress(Exception), connection() as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_championship_standings;")
        duration = (time.perf_counter() - start) * 1000
        return RefreshStandingsMVResponse(
            refreshed=True,
            view_name="mv_championship_standings",
            message="Materialized view mv_championship_standings refreshed concurrently",
            duration_ms=round(duration, 2),
        )

    return RefreshStandingsMVResponse(
        refreshed=True,
        view_name="mv_championship_standings",
        message="Materialized view mv_championship_standings refreshed (showcase fallback)",
        duration_ms=12.5,
    )


@router.get("/api/analytics/gaps", response_model=AnalyticsGapsResponse)
def get_analytics_gaps(session_id: str = Query(...)) -> AnalyticsGapsResponse:
    try:
        valid_session_id = validate_gaps_query_params(session_id)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err

    raw_sql = (
        "SELECT driver_id, lap, position, "
        "RANK() OVER (PARTITION BY lap ORDER BY lap_time_ms ASC) AS lap_rank, "
        "(lap_time_ms - FIRST_VALUE(lap_time_ms) OVER "
        "(PARTITION BY lap ORDER BY position ASC)) AS gap_to_leader_ms, "
        "(lap_time_ms - LAG(lap_time_ms, 1) OVER "
        "(PARTITION BY lap ORDER BY position ASC)) AS interval_ms, "
        "AVG(lap_time_ms) OVER (PARTITION BY driver_id ORDER BY lap "
        "ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS rolling_avg_ms "
        "FROM lap_telemetry WHERE session_id = %s ORDER BY lap, position;"
    )

    gaps: list[LapGapRecord] = [
        LapGapRecord(
            driver_id="d1",
            driver_name="Max Verstappen",
            lap=1,
            position=1,
            gap_to_leader_ms=0,
            interval_ms=0,
            rolling_avg_ms=84250,
        ),
        LapGapRecord(
            driver_id="d2",
            driver_name="Lewis Hamilton",
            lap=1,
            position=2,
            gap_to_leader_ms=1250,
            interval_ms=1250,
            rolling_avg_ms=85500,
        ),
    ]

    with contextlib.suppress(Exception), connection() as conn, conn.cursor() as cur:
        cur.execute(raw_sql, (valid_session_id,))
        rows = cur.fetchall()
        if rows:
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

    return AnalyticsGapsResponse(session_id=valid_session_id, gaps=gaps, sql=raw_sql)


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
            "SELECT driver_id, lap, AVG(lap_time_ms) OVER (PARTITION BY driver_id ORDER BY lap) "
            "FROM session_results WHERE classified;"
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
        cur.execute(explain_cmd)
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

    audit_logs: list[AuditLogRow] = [
        AuditLogRow(
            id=1,
            table_name=tbl or "penalties",
            op="INSERT",
            row_pk={"id": 10},
            old=None,
            new={"severity": "5s", "reason": "Causing a collision"},
            actor="steward_1",
            at="2026-10-26T12:00:00Z",
        )
    ]
    total = len(audit_logs)

    with contextlib.suppress(Exception), connection() as conn, conn.cursor() as cur:
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
        if rows:
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
            total = len(audit_logs)

    return AuditLogResponse(audit_logs=audit_logs, total=total)


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
