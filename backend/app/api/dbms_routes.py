from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter

from .dbms_mongo import (
    create_dbms_mongo_router,
    mongo_handlers,
)
from .dbms_mongo import (
    router as dbms_mongo_router,
)
from .dbms_sql import (
    create_dbms_sql_router,
    sql_handlers,
)
from .dbms_sql import (
    router as dbms_sql_router,
)

sql_router = dbms_sql_router
mongo_router = dbms_mongo_router

__all__ = [
    "dbms_mongo_router",
    "dbms_sql_router",
    "mongo_router",
    "register_dbms_routes",
    "sql_router",
]


def register_dbms_routes(
    app: Any,
    create_sql_router: Callable[
        ..., tuple[APIRouter, dict[str, Callable[..., Any]]]
    ] = create_dbms_sql_router,
    create_mongo_router: Callable[
        ..., tuple[APIRouter, dict[str, Callable[..., Any]]]
    ] = create_dbms_mongo_router,
    fetch_all: Callable[..., Any] | None = None,
    jsonable: Callable[[Any], Any] | None = None,
    admin_dependency: Any = None,
    connection: Callable[[], Any] | None = None,
    fetch_one: Callable[..., Any] | None = None,
    mongo_ready: Callable[[], Any] | None = None,
    mongo_database_ready: Callable[[], Any] | None = None,
    mongodb_database_name: str = "",
) -> tuple[
    APIRouter,
    dict[str, Callable[..., Any]],
    APIRouter,
    dict[str, Callable[..., Any]],
]:
    if (
        create_sql_router is not create_dbms_sql_router
        or connection is not None
        or fetch_all is not None
        or jsonable is not None
    ):
        sql_rt, cur_sql_handlers = create_sql_router(
            fetch_all,
            jsonable,
            admin_dependency,
            connection,
        )
    else:
        sql_rt = dbms_sql_router
        cur_sql_handlers = sql_handlers

    if (
        create_mongo_router is not create_dbms_mongo_router
        or fetch_one is not None
        or jsonable is not None
        or mongo_ready is not None
        or mongo_database_ready is not None
    ):
        mongo_rt, cur_mongo_handlers = create_mongo_router(
            fetch_one,
            jsonable,
            mongo_ready,
            admin_dependency,
            mongo_database_ready,
            mongodb_database_name,
            fetch_all,
        )
    else:
        mongo_rt = dbms_mongo_router
        cur_mongo_handlers = mongo_handlers

    app.include_router(sql_rt)
    app.include_router(mongo_rt)
    return sql_rt, cur_sql_handlers, mongo_rt, cur_mongo_handlers
