from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager
from datetime import UTC, datetime
from typing import Annotated, Any, Literal, cast

from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg import Connection, sql
from psycopg.errors import CheckViolation
from psycopg.rows import dict_row, tuple_row

from ..core.request_database import DatabaseRow, DatabaseSession
from ..core.serialization import jsonable
from .laps import admin, get_race_db

router = APIRouter()
sql_router = router

admin_dependency = Depends(admin)


def _resolve_db(database: DatabaseSession | None = None) -> DatabaseSession:
    if database is not None:
        return database
    import sys

    from .. import database as db_module

    main_module = sys.modules.get("backend.app.main")
    cur_fetch_one = (
        getattr(main_module, "fetch_one", db_module.fetch_one)
        if main_module is not None
        else db_module.fetch_one
    )
    cur_fetch_all = (
        getattr(main_module, "fetch_all", db_module.fetch_all)
        if main_module is not None
        else db_module.fetch_all
    )
    from .laps import _MonkeypatchedDatabaseSession

    return _MonkeypatchedDatabaseSession(cur_fetch_one, cur_fetch_all)


def _get_connection(
    database: DatabaseSession | None = None,
) -> AbstractContextManager[Connection[DatabaseRow]]:
    if database is not None and getattr(database, "pool", None) is not None:
        pool = database.pool
        if not pool.closed:
            return cast(AbstractContextManager[Connection[DatabaseRow]], pool.connection())
    import sys

    from .. import database as db_module

    main_module = sys.modules.get("backend.app.main")
    conn_fn = (
        getattr(main_module, "connection", db_module.connection)
        if main_module is not None
        else db_module.connection
    )
    return cast(AbstractContextManager[Connection[DatabaseRow]], conn_fn())


def public_dbms_tables(database: DatabaseSession | None = None) -> list[str]:
    db = _resolve_db(database)
    return [
        cast(str, row["table_name"])
        for row in db.fetch_all(
            """SELECT table_name FROM information_schema.tables
      WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY table_name"""
        )
    ]


@router.post("/api/dbms/constraint-demo", response_model=None)
def constraint_demo(
    user: Annotated[dict[str, Any] | None, admin_dependency] = None,
    database: Annotated[DatabaseSession | None, Depends(get_race_db)] = None,
) -> dict[str, Any]:
    with _get_connection(database) as conn, conn.cursor(row_factory=tuple_row) as cur:
        cur.execute("SAVEPOINT constraint_demo")
        try:
            cur.execute(
                "INSERT INTO drivers(licence_number,number,eligibility) VALUES ('APX-DEMO-CON"
                "STRAINT',-1,'ACTIVE')"
            )
            result: dict[str, Any] = {"constraint": "unexpectedly accepted"}
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


@router.post("/api/dbms/transaction-demo", response_model=None)
def transaction_demo(
    user: Annotated[dict[str, Any] | None, admin_dependency] = None,
    database: Annotated[DatabaseSession | None, Depends(get_race_db)] = None,
) -> dict[str, Any]:
    with _get_connection(database) as conn, conn.cursor(row_factory=tuple_row) as cur:
        cur.execute("SELECT txid_current()")
        txid = cast(tuple[Any, ...], cur.fetchone())[0]
        cur.execute(
            "CREATE TEMP TABLE IF NOT EXISTS transaction_demo_probe(value integer) ON COMMIT DROP"
        )
        cur.execute("TRUNCATE transaction_demo_probe")
        cur.execute("INSERT INTO transaction_demo_probe VALUES (1)")
        cur.execute("SELECT count(*) FROM transaction_demo_probe")
        before = cast(tuple[Any, ...], cur.fetchone())[0]
        cur.execute("SAVEPOINT tx_demo")
        cur.execute("INSERT INTO transaction_demo_probe VALUES (2)")
        cur.execute("SELECT count(*) FROM transaction_demo_probe")
        during = cast(tuple[Any, ...], cur.fetchone())[0]
        cur.execute("ROLLBACK TO SAVEPOINT tx_demo")
        cur.execute("SELECT count(*) FROM transaction_demo_probe")
        after = cast(tuple[Any, ...], cur.fetchone())[0]
    return {
        "transaction_id": txid,
        "before": before,
        "during": during,
        "after_rollback": after,
        "savepoint_rolled_back": during == 2 and after == before,
        "committed_effects": 0,
    }


