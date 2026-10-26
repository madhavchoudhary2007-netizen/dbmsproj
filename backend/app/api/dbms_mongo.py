from __future__ import annotations

from collections.abc import Callable
from contextlib import suppress
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pymongo import DESCENDING
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import PyMongoError

from ..core.request_database import DatabaseRow, DatabaseSession
from ..core.runtime import RuntimeState, get_mongo
from ..core.serialization import jsonable
from .laps import admin, get_race_db, get_race_telemetry

router = APIRouter()
mongo_router = router

admin_dependency = Depends(admin)


def get_mongo_db(request: Request) -> Database[dict[str, Any]]:
    if get_mongo in getattr(request.app, "dependency_overrides", {}):
        return cast(Database[dict[str, Any]], request.app.dependency_overrides[get_mongo]())

    import sys

    main_module = sys.modules.get("backend.app.main")
    m_ready = (
        getattr(main_module, "mongo_database_ready", None) if main_module is not None else None
    )
    orig_ready = (
        getattr(main_module, "_default_mongo_database_ready", None)
        if main_module is not None
        else None
    )
    if m_ready is not None and orig_ready is not None and m_ready is not orig_ready:
        return cast(Database[dict[str, Any]], m_ready())

    runtime = getattr(request.app.state, "runtime", None)
    if isinstance(runtime, RuntimeState) and runtime.mongo_client is not None:
        from ..config import MONGODB_DATABASE

        return runtime.mongo_client[MONGODB_DATABASE]

    if m_ready is not None:
        with suppress(HTTPException):
            return cast(Database[dict[str, Any]], m_ready())

    if isinstance(runtime, RuntimeState):
        return get_mongo(runtime)

    raise HTTPException(status_code=503, detail="MongoDB document store is unavailable")


def _resolve_mongo_db(
    database: Database[dict[str, Any]] | None = None,
) -> Database[dict[str, Any]]:
    if database is not None:
        return database
    import sys

    main_module = sys.modules.get("backend.app.main")
    m_ready = (
        getattr(main_module, "mongo_database_ready", None) if main_module is not None else None
    )
    if m_ready is not None:
        return cast(Database[dict[str, Any]], m_ready())
    raise HTTPException(status_code=503, detail="MongoDB document store is unavailable")


def _resolve_telemetry(
    request: Request | None = None,
    col: Collection[dict[str, Any]] | None = None,
) -> Collection[dict[str, Any]]:
    if col is not None:
        return col
    if request is not None:
        with suppress(Exception):
            return get_race_telemetry(request)
    import sys

    main_module = sys.modules.get("backend.app.main")
    m_mongo_ready = getattr(main_module, "mongo_ready", None) if main_module is not None else None
    if m_mongo_ready is not None:
        return cast(Collection[dict[str, Any]], m_mongo_ready())
    if request is not None:
        runtime = getattr(request.app.state, "runtime", None)
        if isinstance(runtime, RuntimeState) and runtime.telemetry_collection is not None:
            return runtime.telemetry_collection
    raise HTTPException(status_code=503, detail="MongoDB telemetry store is unavailable")


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


@router.get("/api/dbms/overview")
def dbms_overview(
    request: Request,
    user: Annotated[dict[str, Any] | None, admin_dependency] = None,
    database: Annotated[DatabaseSession | None, Depends(get_race_db)] = None,
) -> Any:
    db = _resolve_db(database)
    counts = (
        db.fetch_one("""SELECT
      (SELECT count(*) FROM race_sessions WHERE state='ACTIVE') AS active_sessions,
      (SELECT count(*) FROM race_sessions WHERE state='COMPLETED') AS completed_sessions,
      (SELECT count(*) FROM incident_reports WHERE state='OPEN') AS open_incidents,
      (SELECT count(*) FROM pit_reservations WHERE status='RESERVED') AS reserved_pit_stops,
      (SELECT count(*) FROM pit_reservations WHERE status='COMPLETED') AS completed_pit_stops,
      (SELECT count(*) FROM session_results) AS official_results""")
        or {}
    )
    try:
        telemetry = _resolve_telemetry(request=request)
        telemetry_samples: int | None = telemetry.count_documents({})
        mongo_status = "up"
    except (HTTPException, PyMongoError, Exception):
        telemetry_samples = None
        mongo_status = "down"
    return jsonable(
        {
            **counts,
            "telemetry_samples": telemetry_samples,
            "postgres": "up",
            "mongodb": mongo_status,
            "updated_at": datetime.now(UTC),
        }
    )


