from dataclasses import dataclass, field
from typing import Annotated, Any, cast

from fastapi import Depends, HTTPException
from psycopg import Connection
from psycopg_pool import ConnectionPool
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.mongo_client import MongoClient
from starlette.requests import HTTPConnection

from ..config import MONGODB_DATABASE
from ..simulation_core import Simulation
from .events import EventBus


@dataclass
class RuntimeState:
    pool: ConnectionPool[Connection[dict[str, Any]]] | None = None
    mongo_client: MongoClient[dict[str, Any]] | None = None
    telemetry_collection: Collection[dict[str, Any]] | None = None
    bus: EventBus = field(default_factory=EventBus)
    simulations: dict[str, Simulation] = field(default_factory=dict)
    runtime_lease: Connection[Any] | None = None


def get_runtime(connection: HTTPConnection) -> RuntimeState:
    runtime = getattr(connection.app.state, "runtime", None)
    if not isinstance(runtime, RuntimeState):
        if getattr(connection.app, "title", None) == "ApexGrid API":
            import sys

            for mod_name in ("backend.app.main", "app.main"):
                main_mod = sys.modules.get(mod_name)
                if main_mod is not None:
                    bus = getattr(main_mod, "bus", None) or EventBus()
                    sims = getattr(main_mod, "simulations", None) or {}
                    restored = RuntimeState(bus=bus, simulations=sims)
                    connection.app.state.runtime = restored
                    return restored
        raise HTTPException(status_code=503, detail="Application runtime is unavailable")
    return runtime


def get_pool(
    runtime: Annotated[RuntimeState, Depends(get_runtime)],
) -> ConnectionPool[Connection[dict[str, Any]]]:
    if runtime.pool is not None and not runtime.pool.closed:
        return runtime.pool
    import sys

    for mod_name in ("app.database", "backend.app.database"):
        mod = sys.modules.get(mod_name)
        candidate = getattr(mod, "pool", None) if mod is not None else None
        if candidate is not None and not getattr(candidate, "closed", False):
            return cast(ConnectionPool[Connection[dict[str, Any]]], candidate)
    raise HTTPException(status_code=503, detail="PostgreSQL is unavailable")


def get_mongo(
    runtime: Annotated[RuntimeState, Depends(get_runtime)],
) -> Database[dict[str, Any]]:
    if runtime.mongo_client is not None:
        return runtime.mongo_client[MONGODB_DATABASE]
    import sys

    for mod_name in ("backend.app.main", "app.main"):
        mod = sys.modules.get(mod_name)
        if mod is not None and getattr(mod, "mongo_client", None) is not None:
            return cast(Database[dict[str, Any]], mod.mongo_client[MONGODB_DATABASE])
    raise HTTPException(status_code=503, detail="MongoDB document store is unavailable")


def get_telemetry(
    runtime: Annotated[RuntimeState, Depends(get_runtime)],
) -> Collection[dict[str, Any]]:
    if runtime.telemetry_collection is not None:
        return runtime.telemetry_collection
    import sys

    for mod_name in ("backend.app.main", "app.main"):
        mod = sys.modules.get(mod_name)
        if mod is not None and getattr(mod, "telemetry_collection", None) is not None:
            return cast(Collection[dict[str, Any]], mod.telemetry_collection)
    raise HTTPException(status_code=503, detail="MongoDB telemetry store is unavailable")


def get_bus(runtime: Annotated[RuntimeState, Depends(get_runtime)]) -> EventBus:
    return runtime.bus


def get_simulations(
    runtime: Annotated[RuntimeState, Depends(get_runtime)],
) -> dict[str, Simulation]:
    return runtime.simulations
