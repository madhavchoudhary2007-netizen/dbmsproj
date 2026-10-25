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
from contextlib import asynccontextmanager, suppress
from datetime import UTC as UTC
from datetime import datetime as datetime
from datetime import timedelta
from typing import Any
from uuid import UUID as UUID
from uuid import uuid4 as uuid4

import jwt as jwt
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Query,
    Request,
    WebSocket,
)
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from psycopg.rows import dict_row
from pymongo import DESCENDING as DESCENDING
from pymongo import MongoClient
from pymongo.collection import Collection

from . import token_revocation
from .analytics_router import create_analytics_router
from .api.crud import create_crud_router
from .api.dbms_lock import FutureTimeout as FutureTimeout
from .api.dbms_lock import create_dbms_lock_router
from .api.dbms_mongo import create_dbms_mongo_router
from .api.dbms_sql import create_dbms_sql_router
from .api.health import health_live as health_live
from .api.health import legacy_router as legacy_health_router
from .api.health import register_legacy_health, register_readiness
from .api.health import router as health_router
from .api.laps import create_laps_router
from .api.laps import race_lap_measurements as race_lap_measurements
from .api.live import create_live_router
from .api.pit_write import create_pit_write_router
from .api.race_archive import create_race_archive_router
from .api.results_read import create_results_read_router
from .api.results_write import create_results_write_router
from .api.session_action import create_session_action_router
from .api.simulation import create_simulation_router
from .api.stewards import create_stewards_router
from .auth_cookie import verify_csrf_token
from .auth_router import create_auth_router
from .config import (
    APP_ENV,
    AUTO_DEMO_RACE,
    CORS_ORIGINS,
    JWT_ALGORITHM,
    JWT_SECRET,
    MONGODB_DATABASE,
    MONGODB_URL,
)
from .core.application import create_application
from .core.auth_dependencies import (
    check_allowed_origin,
    create_role_check,
    token_is_revoked,
)
from .core.events import EventBus
from .core.http_auth import authenticate_http_user
from .core.lock_demo import create_lock_demo_helpers
from .core.runtime import RuntimeState
from .core.security import websocket_bearer
from .core.serialization import jsonable, telemetry_ws_payload
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
from .database import close_pool, connection, fetch_all, fetch_one, get_pool, open_pool
from .demo_names import generate_demo_names as generate_demo_names
from .demo_race_repository import DemoRaceDeleteConflict as DemoRaceDeleteConflict
from .demo_race_repository import DemoRaceSetupError as DemoRaceSetupError
from .demo_race_repository import choose_demo_car_numbers as choose_demo_car_numbers
from .demo_race_repository import (
    create_demo_race_records,
    delete_demo_race_records,
    get_demo_race_row,
    list_demo_race_ids,
    validate_demo_race_delete,
)
from .demo_race_router import (
    DEFAULT_DEMO_RACE_CREATE,
    create_demo_race_router,
    run_demo_race_create,
    run_demo_race_delete,
)
from .demo_runtime import build_demo_race
from .membership_router import router as membership_router
from .pit_repository import PIT_RESERVATION_SELECT, load_pit_strategy_rows, load_pit_telemetry
from .pit_router import create_pit_router
from .pit_strategy_router import create_pit_strategy_router
from .pit_strategy_service import PIT_TIRE_STINT_LAPS as PIT_TIRE_STINT_LAPS
from .pit_strategy_service import (
    project_pit_strategy,
    tire_stint_target,
)
from .runtime_lease import acquire_runtime_lease, check_runtime_lease
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
from .schemas_simulation import DemoRaceCreate, SimulationControl
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
from .telemetry_router import create_telemetry_router
from .user_router import create_user_router

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("apexgrid")
bearer = HTTPBearer(auto_error=False)
mongo_client: MongoClient | None = None
telemetry_collection = None