@router.get("/api/dbms/telemetry")
def dbms_telemetry(
    user: Annotated[dict[str, Any] | None, admin_dependency] = None,
    col: Annotated[Collection[dict[str, Any]] | None, Depends(get_race_telemetry)] = None,
) -> Any:
    try:
        telemetry = _resolve_telemetry(col=col)
        return {
            "store": "MongoDB",
            "count": telemetry.count_documents({}),
            "indexes": list(telemetry.index_information().keys()),
            "sample": jsonable(
                list(telemetry.find({}, {"_id": 0}).sort("ts", DESCENDING).limit(3))
            ),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(503, "Could not inspect MongoDB telemetry") from exc


@router.get("/api/dbms/mongo/collections")
def dbms_mongo_collections(
    user: Annotated[dict[str, Any] | None, admin_dependency] = None,
    database: Annotated[Database[dict[str, Any]] | None, Depends(get_mongo_db)] = None,
) -> Any:
    """List application collections with their actual document and index metadata."""
    try:
        db = _resolve_mongo_db(database)
        collections = []
        for name in sorted(
            name for name in db.list_collection_names() if not name.startswith("system.")
        ):
            collection = db[name]
            indexes = collection.index_information()
            collections.append(
                {
                    "name": name,
                    "document_count": collection.count_documents({}),
                    "indexes": [
                        {"name": index_name, **index} for index_name, index in indexes.items()
                    ],
                }
            )
        from ..config import MONGODB_DATABASE

        return {
            "store": "MongoDB",
            "database": MONGODB_DATABASE,
            "collections": collections,
            "updated_at": datetime.now(UTC),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(503, "Could not inspect MongoDB collections") from exc


@router.get("/api/dbms/mongo/collections/{collection_name}")
def dbms_mongo_collection_documents(
    collection_name: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session_id: str | None = Query(None, max_length=64),
    driver_id: str | None = Query(None, max_length=64),
    lap: int | None = Query(None, ge=1),
    sector: int | None = Query(None, ge=1, le=3),
    user: Annotated[dict[str, Any] | None, admin_dependency] = None,
    database: Annotated[Database[dict[str, Any]] | None, Depends(get_mongo_db)] = None,
) -> Any:
    (
        "Browse one real Mongo collection without permitting arbitrary collection "
        # Keep the docstring split within the configured line length.
        "names or query syntax."
    )
    try:
        db = _resolve_mongo_db(database)
        if (
            collection_name.startswith("system.")
            or collection_name not in db.list_collection_names()
        ):
            raise HTTPException(404, "MongoDB collection not found")
        filters = {
            key: value
            for key, value in {
                "session_id": session_id,
                "driver_id": driver_id,
                "lap": lap,
                "sector": sector,
            }.items()
            if value is not None
        }
        collection = db[collection_name]
        total = collection.count_documents(filters)
        cursor = collection.find(filters).sort("ts", DESCENDING).skip(offset).limit(limit)
        documents = [
            {
                **jsonable({key: value for key, value in document.items() if key != "_id"}),
                "id": str(document["_id"]),
            }
            for document in cursor
        ]
        return jsonable(
            {
                "collection": collection_name,
                "filters": filters,
                "documents": documents,
                "total": total,
                "limit": limit,
                "offset": offset,
                "updated_at": datetime.now(UTC),
            }
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(503, "Could not read MongoDB collection") from exc


@router.get("/api/dbms/polyglot")
def dbms_polyglot(
    user: Annotated[dict[str, Any] | None, admin_dependency] = None,
    database: Annotated[DatabaseSession | None, Depends(get_race_db)] = None,
    col: Annotated[Collection[dict[str, Any]] | None, Depends(get_race_telemetry)] = None,
) -> Any:
    sql = """SELECT s.id AS session_id,s.state,d.id AS driver_id,u.full_name
  FROM race_sessions s JOIN (
    SELECT session_id,driver_id FROM session_results
    UNION SELECT session_id,driver_id FROM demo_race_entries
  ) entry ON entry.session_id=s.id
  JOIN drivers d ON d.id=entry.driver_id JOIN users u ON u.id=d.user_id
  ORDER BY s.scheduled_at DESC LIMIT 50"""
    db = _resolve_db(database)
    rows = jsonable(db.fetch_all(sql))
    telemetry_col = _resolve_telemetry(col=col)
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    recent_cutoff = datetime.now(UTC) - timedelta(days=30)
    pipeline: list[dict[str, Any]] = [
        {"$match": {"ts": {"$gte": recent_cutoff}}},
        {"$sort": {"ts": -1}},
        {"$limit": 5000},
        {
            "$group": {
                "_id": {"session_id": "$session_id", "driver_id": "$driver_id"},
                "samples": {"$sum": 1},
                "latest": {"$max": "$ts"},
            }
        },
    ]
    for doc in telemetry_col.aggregate(pipeline):
        grouped[(doc["_id"]["session_id"], doc["_id"]["driver_id"])] = doc
    return {
        "relational_rows": len(rows),
        "rows": [
            {
                **r,
                "telemetry": grouped.get(
                    (str(r["session_id"]), str(r["driver_id"])), {"samples": 0}
                ),
            }
            for r in rows
        ],
    }


mongo_handlers: dict[str, Callable[..., Any]] = {
    "dbms_overview": dbms_overview,
    "dbms_telemetry": dbms_telemetry,
    "dbms_mongo_collections": dbms_mongo_collections,
    "dbms_mongo_collection_documents": dbms_mongo_collection_documents,
    "dbms_polyglot": dbms_polyglot,
}
dbms_mongo_handlers = mongo_handlers


def _register_collection_handlers(
    rt: APIRouter,
    admin_dep: Any,
    mongo_database_ready: Callable[[], Database[dict[str, Any]]],
    mongodb_database_name: str,
) -> dict[str, Callable[..., Any]]:
    @rt.get("/api/dbms/mongo/collections")
    def local_dbms_mongo_collections(user: Any = admin_dep) -> Any:
        """List application collections with their actual document and index metadata."""
        try:
            database = mongo_database_ready()
            collections = []
            for name in sorted(
                name for name in database.list_collection_names() if not name.startswith("system.")
            ):
                collection = database[name]
                indexes = collection.index_information()
                collections.append(
                    {
                        "name": name,
                        "document_count": collection.count_documents({}),
                        "indexes": [
                            {"name": index_name, **index} for index_name, index in indexes.items()
                        ],
                    }
                )
            return {
                "store": "MongoDB",
                "database": mongodb_database_name,
                "collections": collections,
                "updated_at": datetime.now(UTC),
            }
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(503, "Could not inspect MongoDB collections") from exc

    return {"dbms_mongo_collections": local_dbms_mongo_collections}


def _register_document_handlers(
    rt: APIRouter,
    admin_dep: Any,
    mongo_database_ready: Callable[[], Database[dict[str, Any]]],
    json_fn: Callable[[Any], Any],
) -> dict[str, Callable[..., Any]]:
    @rt.get("/api/dbms/mongo/collections/{collection_name}")
    def local_dbms_mongo_collection_documents(
        collection_name: str,
        limit: int = Query(50, ge=1, le=100),
        offset: int = Query(0, ge=0),
        session_id: str | None = Query(None, max_length=64),
        driver_id: str | None = Query(None, max_length=64),
        lap: int | None = Query(None, ge=1),
        sector: int | None = Query(None, ge=1, le=3),
        user: Any = admin_dep,
    ) -> Any:
        (
            "Browse one real Mongo collection without permitting arbitrary collection "
            # Keep the docstring split within the configured line length.
            "names or query syntax."
        )
        try:
            database = mongo_database_ready()
            if (
                collection_name.startswith("system.")
                or collection_name not in database.list_collection_names()
            ):
                raise HTTPException(404, "MongoDB collection not found")
            filters = {
                key: value
                for key, value in {
                    "session_id": session_id,
                    "driver_id": driver_id,
                    "lap": lap,
                    "sector": sector,
                }.items()
                if value is not None
            }
            collection = database[collection_name]
            total = collection.count_documents(filters)
            cursor = collection.find(filters).sort("ts", DESCENDING).skip(offset).limit(limit)
            documents = [
                {
                    **json_fn({key: value for key, value in document.items() if key != "_id"}),
                    "id": str(document["_id"]),
                }
                for document in cursor
            ]
            return json_fn(
                {
                    "collection": collection_name,
                    "filters": filters,
                    "documents": documents,
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                    "updated_at": datetime.now(UTC),
                }
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(503, "Could not read MongoDB collection") from exc

    return {"dbms_mongo_collection_documents": local_dbms_mongo_collection_documents}


def _register_polyglot_handler(
    rt: APIRouter,
    admin_dep: Any,
    json_fn: Callable[[Any], Any],
    mongo_ready: Callable[[], Collection[dict[str, Any]]],
    fetch_all: Callable[..., list[DatabaseRow]],
) -> dict[str, Callable[..., Any]]:
    @rt.get("/api/dbms/polyglot")
    def local_dbms_polyglot(user: Any = admin_dep) -> Any:
        sql = """SELECT s.id AS session_id,s.state,d.id AS driver_id,u.full_name
      FROM race_sessions s JOIN (
        SELECT session_id,driver_id FROM session_results
        UNION SELECT session_id,driver_id FROM demo_race_entries
      ) entry ON entry.session_id=s.id
      JOIN drivers d ON d.id=entry.driver_id JOIN users u ON u.id=d.user_id
      ORDER BY s.scheduled_at DESC LIMIT 50"""
        rows = json_fn(fetch_all(sql))
        col = mongo_ready()
        grouped: dict[tuple[str, str], dict[str, Any]] = {}
        recent_cutoff = datetime.now(UTC) - timedelta(days=30)
        pipeline: list[dict[str, Any]] = [
            {"$match": {"ts": {"$gte": recent_cutoff}}},
            {"$sort": {"ts": -1}},
            {"$limit": 5000},
            {
                "$group": {
                    "_id": {"session_id": "$session_id", "driver_id": "$driver_id"},
                    "samples": {"$sum": 1},
                    "latest": {"$max": "$ts"},
                }
            },
        ]
        for doc in col.aggregate(pipeline):
            grouped[(doc["_id"]["session_id"], doc["_id"]["driver_id"])] = doc
        return {
            "relational_rows": len(rows),
            "rows": [
                {
                    **r,
                    "telemetry": grouped.get(
                        (str(r["session_id"]), str(r["driver_id"])), {"samples": 0}
                    ),
                }
                for r in rows
            ],
        }

    return {"dbms_polyglot": local_dbms_polyglot}


def create_dbms_mongo_router(
    fetch_one: Callable[..., Any],
    jsonable: Callable[[Any], Any],
    mongo_ready: Callable[[], Collection[dict[str, Any]]],
    admin_dependency: Any,
    mongo_database_ready: Callable[[], Database[dict[str, Any]]],
    mongodb_database_name: str,
    fetch_all: Callable[..., list[DatabaseRow]],
) -> tuple[APIRouter, dict[str, Callable[..., Any]]]:
    rt = APIRouter()

    @rt.get("/api/dbms/overview")
    def local_dbms_overview(user: Any = admin_dependency) -> Any:
        counts = fetch_one("""SELECT
      (SELECT count(*) FROM race_sessions WHERE state='ACTIVE') AS active_sessions,
      (SELECT count(*) FROM race_sessions WHERE state='COMPLETED') AS completed_sessions,
      (SELECT count(*) FROM incident_reports WHERE state='OPEN') AS open_incidents,
      (SELECT count(*) FROM pit_reservations WHERE status='RESERVED') AS reserved_pit_stops,
      (SELECT count(*) FROM pit_reservations WHERE status='COMPLETED') AS completed_pit_stops,
      (SELECT count(*) FROM session_results) AS official_results""")
        try:
            telemetry_samples: int | None = mongo_ready().count_documents({})
            mongo_status = "up"
        except (HTTPException, PyMongoError):
            telemetry_samples = None
            mongo_status = "down"
        return jsonable(
            {
                **counts,
                "telemetry_samples": telemetry_samples,
                "postgres": "up",
                "mongodb": mongo_status,
                "updated_at": datetime.now(UTC),
            }
        )

    @rt.get("/api/dbms/telemetry")
    def local_dbms_telemetry(user: Any = admin_dependency) -> Any:
        try:
            col = mongo_ready()
            return {
                "store": "MongoDB",
                "count": col.count_documents({}),
                "indexes": list(col.index_information().keys()),
                "sample": jsonable(list(col.find({}, {"_id": 0}).sort("ts", DESCENDING).limit(3))),
            }
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(503, "Could not inspect MongoDB telemetry") from exc

    handlers = {
        "dbms_overview": local_dbms_overview,
        "dbms_telemetry": local_dbms_telemetry,
    }
    handlers.update(
        _register_collection_handlers(
            rt, admin_dependency, mongo_database_ready, mongodb_database_name
        )
    )
    handlers.update(
        _register_document_handlers(rt, admin_dependency, mongo_database_ready, jsonable)
    )
    handlers.update(
        _register_polyglot_handler(rt, admin_dependency, jsonable, mongo_ready, fetch_all)
    )
    return rt, handlers
