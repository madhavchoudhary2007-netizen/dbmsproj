from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from psycopg import Connection
from psycopg.errors import CheckViolation
from psycopg.rows import tuple_row

from ..database import DatabaseRow


def _register_demo_handlers(
    router: APIRouter,
    admin_dependency: Any,
    connection: Callable[[], AbstractContextManager[Connection[DatabaseRow]]],
) -> dict[str, Callable[..., Any]]:
    @router.post("/api/dbms/constraint-demo")
    def constraint_demo(user=admin_dependency):
        with connection() as conn, conn.cursor(row_factory=tuple_row) as cur:
            cur.execute("SAVEPOINT constraint_demo")
            try:
                cur.execute(
                    "INSERT INTO drivers(licence_number,number,eligibility) VALUES ('APX-DEMO-CON"
                    "STRAINT',-1,'ACTIVE')"
                )
                result = {"constraint": "unexpectedly accepted"}
                cur.execute("ROLLBACK TO SAVEPOINT constraint_demo")
            except CheckViolation as exc:
                constraint = getattr(exc.diag, "constraint_name", None)
                cur.execute("ROLLBACK TO SAVEPOINT constraint_demo")
                if constraint != "drivers_number_check":
                    raise HTTPException(
                        500, "Invalid driver row failed an unexpected check constraint"
                    ) from exc
                result = {"constraint": constraint, "rejected": True, "sqlstate": exc.sqlstate}
            cur.execute("RELEASE SAVEPOINT constraint_demo")
        if result.get("constraint") == "unexpectedly accepted":
            raise HTTPException(500, "Database accepted a driver number outside the allowed range")
        return result

    @router.post("/api/dbms/transaction-demo")
    def transaction_demo(user=admin_dependency):
        with connection() as conn, conn.cursor(row_factory=tuple_row) as cur:
            cur.execute("SELECT txid_current()")
            txid = cur.fetchone()[0]
            cur.execute(
                "CREATE TEMP TABLE IF NOT EXISTS transaction_demo_probe(value integer) "
                "ON COMMIT DROP"
            )
            cur.execute("TRUNCATE transaction_demo_probe")
            cur.execute("INSERT INTO transaction_demo_probe VALUES (1)")
            cur.execute("SELECT count(*) FROM transaction_demo_probe")
            before = cur.fetchone()[0]
            cur.execute("SAVEPOINT tx_demo")
            cur.execute("INSERT INTO transaction_demo_probe VALUES (2)")
            cur.execute("SELECT count(*) FROM transaction_demo_probe")
            during = cur.fetchone()[0]
            cur.execute("ROLLBACK TO SAVEPOINT tx_demo")
            cur.execute("SELECT count(*) FROM transaction_demo_probe")
            after = cur.fetchone()[0]
        return {
            "transaction_id": txid,
            "before": before,
            "during": during,
            "after_rollback": after,
            "savepoint_rolled_back": during == 2 and after == before,
            "committed_effects": 0,
        }

    return {"constraint_demo": constraint_demo, "transaction_demo": transaction_demo}


