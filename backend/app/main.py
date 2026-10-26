from __future__ import annotations

import asyncio
import logging
import os
import random as random
import secrets as secrets
import threading
import time as time
from collections.abc import Callable
from concurrent.futures import Future as Future
from concurrent.futures import ThreadPoolExecutor as ThreadPoolExecutor
from concurrent.futures import TimeoutError as _FutureTimeout
from datetime import UTC as UTC
from datetime import datetime as datetime
from typing import Annotated, Any
from uuid import UUID as UUID
from uuid import uuid4 as uuid4

import jwt as jwt
from fastapi import (
    Depends,
    HTTPException,
    Request,
    WebSocket,
)
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pymongo import DESCENDING as DESCENDING
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from . import token_revocation
from .analytics_router import router as analytics_router
from .api.crud import create_crud_router, crud_router
from .api.dbms_lock import (
    create_dbms_lock_router as create_dbms_lock_router,
)
from .api.dbms_lock import (
    dbms_lock_demo as dbms_lock_demo,
)
from .api.dbms_lock import (
    dbms_recalculate as dbms_recalculate,
)
from .api.dbms_lock import (
    router as dbms_lock_router,
)
from .api.dbms_mongo import (
    create_dbms_mongo_router as create_dbms_mongo_router,
)
from .api.dbms_mongo import (
    dbms_mongo_collection_documents as dbms_mongo_collection_documents,
)
from .api.dbms_mongo import (
    dbms_mongo_collections as dbms_mongo_collections,
)
from .api.dbms_mongo import (
    dbms_mongo_handlers as dbms_mongo_handlers,
)
from .api.dbms_mongo import (
    dbms_overview as dbms_overview,
)
from .api.dbms_mongo import (
    dbms_polyglot as dbms_polyglot,
)
from .api.dbms_mongo import (
    dbms_telemetry as dbms_telemetry,
)
from .api.dbms_mongo import (
    router as dbms_mongo_router,
)
from .api.dbms_routes import register_dbms_routes as register_dbms_routes
from .api.dbms_sql import (
    constraint_demo as constraint_demo,
)
from .api.dbms_sql import (
    create_dbms_sql_router as create_dbms_sql_router,
)
from .api.dbms_sql import (
    dbms_eer as dbms_eer,
)
from .api.dbms_sql import (
    dbms_explain as dbms_explain,
)
from .api.dbms_sql import (
    dbms_indexes as dbms_indexes,
)
from .api.dbms_sql import (
    dbms_locks as dbms_locks,
)
from .api.dbms_sql import (
    dbms_races as dbms_races,
)
from .api.dbms_sql import (
    dbms_schema as dbms_schema,
)
from .api.dbms_sql import (
    dbms_sql_handlers as dbms_sql_handlers,
)
from .api.dbms_sql import (
    dbms_table_rows as dbms_table_rows,
)
from .api.dbms_sql import (
    dbms_tables as dbms_tables,
)
from .api.dbms_sql import (
    public_dbms_tables as public_dbms_tables,
)
from .api.dbms_sql import (
    router as dbms_sql_router,
)
from .api.dbms_sql import (
    transaction_demo as transaction_demo,
)
from .api.health import health_live as health_live
from .api.health import legacy_router as legacy_health_router
from .api.health import register_legacy_health, register_readiness
from .api.health import router as health_router
from .api.laps import (
    admin as admin,
)
from .api.laps import (
    dbms_race as dbms_race,
)
from .api.laps import (
    dbms_race_laps as dbms_race_laps,
)
from .api.laps import (
    get_race_db as get_race_db,
)
from .api.laps import (
    get_race_telemetry as get_race_telemetry,
)
from .api.laps import (
    laps_router as laps_router,
)
from .api.laps import (
    race_lap_measurements as race_lap_measurements,
)
from .api.laps import (
    session_laps as session_laps,
)
from .api.live import (
    create_live_router as create_live_router,
)
from .api.live import (
    router as live_router,
)
from .api.live import (
    session_ws as session_ws,
)
from .api.operations_routes import (
    register_operations_routes as register_operations_routes,
)
from .api.pit_write import (
    create_pit_write_router as create_pit_write_router,
)
from .api.pit_write import (
    pit_write_handlers as _pit_write_handlers,
)
from .api.pit_write import (
    pit_write_router as _pit_write_router,
)
from .api.pit_write import (
    reserve_pit as reserve_pit,
)
from .api.pit_write import (
    reserve_pit_auto as reserve_pit_auto,
)
from .api.pit_write import (
    update_pit_reservation as update_pit_reservation,
)
from .api.race_archive import (
    create_race_archive_router as create_race_archive_router,
)
from .api.race_archive import (
    race_archive_router as race_archive_router,
)
from .api.race_history_routes import (
    race_history_router as race_history_router,
)
from .api.race_history_routes import (
    register_race_history_routes as register_race_history_routes,
)
from .api.race_operation_routes import (
    recalculate as recalculate,
)
from .api.race_operation_routes import (
    register_race_operation_routers as register_race_operation_routers,
)
from .api.race_operation_routes import (
    results as results,
)
from .api.race_operation_routes import (
    results_read_handlers as results_read_handlers,
)
from .api.race_operation_routes import (
    results_read_router as results_read_router,
)
from .api.race_operation_routes import (
    results_write_handlers as results_write_handlers,
)
from .api.race_operation_routes import (
    results_write_router as results_write_router,
)
from .api.race_operation_routes import (
    save_results as save_results,
)
from .api.race_operation_routes import (
    session_action as session_action,
)
from .api.race_operation_routes import (
    session_action_handlers as session_action_handlers,
)
from .api.race_operation_routes import (
    session_action_router as session_action_router,
)
from .api.race_operation_routes import (
    standings as standings,
)
from .api.simulation import (
    control_simulation as control_simulation,
)
from .api.simulation import (
    create_simulation_router as create_simulation_router,
)
from .api.simulation import (
    router as simulation_router,
)
from .api.stewarding_reads import router as stewarding_reads_router
from .api.stewards import (
    create_incident as create_incident,
)
from .api.stewards import (
    create_stewards_router as create_stewards_router,
)
from .api.stewards import (
    decide_incident as decide_incident,
)
from .api.stewards import (
    get_incidents as get_incidents,
)
from .api.stewards import (
    stewards_handlers as stewards_handlers,
)
from .api.stewards import (
    stewards_router as stewards_router,
)
from .auth_cookie import verify_csrf_token
from .auth_router import (
    auth_router as auth_router,
)
from .auth_router import (
    create_auth_router as create_auth_router,
)
from .auth_router import (
    login as login,
)
from .auth_router import (
    logout as logout,
)
from .auth_router import (
    me as me,
)
from .auth_router import (
    refresh as refresh,
)
from .config import (
    APP_ENV as APP_ENV,
)
from .config import (
    CORS_ORIGINS,
    JWT_ALGORITHM,
    JWT_SECRET,
    MONGODB_DATABASE,
)
from .core.application import create_application
from .core.auth_dependencies import (
    check_allowed_origin,
    create_role_check,
    token_is_revoked,
)
from .core.events import EventBus as EventBus
from .core.http_auth import authenticate_http_user
from .core.lifespan import lifespan
from .core.lock_demo import create_lock_demo_helpers
from .core.runtime import RuntimeState as RuntimeState
from .core.security import websocket_bearer as websocket_bearer
from .core.serialization import jsonable
from .core.serialization import telemetry_ws_payload as telemetry_ws_payload
from .core.simulation_service import (
    _default_demo_race_row as _default_demo_race_row,
)
from .core.simulation_service import (
    _finalize_simulation_results as _finalize_simulation_results,
)
from .core.simulation_service import (
    _make_demo_race as _make_demo_race,
)
from .core.simulation_service import (
    _persist_simulation_tick as _persist_simulation_tick,
)
from .core.simulation_service import (
    _reset_session_simulation as _reset_session_simulation,
)
from .core.simulation_service import (
    _simulation_lease_is_valid as _simulation_lease_is_valid,
)
from .core.simulation_service import (
    _start_session_simulation as _start_session_simulation,
)
from .core.simulation_service import (
    cancel_automatic_pit_reservations as cancel_automatic_pit_reservations,
)
from .core.simulation_service import (
    clear_session_measurements as clear_session_measurements,
)
from .core.simulation_service import (
    demo_race_row as demo_race_row,
)
from .core.simulation_service import (
    ensure_session_reset_allowed as ensure_session_reset_allowed,
)
from .core.simulation_service import (
    launch_demo_simulation as launch_demo_simulation,
)
from .core.simulation_service import (
    record_simulated_incidents as record_simulated_incidents,
)
from .core.simulation_service import (
    refresh_simulation_pit_state as refresh_simulation_pit_state,
)
from .core.simulation_service import (
    restore_simulated_incidents as restore_simulated_incidents,
)
from .core.simulation_service import (
    restore_simulation_from_telemetry as restore_simulation_from_telemetry,
)
from .core.simulation_service import (
    resume_or_create_auto_demo_race as resume_or_create_auto_demo_race,
)
from .core.simulation_service import (
    schedule_simulation_pit_stops as schedule_simulation_pit_stops,
)
from .core.simulation_service import (
    simulation_loop as simulation_loop,
)
from .core.simulation_service import (
    simulation_tick_work as simulation_tick_work,
)
from .core.simulation_service import (
    simulations as simulations,
)
from .core.simulation_service import (
    sync_simulation_lifecycle as sync_simulation_lifecycle,
)
from .core.simulation_tick import advance_simulation_tick as advance_simulation_tick
from .core.validation import (
    validate_session_laps as validate_session_laps,
)
from .core.websocket_runtime import check_ws_runtime_lease as _check_ws_runtime_lease_impl
from .core.websocket_runtime import wait_for_ws_event as _wait_for_ws_event_impl
from .core.websocket_runtime import (
    websocket_authenticated_user as _websocket_authenticated_user_impl,
)
from .database import connection, fetch_one, get_pool
from .database import fetch_all as fetch_all
from .demo_names import generate_demo_names as generate_demo_names
from .demo_race_repository import DemoRaceDeleteConflict as DemoRaceDeleteConflict
from .demo_race_repository import DemoRaceSetupError as DemoRaceSetupError
from .demo_race_repository import choose_demo_car_numbers as choose_demo_car_numbers
from .demo_race_router import (
    create_demo_race_router as create_demo_race_router,
)
from .demo_race_router import (
    router as demo_race_router,
)
from .membership_router import router as membership_router
from .pit_repository import (
    create_automatic_reservation as create_automatic_reservation,
)
from .pit_router import router as pit_router
from .pit_strategy_router import (
    create_pit_strategy_router as create_pit_strategy_router,
)
from .pit_strategy_router import (
    pit_strategy as pit_strategy,
)
from .pit_strategy_router import (
    router as pit_strategy_router,
)
from .pit_strategy_service import PIT_TIRE_STINT_LAPS as PIT_TIRE_STINT_LAPS
from .runtime_lease import check_runtime_lease
from .schemas_competition import ResultIn as ResultIn
from .schemas_health import HealthReport as HealthReport
from .schemas_health import LivenessReport as LivenessReport
from .schemas_health import ReadinessReport as ReadinessReport
from .schemas_operations import Action as Action
from .schemas_operations import AutoReservationIn as AutoReservationIn
from .schemas_operations import Decision as Decision
from .schemas_operations import IncidentIn as IncidentIn
from .schemas_operations import ReservationIn as ReservationIn
from .schemas_operations import ReservationStatus as ReservationStatus
from .schemas_simulation import SimulationControl as SimulationControl
from .simulation_core import Simulation as Simulation
from .simulation_core import calculate_sector_performance as calculate_sector_performance
from .telemetry_router import (
    create_telemetry_router as create_telemetry_router,
)
from .telemetry_router import (
    router as telemetry_router,
)
from .user_router import (
    create_user as create_user,
)
from .user_router import (
    create_user_router as create_user_router,
)
from .user_router import (
    delete_user as delete_user,
)
from .user_router import (
    get_user as get_user,
)
from .user_router import (
    update_user as update_user,
)
from .user_router import (
    user_router as user_router,
)
from .user_router import (
    users as users,
)