@asynccontextmanager
async def lifespan(application: FastAPI):
    global mongo_client, telemetry_collection
    runtime_lease = acquire_runtime_lease()
    application.state.runtime_lease = runtime_lease
    runtime = RuntimeState(bus=bus, simulations=simulations, runtime_lease=runtime_lease)
    application.state.runtime = runtime
    try:
        open_pool()
    except Exception:
        log.exception("PostgreSQL pool could not open")
    runtime.pool = get_pool()
    try:
        mongo_client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=1800)
        mongo_client.admin.command("ping")
        telemetry_collection = mongo_client[MONGODB_DATABASE]["telemetry"]
        telemetry_collection.create_index([("session_id", 1), ("ts", -1)])
        telemetry_collection.create_index([("driver_id", 1), ("ts", -1)])
        telemetry_collection.create_index([("session_id", 1), ("driver_id", 1), ("ts", -1)])
    except Exception:
        log.warning("MongoDB is not available at startup", exc_info=True)
    runtime.mongo_client = mongo_client
    runtime.telemetry_collection = telemetry_collection
    if APP_ENV == "local" and not get_pool().closed and telemetry_collection is not None:
        try:
            await resume_or_create_auto_demo_race(create_if_missing=AUTO_DEMO_RACE)
        except Exception:
            log.exception("Automatic local demo race could not be started")

    try:
        yield
    finally:
        try:
            tasks = [sim.task for sim in simulations.values() if sim.task and not sim.task.done()]
            for task in tasks:
                task.cancel()
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            if mongo_client:
                mongo_client.close()
            mongo_client = None
            telemetry_collection = None
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


app, require_runtime_lease = create_application(
    lifespan,
    CORS_ORIGINS,
    lambda lease: check_runtime_lease(lease),
    os.getenv("COOKIE_SECURE") == "1",
)


def require_db():
    if get_pool().closed:
        raise HTTPException(503, "PostgreSQL is unavailable")


def require_allowed_origin(request: Request):
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
):
    return authenticate_http_user(
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


authenticated_user_dependency = Depends(current_user)


def roles(*allowed: str) -> Callable[..., Any]:
    return create_role_check(allowed, authenticated_user_dependency)


admin_role_dependency = Depends(roles("ADMIN"))
admin_steward_dependency = Depends(roles("ADMIN", "STEWARD"))
admin_steward_principal_dependency = Depends(roles("ADMIN", "STEWARD", "PRINCIPAL"))


def create_automatic_reservation(
    session_id: UUID | str, team_id: UUID | str, driver_id: UUID | str | None, duration: timedelta
):
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT reserve_pit_box_auto(%s,%s,%s,%s) AS id",
            (session_id, team_id, driver_id, duration),
        )
        reservation_id = cur.fetchone()["id"]
        cur.execute(PIT_RESERVATION_SELECT + " WHERE r.id=%s", (reservation_id,))
        return cur.fetchone()


def crud_routes(
    resource: str, table: str, cols: tuple[str, ...], joins: str = "", select: str | None = None
):
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


app.include_router(
    create_auth_router(
        require_allowed_origin,
        lambda: fetch_one,
        jsonable,
        lambda: APP_ENV != "local",
        current_user,
    )
)


app.include_router(create_user_router(roles, jsonable))


session_action_router, session_action_handlers = create_session_action_router(
    lambda *a, **kw: _require_crud_record(*a, **kw),
    lambda *a, **kw: fetch_one(*a, **kw),
    lambda *a, **kw: ensure_session_reset_allowed(*a, **kw),
    lambda: simulations,
    lambda *a, **kw: connection(*a, **kw),
    lambda *a, **kw: clear_session_measurements(*a, **kw),
    lambda *a, **kw: sync_simulation_lifecycle(*a, **kw),
    lambda *a, **kw: cancel_automatic_pit_reservations(*a, **kw),
    lambda value: jsonable(value),
    lambda *a, **kw: publish(*a, **kw),
    admin_steward_dependency,
)
session_action = session_action_handlers["session_action"]
app.include_router(session_action_router)


