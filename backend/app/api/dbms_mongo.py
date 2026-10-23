from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pymongo import DESCENDING
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import PyMongoError

from ..database import DatabaseRow


def create_dbms_mongo_router(
    fetch_one: Callable[..., Any],
    jsonable: Callable[[Any], Any],
    mongo_ready: Callable[[], Collection[dict[str, Any]]],
    admin_dependency: Any,
    mongo_database_ready: Callable[[], Database[dict[str, Any]]],
    mongodb_database_name: str,
    fetch_all: Callable[..., list[DatabaseRow]],
) -> tuple[APIRouter, dict[str, Callable[..., Any]]]:
    router = APIRouter()

    @router.get("/api/dbms/overview")
    def dbms_overview(user=admin_dependency):
        counts = fetch_one("""SELECT
      (SELECT count(*) FROM race_sessions WHERE state='ACTIVE') AS active_sessions,
      (SELECT count(*) FROM race_sessions WHERE state='COMPLETED') AS completed_sessions,
      (SELECT count(*) FROM incident_reports WHERE state='OPEN') AS open_incidents,
      (SELECT count(*) FROM pit_reservations WHERE status='RESERVED') AS reserved_pit_stops,
      (SELECT count(*) FROM pit_reservations WHERE status='COMPLETED') AS completed_pit_stops,
      (SELECT count(*) FROM session_results) AS official_results""")
        try:
            telemetry_samples = mongo_ready().count_documents({})
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

    @router.get("/api/dbms/telemetry")
    def dbms_telemetry(user=admin_dependency):
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
        "dbms_overview": dbms_overview,
        "dbms_telemetry": dbms_telemetry,
    }
    handlers.update(
        _register_collection_handlers(
            router, admin_dependency, mongo_database_ready, mongodb_database_name
        )
    )
    handlers.update(
        _register_document_handlers(router, admin_dependency, mongo_database_ready, jsonable)
    )
    handlers.update(
        _register_polyglot_handler(router, admin_dependency, jsonable, mongo_ready, fetch_all)
    )
    return router, handlers


def _register_polyglot_handler(
    router: APIRouter,
    admin_dependency: Any,
    jsonable: Callable[[Any], Any],
    mongo_ready: Callable[[], Collection[dict[str, Any]]],
    fetch_all: Callable[..., list[DatabaseRow]],
) -> dict[str, Callable[..., Any]]:
    @router.get("/api/dbms/polyglot")
    def dbms_polyglot(user=admin_dependency):
        sql = """SELECT s.id AS session_id,s.state,d.id AS driver_id,u.full_name
      FROM race_sessions s JOIN (
        SELECT session_id,driver_id FROM session_results
        UNION SELECT session_id,driver_id FROM demo_race_entries
      ) entry ON entry.session_id=s.id
      JOIN drivers d ON d.id=entry.driver_id JOIN users u ON u.id=d.user_id
      ORDER BY s.scheduled_at DESC LIMIT 50"""
        rows = jsonable(fetch_all(sql))
        col = mongo_ready()
        grouped = {}
        recent_cutoff = datetime.now(UTC) - timedelta(days=30)
        pipeline = [
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

    return {"dbms_polyglot": dbms_polyglot}


def _register_collection_handlers(
    router: APIRouter,
    admin_dependency: Any,
    mongo_database_ready: Callable[[], Database[dict[str, Any]]],
    MONGODB_DATABASE: str,
) -> dict[str, Callable[..., Any]]:
    @router.get("/api/dbms/mongo/collections")
    def dbms_mongo_collections(user=admin_dependency):
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
                "database": MONGODB_DATABASE,
                "collections": collections,
                "updated_at": datetime.now(UTC),
            }
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(503, "Could not inspect MongoDB collections") from exc

    return {"dbms_mongo_collections": dbms_mongo_collections}


def _register_document_handlers(
    router: APIRouter,
    admin_dependency: Any,
    mongo_database_ready: Callable[[], Database[dict[str, Any]]],
    jsonable: Callable[[Any], Any],
) -> dict[str, Callable[..., Any]]:
    @router.get("/api/dbms/mongo/collections/{collection_name}")
    def dbms_mongo_collection_documents(
        collection_name: str,
        limit: int = Query(50, ge=1, le=100),
        offset: int = Query(0, ge=0),
        session_id: str | None = Query(None, max_length=64),
        driver_id: str | None = Query(None, max_length=64),
        lap: int | None = Query(None, ge=1),
        sector: int | None = Query(None, ge=1, le=3),
        user=admin_dependency,
    ):
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

    return {"dbms_mongo_collection_documents": dbms_mongo_collection_documents}
