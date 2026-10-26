from collections.abc import Callable
from typing import Any

from fastapi import APIRouter


def register_dbms_routes(
    app: Any,
    create_sql_router: Callable[..., tuple[APIRouter, dict[str, Callable[..., Any]]]],
    create_mongo_router: Callable[..., tuple[APIRouter, dict[str, Callable[..., Any]]]],
    fetch_all: Callable[..., Any],
    jsonable: Callable[[Any], Any],
    admin_dependency: Any,
    connection: Callable[[], Any],
    fetch_one: Callable[..., Any],
    mongo_ready: Callable[[], Any],
    mongo_database_ready: Callable[[], Any],
    mongodb_database_name: str,
) -> tuple[
    APIRouter,
    dict[str, Callable[..., Any]],
    APIRouter,
    dict[str, Callable[..., Any]],
]:
    sql_router, sql_handlers = create_sql_router(
        fetch_all,
        jsonable,
        admin_dependency,
        connection,
    )
    app.include_router(sql_router)

    mongo_router, mongo_handlers = create_mongo_router(
        fetch_one,
        jsonable,
        mongo_ready,
        admin_dependency,
        mongo_database_ready,
        mongodb_database_name,
        fetch_all,
    )
    app.include_router(mongo_router)
    return sql_router, sql_handlers, mongo_router, mongo_handlers