@router.get("/api/dbms/tables", response_model=None)
def dbms_tables(
    user: Annotated[dict[str, Any] | None, admin_dependency] = None,
    database: Annotated[DatabaseSession | None, Depends(get_race_db)] = None,
) -> Any:
    names = public_dbms_tables(database)
    with _get_connection(database) as conn, conn.cursor(row_factory=dict_row) as cur:
        rows = []
        for name in names:
            cur.execute(
                sql.SQL("SELECT count(*) AS count FROM public.{}").format(sql.Identifier(name))
            )
            rows.append(
                {"table_name": name, "row_count": cast(DatabaseRow, cur.fetchone())["count"]}
            )
    return jsonable({"tables": rows, "updated_at": datetime.now(UTC)})


@router.get("/api/dbms/tables/{table_name}", response_model=None)
def dbms_table_rows(
    table_name: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: Annotated[dict[str, Any] | None, admin_dependency] = None,
    database: Annotated[DatabaseSession | None, Depends(get_race_db)] = None,
) -> Any:
    if table_name not in public_dbms_tables(database):
        raise HTTPException(404, "Database table not found")
    db = _resolve_db(database)
    columns = db.fetch_all(
        """SELECT column_name FROM information_schema.columns
  WHERE table_schema='public' AND table_name=%s ORDER BY ordinal_position""",
        (table_name,),
    )
    visible_columns = [
        row["column_name"] for row in columns if row["column_name"] not in {"password_hash"}
    ]
    primary_keys = db.fetch_all(
        """SELECT k.column_name FROM information_schema.table_constraints t
  JOIN information_schema.key_column_usage k ON k.constraint_name=t.constraint_name
    AND k.constraint_schema=t.constraint_schema AND k.table_name=t.table_name
  WHERE t.table_schema='public' AND t.table_name=%s AND t.constraint_type='PRIMARY KEY'
  ORDER BY k.ordinal_position""",
        (table_name,),
    )
    order_columns = [row["column_name"] for row in primary_keys] or visible_columns[:1]
    with _get_connection(database) as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            sql.SQL("SELECT {} FROM public.{} ORDER BY {} LIMIT %s OFFSET %s").format(
                sql.SQL(",").join(map(sql.Identifier, visible_columns)),
                sql.Identifier(table_name),
                sql.SQL(",").join(map(sql.Identifier, order_columns)),
            ),
            (limit, offset),
        )
        rows = cur.fetchall()
        cur.execute(
            sql.SQL("SELECT count(*) AS count FROM public.{}").format(sql.Identifier(table_name))
        )
        count = cast(DatabaseRow, cur.fetchone())["count"]
    return jsonable(
        {
            "table_name": table_name,
            "columns": visible_columns,
            "rows": rows,
            "total": count,
            "limit": limit,
            "offset": offset,
            "updated_at": datetime.now(UTC),
        }
    )


@router.get("/api/dbms/schema", response_model=None)
def dbms_schema(
    user: Annotated[dict[str, Any] | None, admin_dependency] = None,
    database: Annotated[DatabaseSession | None, Depends(get_race_db)] = None,
) -> Any:
    db = _resolve_db(database)
    return jsonable(
        db.fetch_all(
            "SELECT table_name,column_name,data_type,is_nullable FROM information_schema.columns"
            " WHERE table_schema='public' ORDER BY table_name,ordinal_position"
        )
    )


@router.get("/api/dbms/indexes", response_model=None)
def dbms_indexes(
    user: Annotated[dict[str, Any] | None, admin_dependency] = None,
    database: Annotated[DatabaseSession | None, Depends(get_race_db)] = None,
) -> Any:
    db = _resolve_db(database)
    return jsonable(
        db.fetch_all(
            "SELECT tablename,indexname,indexdef FROM pg_indexes WHERE schemaname='public'"
            " ORDER BY tablename,indexname"
        )
    )


@router.get("/api/dbms/locks", response_model=None)
def dbms_locks(
    user: Annotated[dict[str, Any] | None, admin_dependency] = None,
    database: Annotated[DatabaseSession | None, Depends(get_race_db)] = None,
) -> Any:
    db = _resolve_db(database)
    return jsonable(
        db.fetch_all(
            "SELECT locktype,mode,granted,relation::regclass::text AS relation,pid FROM pg_locks"
            " WHERE database=(SELECT oid FROM pg_database WHERE datname=current_database())"
            " ORDER BY granted,mode"
        )
    )