results_read_router, results_read_handlers = create_results_read_router(
    lambda *a, **kw: fetch_all(*a, **kw),
    lambda value: jsonable(value),
    lambda *a, **kw: connection(*a, **kw),
    authenticated_user_dependency,
    admin_steward_dependency,
)
results = results_read_handlers["results"]
standings = results_read_handlers["standings"]
recalculate = results_read_handlers["recalculate"]
app.include_router(results_read_router)


results_write_router, results_write_handlers = create_results_write_router(
    lambda *a, **kw: fetch_one(*a, **kw),
    lambda *a, **kw: connection(*a, **kw),
    lambda: simulations,
    lambda *a, **kw: publish(*a, **kw),
    lambda value: jsonable(value),
    admin_steward_dependency,
)
save_results = results_write_handlers["save_results"]
app.include_router(results_write_router)


stewards_router, stewards_handlers = create_stewards_router(
    lambda *a, **kw: fetch_all(*a, **kw),
    lambda value: jsonable(value),
    lambda limit, offset: limit_offset(limit, offset),
    authenticated_user_dependency,
    lambda: connection(),
    lambda *a, **kw: publish(*a, **kw),
    admin_steward_dependency,
)
get_incidents = stewards_handlers["get_incidents"]
create_incident = stewards_handlers["create_incident"]
decide_incident = stewards_handlers["decide_incident"]
app.include_router(stewards_router)


app.include_router(create_pit_router(current_user, jsonable))


def _require_principal_own_team(team_id: UUID, user: dict[str, Any]) -> None:
    if user["role"] == "PRINCIPAL":
        own_team = fetch_one(
            "SELECT id FROM teams WHERE id=%s AND principal_user_id=%s", (team_id, user["id"])
        )
        if not own_team:
            raise HTTPException(403, "Principals may reserve pit boxes only for their own team")


_pit_write_router, _pit_write_handlers = create_pit_write_router(
    lambda team_id, user: _require_principal_own_team(team_id, user),
    lambda *args, **kwargs: connection(*args, **kwargs),
    lambda value: jsonable(value),
    lambda *args, **kwargs: publish(*args, **kwargs),
    lambda *args, **kwargs: fetch_one(*args, **kwargs),
    lambda: simulations,
    lambda *args, **kwargs: create_automatic_reservation(*args, **kwargs),
    admin_steward_principal_dependency,
)
app.include_router(_pit_write_router)
reserve_pit = _pit_write_handlers["reserve_pit"]
reserve_pit_auto = _pit_write_handlers["reserve_pit_auto"]
update_pit_reservation = _pit_write_handlers["update_pit_reservation"]


def mongo_ready():
    if telemetry_collection is None:
        raise HTTPException(503, "MongoDB telemetry store is unavailable")
    return telemetry_collection


def publish(session_id, kind, data):
    bus.send(
        session_id,
        {
            "type": kind,
            "ts": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "session_id": str(session_id),
            "data": jsonable(data),
        },
    )


app.include_router(
    create_telemetry_router(
        current_user,
        jsonable,
        mongo_ready,
        roles,
        telemetry_ws_payload,
        publish,
    )
)


pit_strategy_router, pit_strategy = create_pit_strategy_router(
    current_user,
    load_pit_strategy_rows,
    load_pit_telemetry,
    lambda: mongo_ready(),
    lambda session_key: simulations.get(session_key),
    project_pit_strategy,
    MAX_SESSION_LAPS,
    tire_stint_target,
    jsonable,
)
app.include_router(pit_strategy_router)


def demo_race_row(session_id: UUID | str):
    row = get_demo_race_row(session_id)
    if not row:
        return None
    result = jsonable(row)
    sim = simulations.get(str(session_id))
    result["simulation_state"] = sim.status if sim else "stopped"
    return result


def list_demo_races(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user=authenticated_user_dependency,
):
    ids = list_demo_race_ids(limit, offset)
    return [demo_race_row(row["session_id"]) for row in ids]


def _make_demo_race(cars: int | None = None, auto_repeat: bool = False):
    return build_demo_race(
        cars,
        auto_repeat,
        mongo_ready,
        create_demo_race_records,
        simulations,
        demo_race_row,
    )


