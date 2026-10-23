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

    return router, {"dbms_schema": dbms_schema}
