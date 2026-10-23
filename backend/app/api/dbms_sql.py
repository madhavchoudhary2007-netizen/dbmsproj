from collections.abc import Callable
from typing import Any

from fastapi import APIRouter


def create_dbms_sql_router(
    fetch_all: Callable[..., Any],
    jsonable: Callable[[Any], Any],
    admin_dependency: Any,
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

    return router, {
        "dbms_schema": dbms_schema,
        "dbms_indexes": dbms_indexes,
        "dbms_locks": dbms_locks,
    }
