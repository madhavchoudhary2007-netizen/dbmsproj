from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from pymongo import MongoClient

from ..config import APP_ENV, AUTO_DEMO_RACE, MONGODB_DATABASE, MONGODB_URL
from ..database import close_pool, get_pool, open_pool
from ..runtime_lease import acquire_runtime_lease
from .runtime import RuntimeState

log = logging.getLogger("apexgrid")


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    # Import at startup so main's live singletons and deferred demo helper remain
    # the source of truth without creating an import cycle during app creation.
    from .. import main

    runtime_lease = acquire_runtime_lease()
    application.state.runtime_lease = runtime_lease
    runtime = RuntimeState(bus=main.bus, simulations=main.simulations, runtime_lease=runtime_lease)
    application.state.runtime = runtime
    try:
        open_pool()
    except Exception:
        log.exception("PostgreSQL pool could not open")
    runtime.pool = get_pool()
    try:
        main.mongo_client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=1800)
        main.mongo_client.admin.command("ping")
        main.telemetry_collection = main.mongo_client[MONGODB_DATABASE]["telemetry"]
        main.telemetry_collection.create_index([("session_id", 1), ("ts", -1)])
        main.telemetry_collection.create_index([("driver_id", 1), ("ts", -1)])
        main.telemetry_collection.create_index([("session_id", 1), ("driver_id", 1), ("ts", -1)])
    except Exception:
        log.warning("MongoDB is not available at startup", exc_info=True)
    runtime.mongo_client = main.mongo_client
    runtime.telemetry_collection = main.telemetry_collection
    if APP_ENV == "local" and not get_pool().closed and main.telemetry_collection is not None:
        try:
            await main.resume_or_create_auto_demo_race(create_if_missing=AUTO_DEMO_RACE)
        except Exception:
            log.exception("Automatic local demo race could not be started")

    try:
        yield
    finally:
        try:
            tasks = [
                sim.task for sim in main.simulations.values() if sim.task and not sim.task.done()
            ]
            for task in tasks:
                task.cancel()
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            if main.mongo_client:
                main.mongo_client.close()
            main.mongo_client = None
            main.telemetry_collection = None
            with suppress(Exception):
                close_pool()
        finally:
            runtime.pool = None
            runtime.mongo_client = None
            runtime.telemetry_collection = None
            runtime.runtime_lease = None
            application.state.runtime = None
            application.state.runtime_lease = None
            runtime_lease.close()