def create_dbms_sql_router(
    fetch_all: Callable[..., Any],
    jsonable: Callable[[Any], Any],
    admin_dependency: Any,
    connection: Callable[[], AbstractContextManager[Connection[DatabaseRow]]],
) -> tuple[APIRouter, dict[str, Callable[..., Any]]]:
    router = APIRouter()

    @router.get("/api/dbms/schema")
    def dbms_schema(user=admin_dependency):
        return jsonable(
            fetch_all(
                "SELECT table_name,column_name,data_type,is_nullable FROM information_schema.colu"
                "mns WHERE table_schema='public' ORDER BY table_name,ordinal_position"
            )
        )

    @router.get("/api/dbms/indexes")
    def dbms_indexes(user=admin_dependency):
        return jsonable(
            fetch_all(
                "SELECT tablename,indexname,indexdef FROM pg_indexes WHERE schemaname='public' OR"
                "DER BY tablename,indexname"
            )
        )

    @router.get("/api/dbms/locks")
    def dbms_locks(user=admin_dependency):
        return jsonable(
            fetch_all(
                "SELECT locktype,mode,granted,relation::regclass::text AS relation,pid FROM pg_lo"
                "cks WHERE database=(SELECT oid FROM pg_database WHERE datname=current_database()"
                ") ORDER BY granted,mode"
            )
        )

    @router.get("/api/dbms/eer")
    def dbms_eer(user=admin_dependency):
        columns = fetch_all(
            """SELECT c.table_name,c.column_name,c.data_type,EXISTS(SELECT """
            """1 FROM information_schema.key_column_usage k
      JOIN information_schema.table_constraints t ON """
            """t.constraint_name=k.constraint_name AND t.constraint_schema=k.constraint_schema
      WHERE t.constraint_type='PRIMARY KEY' AND k.table_schema='public' AND """
            """k.table_name=c.table_name AND k.column_name=c.column_name) AS primary_key
      FROM information_schema.columns c WHERE c.table_schema='public' ORDER BY """
            """c.table_name,c.ordinal_position"""
        )
        relationships = fetch_all(
            """SELECT DISTINCT child.relname AS child,ca.attname AS """
            """foreign_key,parent.relname AS parent,
      pa.attname AS parent_key,NOT ca.attnotnull AS optional,
      CASE WHEN EXISTS(SELECT 1 FROM pg_constraint uq WHERE uq.conrelid=f.conrelid AND """
            """uq.contype IN ('p','u') AND uq.conkey <@ f.conkey)
        THEN '0..1' ELSE '0..many' END AS children_per_parent
      FROM pg_constraint f JOIN pg_class child ON child.oid=f.conrelid JOIN """
            """pg_namespace ns ON ns.oid=child.relnamespace
      JOIN pg_class parent ON parent.oid=f.confrelid
      CROSS JOIN LATERAL unnest(f.conkey,f.confkey) AS pair(child_num,parent_num)
      JOIN pg_attribute ca ON ca.attrelid=f.conrelid AND ca.attnum=pair.child_num
      JOIN pg_attribute pa ON pa.attrelid=f.confrelid AND pa.attnum=pair.parent_num
      WHERE f.contype='f' AND ns.nspname='public' ORDER BY child.relname,ca.attname"""
        )
        return {"columns": columns, "relationships": relationships}

    @router.get("/api/dbms/explain")
    def dbms_explain(query: Literal["leaderboard", "licence"], user=admin_dependency):
        sql = {
            "leaderboard": (
                "SELECT driver_id,lap_time_ms FROM session_results WHERE session_id=(S"
                "ELECT id FROM race_sessions WHERE session_type='RACE' ORDER BY schedu"
                "led_at LIMIT 1) AND lap_time_ms IS NOT NULL ORDER BY session_id,lap_t"
                "ime_ms LIMIT 20"
            ),
            "licence": "SELECT id,licence_number FROM drivers WHERE licence_number='APX-DEMO'",
        }[query]
        with connection() as conn, conn.cursor(row_factory=tuple_row) as cur:
            cur.execute("EXPLAIN (FORMAT JSON) " + sql)
            plan = cur.fetchone()[0]
        return {"query": query, "plan": plan}

    @router.get("/api/dbms/races")
    def dbms_races(user=admin_dependency):
        return jsonable(
            fetch_all(
                """SELECT s.id,s.state,s.total_laps,s.started_at,s.ended_at,e.name AS """
                """event_name,c.name AS circuit_name
      FROM race_sessions s JOIN race_events e ON e.id=s.event_id JOIN circuits c ON """
                """c.id=e.circuit_id LEFT JOIN demo_races d ON d.session_id=s.id
      WHERE s.session_type='RACE' ORDER BY CASE WHEN s.state='ACTIVE' THEN 0 WHEN """
                """s.state='PAUSED' THEN 1 ELSE 2 END,COALESCE(d.auto_repeat,false) """
                """DESC,s.scheduled_at DESC"""
            )
        )

    demo_handlers = _register_demo_handlers(router, admin_dependency, connection)

    return router, {
        "dbms_schema": dbms_schema,
        "dbms_indexes": dbms_indexes,
        "dbms_locks": dbms_locks,
        "dbms_eer": dbms_eer,
        "dbms_explain": dbms_explain,
        "dbms_races": dbms_races,
        **demo_handlers,
    }