FutureTimeout = _FutureTimeout

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("apexgrid")
bearer = HTTPBearer(auto_error=False)
mongo_client: MongoClient[dict[str, Any]] | None = None
telemetry_collection: Collection[dict[str, Any]] | None = None


app, require_runtime_lease = create_application(
    lifespan,
    CORS_ORIGINS,
    lambda lease: check_runtime_lease(lease),
    os.getenv("COOKIE_SECURE") == "1",
)


def require_db() -> None:
    if get_pool().closed:
        raise HTTPException(503, "PostgreSQL is unavailable")


def require_allowed_origin(request: Request) -> None:
    return check_allowed_origin(request, CORS_ORIGINS)


bearer_dependency = Depends(bearer)


def _token_is_revoked(claims: dict[str, Any], *, fail_closed: bool = False) -> bool:
    return token_is_revoked(
        claims,
        fail_closed=fail_closed,
        is_revoked=token_revocation.is_revoked,
    )


def current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = bearer_dependency,
) -> dict[str, Any]:
    user: dict[str, Any] = authenticate_http_user(
        request,
        credentials,
        JWT_SECRET=JWT_SECRET,
        JWT_ALGORITHM=JWT_ALGORITHM,
        _token_is_revoked=_token_is_revoked,
        require_allowed_origin=require_allowed_origin,
        verify_csrf_token=verify_csrf_token,
        fetch_one=fetch_one,
        jsonable=jsonable,
    )
    return user