def launch_demo_simulation(session_id: UUID | str):
    sim = simulations[str(session_id)]
    sim.status = "running"
    sim.task = asyncio.create_task(simulation_loop(sim))


app.include_router(
    create_demo_race_router(
        current_user,
        roles("ADMIN", "STEWARD"),
        demo_race_row,
        list_demo_race_ids,
        _make_demo_race,
        launch_demo_simulation,
        lambda: simulations,
        connection,
        dict_row,
        mongo_ready,
        DemoRaceDeleteConflict,
        validate_demo_race_delete,
        delete_demo_race_records,
    )
)


def restore_simulation_from_telemetry(sim: Simulation):
    return restore_telemetry_state(sim, lambda: mongo_ready())


def restore_simulated_incidents(sim: Simulation):
    return restore_incident_state(sim, lambda *a, **kw: fetch_all(*a, **kw))


async def resume_or_create_auto_demo_race(create_if_missing: bool = True):
    return await restore_or_create_demo(
        create_if_missing,
        lambda *args, **kwargs: fetch_all(*args, **kwargs),
        log,
        lambda sim: restore_simulation_from_telemetry(sim),
        lambda sim: restore_simulated_incidents(sim),
        lambda *args, **kwargs: launch_demo_simulation(*args, **kwargs),
        lambda *args, **kwargs: _make_demo_race(*args, **kwargs),
        simulations,
    )


async def create_demo_race(
    body: DemoRaceCreate = DEFAULT_DEMO_RACE_CREATE,
    user: Any = admin_steward_dependency,
) -> Any:
    return await run_demo_race_create(body, _make_demo_race, launch_demo_simulation, demo_race_row)


async def delete_demo_race(session_id: UUID, user=admin_steward_dependency):
    return await run_demo_race_delete(
        session_id,
        simulations,
        connection,
        dict_row,
        mongo_ready,
        DemoRaceDeleteConflict,
        validate_demo_race_delete,
        delete_demo_race_records,
    )


bus = EventBus()


simulations: dict[str, Simulation] = {}


def sync_simulation_lifecycle(session_id: UUID, action: str):
    sync_lifecycle(session_id, action, simulations)


def ensure_session_reset_allowed(session_id: UUID | str):
    return ensure_reset_allowed(session_id, fetch_one)


def clear_session_measurements(session_id: UUID | str):
    return clear_measurements(session_id, mongo_ready, connection, publish)


def refresh_simulation_pit_state(sim: Simulation, timestamp: datetime):
    return refresh_pit_state(sim, timestamp, connection, publish, tire_stint_target)


def schedule_simulation_pit_stops(sim: Simulation, packets: list[dict[str, Any]]):
    return schedule_pit_stops(
        sim, packets, tire_stint_target, create_automatic_reservation, publish, log
    )


def record_simulated_incidents(sim: Simulation, packets: list[dict[str, Any]]):
    return record_generated_incidents(sim, packets, connection, publish)


def cancel_automatic_pit_reservations(session_id: UUID | str):
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


async def simulation_loop(sim: Simulation):
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


