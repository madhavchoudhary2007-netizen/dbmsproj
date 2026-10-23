from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Any, Literal

from fastapi import APIRouter
from psycopg import Connection
from psycopg.rows import tuple_row

from ..database import DatabaseRow


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

    return router, {
        "dbms_schema": dbms_schema,
        "dbms_indexes": dbms_indexes,
        "dbms_locks": dbms_locks,
        "dbms_eer": dbms_eer,
        "dbms_explain": dbms_explain,
    }