@router.get("/api/dbms/eer", response_model=None)
def dbms_eer(
    user: Annotated[dict[str, Any] | None, admin_dependency] = None,
    database: Annotated[DatabaseSession | None, Depends(get_race_db)] = None,
) -> dict[str, Any]:
    db = _resolve_db(database)
    columns = db.fetch_all(
        """SELECT c.table_name,c.column_name,c.data_type,EXISTS(SELECT """
        """1 FROM information_schema.key_column_usage k
  JOIN information_schema.table_constraints t ON """
        """t.constraint_name=k.constraint_name AND t.constraint_schema=k.constraint_schema
  WHERE t.constraint_type='PRIMARY KEY' AND k.table_schema='public' AND """
        """k.table_name=c.table_name AND k.column_name=c.column_name) AS primary_key
  FROM information_schema.columns c WHERE c.table_schema='public' ORDER BY """
        """c.table_name,c.ordinal_position"""
    )
    relationships = db.fetch_all(
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


@router.get("/api/dbms/explain", response_model=None)
def dbms_explain(
    query: Literal["leaderboard", "licence"],
    user: Annotated[dict[str, Any] | None, admin_dependency] = None,
    database: Annotated[DatabaseSession | None, Depends(get_race_db)] = None,
) -> dict[str, Any]:
    sql_text = {
        "leaderboard": (
            "SELECT driver_id,lap_time_ms FROM session_results WHERE session_id=(S"
            "ELECT id FROM race_sessions WHERE session_type='RACE' ORDER BY schedu"
            "led_at LIMIT 1) AND lap_time_ms IS NOT NULL ORDER BY session_id,lap_t"
            "ime_ms LIMIT 20"
        ),
        "licence": "SELECT id,licence_number FROM drivers WHERE licence_number='APX-DEMO'",
    }[query]
    with _get_connection(database) as conn, conn.cursor(row_factory=tuple_row) as cur:
        cur.execute("EXPLAIN (FORMAT JSON) " + sql_text)
        plan = cast(tuple[Any, ...], cur.fetchone())[0]
    return {"query": query, "plan": plan}


@router.get("/api/dbms/races", response_model=None)
def dbms_races(
    user: Annotated[dict[str, Any] | None, admin_dependency] = None,
    database: Annotated[DatabaseSession | None, Depends(get_race_db)] = None,
) -> Any:
    db = _resolve_db(database)
    return jsonable(
        db.fetch_all(
            """SELECT s.id,s.state,s.total_laps,s.started_at,s.ended_at,e.name AS """
            """event_name,c.name AS circuit_name
  FROM race_sessions s JOIN race_events e ON e.id=s.event_id JOIN circuits c ON """
            """c.id=e.circuit_id LEFT JOIN demo_races d ON d.session_id=s.id
  WHERE s.session_type='RACE' ORDER BY CASE WHEN s.state='ACTIVE' THEN 0 WHEN """
            """s.state='PAUSED' THEN 1 ELSE 2 END,COALESCE(d.auto_repeat,false) """
            """DESC,s.scheduled_at DESC LIMIT 200"""
        )
    )


sql_handlers: dict[str, Callable[..., Any]] = {
    "dbms_schema": dbms_schema,
    "dbms_indexes": dbms_indexes,
    "dbms_locks": dbms_locks,
    "dbms_eer": dbms_eer,
    "dbms_explain": dbms_explain,
    "dbms_races": dbms_races,
    "public_dbms_tables": public_dbms_tables,
    "constraint_demo": constraint_demo,
    "transaction_demo": transaction_demo,
    "dbms_tables": dbms_tables,
    "dbms_table_rows": dbms_table_rows,
}
dbms_sql_handlers = sql_handlers


def _register_demo_handlers(
    rt: APIRouter,
    admin_dep: Any,
    connection: Callable[[], AbstractContextManager[Connection[DatabaseRow]]],
) -> dict[str, Callable[..., Any]]:
    @rt.post("/api/dbms/constraint-demo", response_model=None)
    def local_constraint_demo(user: Any = admin_dep) -> dict[str, Any]:
        with connection() as conn, conn.cursor(row_factory=tuple_row) as cur:
            cur.execute("SAVEPOINT constraint_demo")
            try:
                cur.execute(
                    "INSERT INTO drivers(licence_number,number,eligibility) VALUES ('APX-DEMO-CON"
                    "STRAINT',-1,'ACTIVE')"
                )
                result: dict[str, Any] = {"constraint": "unexpectedly accepted"}
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

    @rt.post("/api/dbms/transaction-demo", response_model=None)
    def local_transaction_demo(user: Any = admin_dep) -> dict[str, Any]:
        with connection() as conn, conn.cursor(row_factory=tuple_row) as cur:
            cur.execute("SELECT txid_current()")
            txid = cast(tuple[Any, ...], cur.fetchone())[0]
            cur.execute(
                "CREATE TEMP TABLE IF NOT EXISTS transaction_demo_probe(value integer) "
                "ON COMMIT DROP"
            )
            cur.execute("TRUNCATE transaction_demo_probe")
            cur.execute("INSERT INTO transaction_demo_probe VALUES (1)")
            cur.execute("SELECT count(*) FROM transaction_demo_probe")
            before = cast(tuple[Any, ...], cur.fetchone())[0]
            cur.execute("SAVEPOINT tx_demo")
            cur.execute("INSERT INTO transaction_demo_probe VALUES (2)")
            cur.execute("SELECT count(*) FROM transaction_demo_probe")
            during = cast(tuple[Any, ...], cur.fetchone())[0]
            cur.execute("ROLLBACK TO SAVEPOINT tx_demo")
            cur.execute("SELECT count(*) FROM transaction_demo_probe")
            after = cast(tuple[Any, ...], cur.fetchone())[0]
        return {
            "transaction_id": txid,
            "before": before,
            "during": during,
            "after_rollback": after,
            "savepoint_rolled_back": during == 2 and after == before,
            "committed_effects": 0,
        }

    return {"constraint_demo": local_constraint_demo, "transaction_demo": local_transaction_demo}


def _register_table_handlers(
    rt: APIRouter,
    admin_dep: Any,
    connection: Callable[[], AbstractContextManager[Connection[DatabaseRow]]],
    json_fn: Callable[[Any], Any],
    tables_fn: Callable[[], list[str]],
) -> dict[str, Callable[..., Any]]:
    @rt.get("/api/dbms/tables", response_model=None)
    def local_dbms_tables(user: Any = admin_dep) -> Any:
        names = tables_fn()
        with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            rows = []
            for name in names:
                cur.execute(
                    sql.SQL("SELECT count(*) AS count FROM public.{}").format(sql.Identifier(name))
                )
                rows.append(
                    {"table_name": name, "row_count": cast(DatabaseRow, cur.fetchone())["count"]}
                )
        return json_fn({"tables": rows, "updated_at": datetime.now(UTC)})

    return {"dbms_tables": local_dbms_tables}


def _register_table_row_handler(
    rt: APIRouter,
    admin_dep: Any,
    connection: Callable[[], AbstractContextManager[Connection[DatabaseRow]]],
    json_fn: Callable[[Any], Any],
    tables_fn: Callable[[], list[str]],
    fetch_all: Callable[..., list[DatabaseRow]],
) -> dict[str, Callable[..., Any]]:
    @rt.get("/api/dbms/tables/{table_name}", response_model=None)
    def local_dbms_table_rows(
        table_name: str,
        limit: int = Query(50, ge=1, le=100),
        offset: int = Query(0, ge=0),
        user: Any = admin_dep,
    ) -> Any:
        if table_name not in tables_fn():
            raise HTTPException(404, "Database table not found")
        columns = fetch_all(
            """SELECT column_name FROM information_schema.columns
      WHERE table_schema='public' AND table_name=%s ORDER BY ordinal_position""",
            (table_name,),
        )
        visible_columns = [
            row["column_name"] for row in columns if row["column_name"] not in {"password_hash"}
        ]
        primary_keys = fetch_all(
            """SELECT k.column_name FROM information_schema.table_constraints t
      JOIN information_schema.key_column_usage k ON k.constraint_name=t.constraint_name
        AND k.constraint_schema=t.constraint_schema AND k.table_name=t.table_name
      WHERE t.table_schema='public' AND t.table_name=%s AND t.constraint_type='PRIMARY KEY'
      ORDER BY k.ordinal_position""",
            (table_name,),
        )
        order_columns = [row["column_name"] for row in primary_keys] or visible_columns[:1]
        with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                sql.SQL("SELECT {} FROM public.{} ORDER BY {} LIMIT %s OFFSET %s").format(
                    sql.SQL(",").join(map(sql.Identifier, visible_columns)),
                    sql.Identifier(table_name),
                    sql.SQL(",").join(map(sql.Identifier, order_columns)),
                ),
                (limit, offset),
            )
            rows = cur.fetchall()
            cur.execute(
                sql.SQL("SELECT count(*) AS count FROM public.{}").format(
                    sql.Identifier(table_name)
                )
            )
            count = cast(DatabaseRow, cur.fetchone())["count"]
        return json_fn(
            {
                "table_name": table_name,
                "columns": visible_columns,
                "rows": rows,
                "total": count,
                "limit": limit,
                "offset": offset,
                "updated_at": datetime.now(UTC),
            }
        )

    return {"dbms_table_rows": local_dbms_table_rows}