authenticated_user_dependency = Depends(current_user)


def roles(*allowed: str) -> Callable[..., Any]:
    return create_role_check(allowed, authenticated_user_dependency)


admin_role_dependency = Depends(roles("ADMIN"))
admin_steward_dependency = Depends(roles("ADMIN", "STEWARD"))
admin_steward_principal_dependency = Depends(roles("ADMIN", "STEWARD", "PRINCIPAL"))


def admin_steward(
    user: Annotated[dict[str, Any], admin_steward_dependency],
) -> dict[str, Any]:
    return user


def crud_routes(
    resource: str, table: str, cols: tuple[str, ...], joins: str = "", select: str | None = None
) -> None:
    app.include_router(create_crud_router(resource, table, cols, joins, select))


app.include_router(crud_router)


app.include_router(membership_router)
app.include_router(stewarding_reads_router)


app.include_router(auth_router)
app.include_router(user_router)
login = login
logout = logout
me = me
refresh = refresh
users = users
get_user = get_user
create_user = create_user
update_user = update_user
delete_user = delete_user


app.include_router(session_action_router)
app.include_router(results_read_router)
app.include_router(results_write_router)
session_action = session_action
results = results
standings = standings
recalculate = recalculate
save_results = save_results


def _require_principal_own_team(team_id: UUID, user: dict[str, Any]) -> None:
    if user["role"] == "PRINCIPAL":
        own_team = fetch_one(
            "SELECT id FROM teams WHERE id=%s AND principal_user_id=%s", (team_id, user["id"])
        )
        if not own_team:
            raise HTTPException(403, "Principals may reserve pit boxes only for their own team")


