from __future__ import annotations

import logging
import os
import threading
from typing import Any

from pymongo import MongoClient
from pymongo.collection import Collection

from .analytics_router import router as analytics_router
from .api.crud import crud_router
from .api.dbms_lock import router as dbms_lock_router
from .api.dbms_mongo import router as dbms_mongo_router
from .api.dbms_sql import router as dbms_sql_router
from .api.health import (
    legacy_router as legacy_health_router,
)
from .api.health import (
    register_legacy_health,
    register_readiness,
)
from .api.health import (
    router as health_router,
)
from .api.laps import dbms_race, dbms_race_laps, laps_router, session_laps
from .api.live import router as live_router
from .api.pit_write import pit_write_router
from .api.race_archive import race_archive_router
from .api.race_operation_routes import (
    results_read_router,
    results_write_router,
    session_action_router,
)
from .api.simulation import router as simulation_router
from .api.stewarding_reads import router as stewarding_reads_router
from .api.stewards import stewards_router
from .auth_router import auth_router
from .config import CORS_ORIGINS
from .core.application import create_application
from .core.events import EventBus
from .core.legacy_compat import resolve_legacy_symbol
from .core.lifespan import lifespan
from .core.lock_demo import create_lock_demo_helpers
from .core.runtime import RuntimeState
from .core.simulation_service import resume_or_create_auto_demo_race, simulations
from .database import connection, fetch_one
from .demo_race_router import router as demo_race_router
from .membership_router import router as membership_router
from .pit_router import router as pit_router
from .pit_strategy_router import router as pit_strategy_router
from .runtime_lease import check_runtime_lease
from .telemetry_router import router as telemetry_router
from .user_router import user_router

__all__ = ("app", "resume_or_create_auto_demo_race", "simulations")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("apexgrid")
mongo_client: MongoClient[dict[str, Any]] | None = None
telemetry_collection: Collection[dict[str, Any]] | None = None

app, require_runtime_lease = create_application(
    lifespan,
    CORS_ORIGINS,
    lambda lease: check_runtime_lease(lease),
    os.getenv("COOKIE_SECURE") == "1",
)

bus = EventBus()
app.state.runtime = RuntimeState(bus=bus, simulations=simulations)

health = register_legacy_health(lambda query: fetch_one(query), lambda: mongo_client)
health_ready = register_readiness(app, lambda: health(), lambda lease: check_runtime_lease(lease))
lock_demo_guard = threading.Lock()
_competing_lock_demo_reservation, _cleanup_lock_demo = create_lock_demo_helpers(
    lambda: connection()
)
race_history_handlers = {
    "dbms_race": dbms_race,
    "dbms_race_laps": dbms_race_laps,
    "session_laps": session_laps,
}

for router in (
    crud_router,
    membership_router,
    stewarding_reads_router,
    auth_router,
    user_router,
    session_action_router,
    results_read_router,
    results_write_router,
    stewards_router,
    pit_router,
    pit_write_router,
    telemetry_router,
    pit_strategy_router,
    demo_race_router,
    simulation_router,
    live_router,
    analytics_router,
    legacy_health_router,
    health_router,
    dbms_sql_router,
    dbms_mongo_router,
    race_archive_router,
    laps_router,
    dbms_lock_router,
):
    app.include_router(router)


def __getattr__(name: str) -> Any:
    val = resolve_legacy_symbol(name, __name__)
    if val is not None:
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