simulation_router, control_simulation = create_simulation_router(
    lambda: mongo_ready(),
    lambda: simulations,
    lambda *args, **kwargs: _start_session_simulation(*args, **kwargs),
    lambda *args, **kwargs: _reset_session_simulation(*args, **kwargs),
    lambda *args, **kwargs: cancel_automatic_pit_reservations(*args, **kwargs),
    admin_steward_dependency,
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


live_router, session_ws = create_live_router(
    lambda ws: _check_ws_runtime_lease(ws),
    lambda token: _websocket_authenticated_user(token),
    lambda ws, queue: _wait_for_ws_event(ws, queue),
    lambda: bus,
    lambda: CORS_ORIGINS,
    websocket_bearer,
)
app.include_router(live_router)


app.include_router(create_analytics_router(current_user, jsonable))


health = register_legacy_health(lambda query: fetch_one(query), lambda: mongo_client)
app.include_router(legacy_health_router)


health_ready = register_readiness(
    app,
    lambda: health(),
    lambda lease: check_runtime_lease(lease),
)
app.include_router(health_router)


def admin(user=admin_role_dependency):
    return user


admin_dependency = Depends(admin)


dbms_sql_router, dbms_sql_handlers = create_dbms_sql_router(
    lambda *a, **kw: fetch_all(*a, **kw),
    lambda v: jsonable(v),
    admin_dependency,
    lambda: connection(),
)
public_dbms_tables = dbms_sql_handlers["public_dbms_tables"]
dbms_tables = dbms_sql_handlers["dbms_tables"]
dbms_schema = dbms_sql_handlers["dbms_schema"]
dbms_indexes = dbms_sql_handlers["dbms_indexes"]
dbms_locks = dbms_sql_handlers["dbms_locks"]
dbms_eer = dbms_sql_handlers["dbms_eer"]
dbms_explain = dbms_sql_handlers["dbms_explain"]
dbms_races = dbms_sql_handlers["dbms_races"]
constraint_demo = dbms_sql_handlers["constraint_demo"]
transaction_demo = dbms_sql_handlers["transaction_demo"]
dbms_table_rows = dbms_sql_handlers["dbms_table_rows"]
app.include_router(dbms_sql_router)


dbms_mongo_router, dbms_mongo_handlers = create_dbms_mongo_router(
    lambda *a, **kw: fetch_one(*a, **kw),
    lambda value: jsonable(value),
    lambda: mongo_ready(),
    admin_dependency,
    lambda: mongo_database_ready(),
    MONGODB_DATABASE,
    lambda *a, **kw: fetch_all(*a, **kw),
)
dbms_overview = dbms_mongo_handlers["dbms_overview"]
dbms_telemetry = dbms_mongo_handlers["dbms_telemetry"]
dbms_mongo_collections = dbms_mongo_handlers["dbms_mongo_collections"]
dbms_mongo_collection_documents = dbms_mongo_handlers["dbms_mongo_collection_documents"]
dbms_polyglot = dbms_mongo_handlers["dbms_polyglot"]
app.include_router(dbms_mongo_router)


race_archive_router, race_archive_handlers = create_race_archive_router(
    lambda *a, **kw: fetch_one(*a, **kw),
    lambda *a, **kw: fetch_all(*a, **kw),
    lambda value: jsonable(value),
    lambda: mongo_ready(),
    lambda col, match: race_lap_measurements(col, match),
    admin_dependency,
)
dbms_race = race_archive_handlers["dbms_race"]
app.include_router(race_archive_router)


laps_router, laps_handlers = create_laps_router(
    lambda *a, **kw: fetch_one(*a, **kw),
    lambda *a, **kw: fetch_all(*a, **kw),
    lambda value: jsonable(value),
    lambda: mongo_ready(),
    lambda col, match: race_lap_measurements(col, match),
    admin_dependency,
    authenticated_user_dependency,
)
dbms_race_laps = laps_handlers["dbms_race_laps"]
session_laps = laps_handlers["session_laps"]
app.include_router(laps_router)


def mongo_database_ready():
    if mongo_client is None:
        raise HTTPException(503, "MongoDB document store is unavailable")
    return mongo_client[MONGODB_DATABASE]


lock_demo_guard = threading.Lock()

_competing_lock_demo_reservation, _cleanup_lock_demo = create_lock_demo_helpers(
    lambda: connection()
)

_dbms_lock_router, _dbms_lock_handlers = create_dbms_lock_router(
    lambda *args, **kwargs: fetch_one(*args, **kwargs),
    lambda *args, **kwargs: connection(*args, **kwargs),
    lambda *args, **kwargs: _competing_lock_demo_reservation(*args, **kwargs),
    lambda *args, **kwargs: _cleanup_lock_demo(*args, **kwargs),
    lock_demo_guard,
    lambda *args, **kwargs: recalculate(*args, **kwargs),
    admin_dependency,
)
app.include_router(_dbms_lock_router)
dbms_lock_demo = _dbms_lock_handlers["dbms_lock_demo"]
dbms_recalculate = _dbms_lock_handlers["dbms_recalculate"]