_default_require_principal_own_team = _require_principal_own_team

app.include_router(stewards_router)
app.include_router(pit_router)
app.include_router(_pit_write_router)
pit_write_router = _pit_write_router
pit_write_handlers = _pit_write_handlers

get_incidents = get_incidents
create_incident = create_incident
decide_incident = decide_incident
reserve_pit = reserve_pit
reserve_pit_auto = reserve_pit_auto
update_pit_reservation = update_pit_reservation
stewards_handlers = stewards_handlers
_pit_write_handlers = _pit_write_handlers


def mongo_ready() -> Collection[dict[str, Any]]:
    if telemetry_collection is None:
        raise HTTPException(503, "MongoDB telemetry store is unavailable")
    return telemetry_collection


_default_mongo_ready = mongo_ready


def publish(session_id: UUID | str, kind: str, data: Any) -> None:
    bus.send(
        session_id,
        {
            "type": kind,
            "ts": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "session_id": str(session_id),
            "data": jsonable(data),
        },
    )


_default_publish = publish


app.include_router(telemetry_router)
app.include_router(pit_strategy_router)
pit_strategy = pit_strategy


bus = EventBus()
app.state.runtime = RuntimeState(bus=bus, simulations=simulations)

app.include_router(demo_race_router)
app.include_router(simulation_router)


async def _check_ws_runtime_lease(ws: WebSocket) -> bool:
    return await _check_ws_runtime_lease_impl(ws, check_runtime_lease)


async def _wait_for_ws_event(ws: WebSocket, queue: asyncio.Queue[Any]) -> dict[str, Any] | None:
    return await _wait_for_ws_event_impl(ws, queue, _check_ws_runtime_lease)


def _websocket_authenticated_user(token: str) -> Any:
    return _websocket_authenticated_user_impl(
        token, JWT_SECRET, JWT_ALGORITHM, _token_is_revoked, fetch_one
    )


app.include_router(live_router)


app.include_router(analytics_router)


health = register_legacy_health(lambda query: fetch_one(query), lambda: mongo_client)
app.include_router(legacy_health_router)


health_ready = register_readiness(
    app,
    lambda: health(),
    lambda lease: check_runtime_lease(lease),
)
app.include_router(health_router)


admin_dependency = Depends(admin)


app.include_router(dbms_sql_router)
app.include_router(dbms_mongo_router)


app.include_router(race_archive_router)
app.include_router(laps_router)
race_history_handlers = {
    "dbms_race": dbms_race,
    "dbms_race_laps": dbms_race_laps,
    "session_laps": session_laps,
}


def mongo_database_ready() -> Database[dict[str, Any]]:
    if mongo_client is None:
        raise HTTPException(503, "MongoDB document store is unavailable")
    return mongo_client[MONGODB_DATABASE]


_default_mongo_database_ready = mongo_database_ready


lock_demo_guard = threading.Lock()

_competing_lock_demo_reservation, _cleanup_lock_demo = create_lock_demo_helpers(
    lambda: connection()
)

app.include_router(dbms_lock_router)
