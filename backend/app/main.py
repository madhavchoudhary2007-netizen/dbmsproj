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
from .api.crud import create_crud_router
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
from .core.events import EventBus
from .core.http_auth import authenticate_http_user
from .core.lifespan import lifespan
from .core.lock_demo import create_lock_demo_helpers
from .core.runtime import RuntimeState as RuntimeState
from .core.security import websocket_bearer as websocket_bearer
from .core.serialization import jsonable
from .core.serialization import telemetry_ws_payload as telemetry_ws_payload
from .core.simulation_tick import advance_simulation_tick as advance_simulation_tick
from .core.validation import (
    _crud_write_payload,
    _require_crud_record,
    limit_offset,
    validate_session_laps,
)
from .core.websocket_runtime import check_ws_runtime_lease as _check_ws_runtime_lease_impl
from .core.websocket_runtime import wait_for_ws_event as _wait_for_ws_event_impl
from .core.websocket_runtime import (
    websocket_authenticated_user as _websocket_authenticated_user_impl,
)
from .crud_repository import (
    create_crud_row,
    delete_crud_row,
    get_crud_row,
    list_crud_rows,
    update_crud_row,
)
from .crud_resources import register_resources
from .database import connection, fetch_all, fetch_one, get_pool
from .demo_names import generate_demo_names as generate_demo_names
from .demo_race_repository import DemoRaceDeleteConflict as DemoRaceDeleteConflict
from .demo_race_repository import DemoRaceSetupError as DemoRaceSetupError
from .demo_race_repository import choose_demo_car_numbers as choose_demo_car_numbers
from .demo_race_repository import (
    create_demo_race_records,
    get_demo_race_row,
)
from .demo_race_router import (
    create_demo_race_router as create_demo_race_router,
)
from .demo_race_router import (
    router as demo_race_router,
)
from .demo_runtime import build_demo_race
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
from .pit_strategy_service import (
    tire_stint_target,
)
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
from .schemas_simulation import SimulationControl
from .session_measurements import clear_measurements, ensure_reset_allowed
from .simulation_core import MAX_SESSION_LAPS
from .simulation_core import Simulation as Simulation
from .simulation_core import calculate_sector_performance as calculate_sector_performance
from .simulation_finish import finalize_results
from .simulation_incidents import record_generated_incidents
from .simulation_lifecycle import sync_lifecycle
from .simulation_persist import persist_tick
from .simulation_pit import (
    cancel_automatic_reservations,
    refresh_pit_state,
    schedule_pit_stops,
)
from .simulation_reset import reset_simulation
from .simulation_restore import (
    restore_incident_state,
    restore_or_create_demo,
    restore_telemetry_state,
)
from .simulation_runner import run_simulation_loop
from .simulation_start import start_simulation
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
    app.include_router(
        create_crud_router(
            resource,
            table,
            cols,
            joins,
            select,
            authenticated_user_dependency=authenticated_user_dependency,
            admin_role_dependency=admin_role_dependency,
            limit_offset=lambda *args, **kwargs: limit_offset(*args, **kwargs),
            jsonable=lambda *args, **kwargs: jsonable(*args, **kwargs),
            list_crud_rows=lambda *args, **kwargs: list_crud_rows(*args, **kwargs),
            get_crud_row=lambda *args, **kwargs: get_crud_row(*args, **kwargs),
            _require_crud_record=lambda *args, **kwargs: _require_crud_record(*args, **kwargs),
            _crud_write_payload=lambda *args, **kwargs: _crud_write_payload(*args, **kwargs),
            validate_session_laps=lambda *args, **kwargs: validate_session_laps(*args, **kwargs),
            create_crud_row=lambda *args, **kwargs: create_crud_row(*args, **kwargs),
            fetch_one=lambda *args, **kwargs: fetch_one(*args, **kwargs),
            update_crud_row=lambda *args, **kwargs: update_crud_row(*args, **kwargs),
            delete_crud_row=lambda *args, **kwargs: delete_crud_row(*args, **kwargs),
            get_telemetry_collection=lambda: telemetry_collection,
        )
    )


register_resources(crud_routes)


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


def demo_race_row(session_id: UUID | str) -> dict[str, Any] | None:
    row = get_demo_race_row(session_id)
    if not row:
        return None
    result: dict[str, Any] = jsonable(row)
    sim = simulations.get(str(session_id))
    result["simulation_state"] = sim.status if sim else "stopped"
    return result


_default_demo_race_row = demo_race_row


def _make_demo_race(cars: int | None = None, auto_repeat: bool = False) -> dict[str, Any] | None:
    result: dict[str, Any] | None = build_demo_race(
        cars,
        auto_repeat,
        mongo_ready,
        create_demo_race_records,
        simulations,
        demo_race_row,
    )
    return result


def launch_demo_simulation(session_id: UUID | str) -> None:
    sim = simulations[str(session_id)]
    sim.status = "running"
    sim.task = asyncio.create_task(simulation_loop(sim))


app.include_router(demo_race_router)