def create_dbms_sql_router(
    fetch_all: Callable[..., list[DatabaseRow]],
    jsonable: Callable[[Any], Any],
    admin_dependency: Any,
    connection: Callable[[], AbstractContextManager[Connection[DatabaseRow]]],
) -> tuple[APIRouter, dict[str, Callable[..., Any]]]:
    rt = APIRouter()

    def local_public_dbms_tables() -> list[str]:
        return [
            cast(str, row["table_name"])
            for row in fetch_all("""SELECT table_name FROM information_schema.tables
      WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY table_name""")
        ]

    demo_handlers = _register_demo_handlers(rt, admin_dependency, connection)
    table_handlers = _register_table_handlers(
        rt, admin_dependency, connection, jsonable, local_public_dbms_tables
    )
    table_row_handlers = _register_table_row_handler(
        rt, admin_dependency, connection, jsonable, local_public_dbms_tables, fetch_all
    )

    @rt.get("/api/dbms/schema", response_model=None)
    def local_dbms_schema(user: Any = admin_dependency) -> Any:
        return jsonable(
            fetch_all(
                "SELECT table_name,column_name,data_type,is_nullable FROM information_schema.colu"
                "mns WHERE table_schema='public' ORDER BY table_name,ordinal_position"
            )
        )

    @rt.get("/api/dbms/indexes", response_model=None)
    def local_dbms_indexes(user: Any = admin_dependency) -> Any:
        return jsonable(
            fetch_all(
                "SELECT tablename,indexname,indexdef FROM pg_indexes WHERE schemaname='public' OR"
                "DER BY tablename,indexname"
            )
        )

    @rt.get("/api/dbms/locks", response_model=None)
    def local_dbms_locks(user: Any = admin_dependency) -> Any:
        return jsonable(
            fetch_all(
                "SELECT locktype,mode,granted,relation::regclass::text AS relation,pid FROM pg_lo"
                "cks WHERE database=(SELECT oid FROM pg_database WHERE datname=current_database()"
                ") ORDER BY granted,mode"
            )
        )

    @rt.get("/api/dbms/eer", response_model=None)
    def local_dbms_eer(user: Any = admin_dependency) -> dict[str, Any]:
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

    @rt.get("/api/dbms/explain", response_model=None)
    def local_dbms_explain(
        query: Literal["leaderboard", "licence"], user: Any = admin_dependency
    ) -> dict[str, Any]:
        sql_text = {
            "leaderboard": (
                "SELECT driver_id,lap_time_ms FROM session_results WHERE session_id=(S"
                "ELECT id FROM race_sessions WHERE session_type='RACE' ORDER BY schedu"
                "led_at LIMIT 1) AND lap_time_ms IS NOT NULL ORDER BY session_id,lap_t"
                "ime_ms LIMIT 20"
            ),
            "licence": "SELECT id,licence_number FROM drivers WHERE licence_number='APX-DEMO'",
        }[query]
        with connection() as conn, conn.cursor(row_factory=tuple_row) as cur:
            cur.execute("EXPLAIN (FORMAT JSON) " + sql_text)
            plan = cast(tuple[Any, ...], cur.fetchone())[0]
        return {"query": query, "plan": plan}

    @rt.get("/api/dbms/races", response_model=None)
    def local_dbms_races(user: Any = admin_dependency) -> Any:
        return jsonable(
            fetch_all(
                """SELECT s.id,s.state,s.total_laps,s.started_at,s.ended_at,e.name AS """
                """event_name,c.name AS circuit_name
      FROM race_sessions s JOIN race_events e ON e.id=s.event_id JOIN circuits c ON """
                """c.id=e.circuit_id LEFT JOIN demo_races d ON d.session_id=s.id
      WHERE s.session_type='RACE' ORDER BY CASE WHEN s.state='ACTIVE' THEN 0 WHEN """
                """s.state='PAUSED' THEN 1 ELSE 2 END,COALESCE(d.auto_repeat,false) """
                """DESC,s.scheduled_at DESC LIMIT 200"""
            )
        )

    return rt, {
        "dbms_schema": local_dbms_schema,
        "dbms_indexes": local_dbms_indexes,
        "dbms_locks": local_dbms_locks,
        "dbms_eer": local_dbms_eer,
        "dbms_explain": local_dbms_explain,
        "dbms_races": local_dbms_races,
        "public_dbms_tables": local_public_dbms_tables,
        **demo_handlers,
        **table_handlers,
        **table_row_handlers,
    }