def restore_simulation_from_telemetry(sim: Simulation) -> None:
    return restore_telemetry_state(sim, lambda: mongo_ready())


def restore_simulated_incidents(sim: Simulation) -> None:
    return restore_incident_state(sim, lambda *a, **kw: fetch_all(*a, **kw))


async def resume_or_create_auto_demo_race(create_if_missing: bool = True) -> None:
    await restore_or_create_demo(
        create_if_missing,
        lambda *args, **kwargs: fetch_all(*args, **kwargs),
        log,
        lambda sim: restore_simulation_from_telemetry(sim),
        lambda sim: restore_simulated_incidents(sim),
        lambda *args, **kwargs: launch_demo_simulation(*args, **kwargs),
        lambda *args, **kwargs: _make_demo_race(*args, **kwargs),
        simulations,
    )


bus = EventBus()


simulations: dict[str, Simulation] = {}
app.state.runtime = RuntimeState(bus=bus, simulations=simulations)


def sync_simulation_lifecycle(session_id: UUID, action: str) -> None:
    sync_lifecycle(session_id, action, simulations)


def ensure_session_reset_allowed(session_id: UUID | str) -> None:
    return ensure_reset_allowed(session_id, fetch_one)


def clear_session_measurements(session_id: UUID | str) -> None:
    return clear_measurements(session_id, mongo_ready, connection, publish)


def refresh_simulation_pit_state(sim: Simulation, timestamp: datetime) -> None:
    refresh_pit_state(sim, timestamp, connection, publish, tire_stint_target)


def schedule_simulation_pit_stops(sim: Simulation, packets: list[dict[str, Any]]) -> None:
    return schedule_pit_stops(
        sim, packets, tire_stint_target, create_automatic_reservation, publish, log
    )


def record_simulated_incidents(sim: Simulation, packets: list[dict[str, Any]]) -> None:
    return record_generated_incidents(sim, packets, connection, publish)


def cancel_automatic_pit_reservations(session_id: UUID | str) -> None:
    return cancel_automatic_reservations(session_id, connection, publish)


def _simulation_lease_is_valid(sim: Simulation) -> bool:
    runtime_lease = getattr(app.state, "runtime_lease", None)
    if runtime_lease is None:
        return True
    try:
        check_runtime_lease(runtime_lease)
    except RuntimeError as error:
        sim.status = "error"
        log.error("Simulation stopped after PostgreSQL runtime ownership loss: %s", error)
        return False
    return True


async def _finalize_simulation_results(
    sim: Simulation,
    ordered: list[dict[str, Any]],
    best_laps: dict[str, int],
    pole_driver_id: str | None,
    fastest_driver_id: str | None,
    championship_id: UUID,
) -> None:
    await finalize_results(
        sim,
        ordered,
        best_laps,
        pole_driver_id,
        fastest_driver_id,
        championship_id,
        connection,
        publish,
        cancel_automatic_pit_reservations,
        _make_demo_race,
        launch_demo_simulation,
        simulations,
    )


def _persist_simulation_tick(
    col: Collection[dict[str, Any]],
    sim: Simulation,
    packets: list[dict[str, Any]],
    timing: dict[str, Any],
) -> None:
    persist_tick(
        col,
        sim,
        packets,
        timing,
        publish,
        schedule_simulation_pit_stops,
        record_simulated_incidents,
    )


async def simulation_loop(sim: Simulation) -> None:
    await run_simulation_loop(
        sim,
        _simulation_lease_is_valid=lambda *args, **kwargs: _simulation_lease_is_valid(
            *args, **kwargs
        ),
        mongo_ready=lambda *args, **kwargs: mongo_ready(*args, **kwargs),
        fetch_one=lambda *args, **kwargs: fetch_one(*args, **kwargs),
        refresh_simulation_pit_state=lambda *args, **kwargs: refresh_simulation_pit_state(
            *args, **kwargs
        ),
        advance_simulation_tick=lambda *args, **kwargs: advance_simulation_tick(*args, **kwargs),
        _persist_simulation_tick=lambda *args, **kwargs: _persist_simulation_tick(*args, **kwargs),
        _finalize_simulation_results=lambda *args, **kwargs: _finalize_simulation_results(
            *args, **kwargs
        ),
        log=log,
        MAX_SESSION_LAPS=MAX_SESSION_LAPS,
        datetime=datetime,
        UTC=UTC,
    )


async def _start_session_simulation(
    session_id: UUID, body: SimulationControl, sim: Simulation | None
) -> Simulation:
    return await start_simulation(
        session_id,
        body,
        sim,
        _require_crud_record,
        fetch_one,
        clear_session_measurements,
        fetch_all,
        restore_simulated_incidents,
        simulations,
        simulation_loop,
    )


async def _reset_session_simulation(
    session_id: UUID, body: SimulationControl, sim: Simulation | None
) -> Simulation:
    return await reset_simulation(
        session_id,
        body,
        sim,
        fetch_one,
        ensure_session_reset_allowed,
        sync_simulation_lifecycle,
        clear_session_measurements,
        simulations,
    )


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
