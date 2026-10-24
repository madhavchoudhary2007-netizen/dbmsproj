from __future__ import annotations

import asyncio
import hmac
import logging
import os
import random
import secrets
import threading
import time as time
from collections.abc import Callable
from concurrent.futures import Future as Future
from concurrent.futures import ThreadPoolExecutor as ThreadPoolExecutor
from contextlib import asynccontextmanager, suppress
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import jwt
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Query,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from psycopg import IntegrityError, OperationalError, sql
from psycopg.errors import ExclusionViolation, ForeignKeyViolation, UniqueViolation
from psycopg.rows import dict_row
from psycopg_pool import PoolClosed, PoolTimeout
from pymongo import DESCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError
from starlette.middleware.base import RequestResponseEndpoint

from . import token_revocation
from .analytics_router import create_analytics_router
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
from .api.race_archive import create_race_archive_router
from .api.results_read import create_results_read_router
from .api.results_write import create_results_write_router
from .api.session_action import create_session_action_router
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
from .core.errors import (
    conflict_handler,
    database_unavailable_handler,
    integrity_handler,
    reference_conflict_handler,
)
from .core.events import EventBus
from .core.lock_demo import create_lock_demo_helpers
from .core.security import websocket_bearer
from .core.serialization import jsonable, telemetry_ws_payload
from .core.simulation_tick import advance_simulation_tick as advance_simulation_tick
from .core.validation import (
    _crud_write_payload,
    _require_crud_record,
    limit_offset,
    validate_session_laps,
)
from .crud_repository import (
    CrudDeleteError,
    create_crud_row,
    delete_crud_row,
    get_crud_row,
    list_crud_rows,
    update_crud_row,
)
from .database import close_pool, connection, fetch_all, fetch_one, get_pool, open_pool
from .demo_race_repository import (
    DemoRaceDeleteConflict,
    DemoRaceSetupError,
    create_demo_race_records,
    delete_demo_race_records,
    get_demo_race_row,
    list_demo_race_ids,
    validate_demo_race_delete,
)
from .demo_race_repository import choose_demo_car_numbers as choose_demo_car_numbers
from .demo_race_router import (
    DEFAULT_DEMO_RACE_CREATE,
    create_demo_race_router,
    run_demo_race_create,
    run_demo_race_delete,
)
from .membership_router import create_membership_router
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
from .schemas_operations import (
    AutoReservationIn,
    ReservationIn,
    ReservationStatus,
)
from .schemas_operations import Decision as Decision
from .schemas_operations import IncidentIn as IncidentIn
from .schemas_simulation import DemoRaceCreate, SimulationControl
from .security_headers import SecurityHeadersMiddleware
from .simulation_core import MAX_SESSION_LAPS, Simulation
from .simulation_core import calculate_sector_performance as calculate_sector_performance
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
    try:
        open_pool()
    except Exception:
        log.exception("PostgreSQL pool could not open")
    try:
        mongo_client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=1800)
        mongo_client.admin.command("ping")
        telemetry_collection = mongo_client[MONGODB_DATABASE]["telemetry"]
        telemetry_collection.create_index([("session_id", 1), ("ts", -1)])
        telemetry_collection.create_index([("driver_id", 1), ("ts", -1)])
        telemetry_collection.create_index([("session_id", 1), ("driver_id", 1), ("ts", -1)])
    except Exception:
        log.warning("MongoDB is not available at startup", exc_info=True)
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
            application.state.runtime_lease = None
            runtime_lease.close()


app = FastAPI(title="ApexGrid API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def require_runtime_lease(request: Request, call_next: RequestResponseEndpoint) -> Response:
    if request.url.path in {"/health/live", "/health/ready"}:
        return await call_next(request)
    runtime_lease = getattr(request.app.state, "runtime_lease", None)
    if runtime_lease is not None:
        try:
            check_runtime_lease(runtime_lease)
        except RuntimeError:
            return JSONResponse(
                status_code=503,
                content={
                    "detail": (
                        "PostgreSQL runtime ownership was lost. Restart the backend to "
                        "restore service."
                    )
                },
            )
    return await call_next(request)


app.add_middleware(SecurityHeadersMiddleware, secure=os.getenv("COOKIE_SECURE") == "1")


app.add_exception_handler(UniqueViolation, conflict_handler)
app.add_exception_handler(ExclusionViolation, conflict_handler)
app.add_exception_handler(ForeignKeyViolation, reference_conflict_handler)
app.add_exception_handler(IntegrityError, integrity_handler)
app.add_exception_handler(OperationalError, database_unavailable_handler)
app.add_exception_handler(PoolTimeout, database_unavailable_handler)
app.add_exception_handler(PoolClosed, database_unavailable_handler)


def require_db():
    if get_pool().closed:
        raise HTTPException(503, "PostgreSQL is unavailable")


def require_allowed_origin(request: Request):
    origin = request.headers.get("origin")
    if origin is not None and origin not in CORS_ORIGINS:
        raise HTTPException(403, "Origin not allowed")


bearer_dependency = Depends(bearer)


def _token_is_revoked(claims: dict[str, Any], *, fail_closed: bool = False) -> bool:
    if "jti" not in claims:
        return False
    jti = claims["jti"]
    if not isinstance(jti, str) or not jti:
        raise ValueError()
    try:
        return token_revocation.is_revoked(jti)
    except Exception:
        if not fail_closed:
            raise
        raise HTTPException(503, "PostgreSQL is unavailable") from None


def current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = bearer_dependency,
):
    bearer_token = credentials.credentials if credentials else None
    cookie_token = request.cookies.get("apexgrid_session")
    token = bearer_token or cookie_token
    if not token:
        raise HTTPException(401, "Authentication required", headers={"WWW-Authenticate": "Bearer"})
    try:
        claims = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if _token_is_revoked(claims, fail_closed=True):
            raise ValueError()
        user_id = claims.get("sub")
        if not user_id:
            raise ValueError()
        if (
            not bearer_token
            and cookie_token
            and request.method in {"POST", "PUT", "PATCH", "DELETE"}
        ):
            require_allowed_origin(request)
            csrf_cookie = request.cookies.get("apexgrid_csrf", "")
            csrf_header = request.headers.get("x-csrf-token", "")
            session_id = claims.get("jti", "")
            if (
                not csrf_cookie
                or not csrf_header
                or not session_id
                or not hmac.compare_digest(csrf_cookie.encode(), csrf_header.encode())
                or not verify_csrf_token(csrf_cookie, session_id, JWT_SECRET)
            ):
                raise HTTPException(403, "CSRF validation failed")
        user = fetch_one("SELECT id,email,full_name,role FROM users WHERE id=%s", (user_id,))
    except (jwt.exceptions.InvalidTokenError, ValueError):
        user = None
    if not user:
        raise HTTPException(401, "Invalid or expired token", headers={"WWW-Authenticate": "Bearer"})
    request.state.auth_claims = claims
    return jsonable(user)


authenticated_user_dependency = Depends(current_user)


def roles(*allowed: str) -> Callable[..., Any]:
    def check(user: Any = authenticated_user_dependency) -> Any:
        if user["role"] not in allowed:
            raise HTTPException(403, "Insufficient role")
        return user

    return check


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
    # Names here are hard-coded contract identifiers, never user supplied SQL.
    projection = select or f"{table}.*"
    base = (
        sql.SQL("SELECT {} FROM {} {}")
        .format(sql.SQL(projection), sql.Identifier(table), sql.SQL(joins))
        .as_string()
    )
    prefix = f"/api/{resource}"

    @app.get(prefix)
    def listing(
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0),
        user=authenticated_user_dependency,
    ):
        page_limit, page_offset = limit_offset(limit, offset)
        return jsonable(list_crud_rows(base, page_limit, page_offset))

    @app.get(prefix + "/{item_id}")
    def get_item(item_id: UUID, user=authenticated_user_dependency):
        result = get_crud_row(base, table, item_id)
        return jsonable(_require_crud_record(result, f"{resource[:-1].capitalize()} not found"))

    @app.post(prefix, status_code=201)
    def create_item(payload: dict[str, Any], user=admin_role_dependency):
        clean = _crud_write_payload(payload, cols)
        validate_session_laps(table, clean)
        row = create_crud_row(table, clean)
        return jsonable(row)

    @app.patch(prefix + "/{item_id}")
    def update_item(item_id: UUID, payload: dict[str, Any], user=admin_role_dependency):
        clean = _crud_write_payload(payload, cols)
        validate_session_laps(table, clean)
        if table == "race_sessions":
            existing = fetch_one("SELECT state FROM race_sessions WHERE id=%s", (item_id,))
            if not existing:
                raise HTTPException(404, "Session not found")
            if existing["state"] != "SCHEDULED" and set(clean) & {
                "event_id",
                "session_type",
                "scheduled_at",
                "total_laps",
            }:
                raise HTTPException(
                    409, "Session context and lap count cannot change after a session starts"
                )
        row = update_crud_row(table, item_id, clean)
        return jsonable(_require_crud_record(row, f"{resource[:-1].capitalize()} not found"))

    @app.delete(prefix + "/{item_id}", status_code=204)
    def delete_item(item_id: UUID, user=admin_role_dependency):
        try:
            delete_crud_row(table, resource, item_id, telemetry_collection)
        except CrudDeleteError as exc:
            raise HTTPException(exc.status_code, exc.detail) from exc
        return None


crud_routes("championships", "championships", ("id", "name", "season"))
crud_routes("circuits", "circuits", ("id", "name", "country", "length_km"))
crud_routes(
    "teams",
    "teams",
    ("id", "name", "principal_user_id"),
    "LEFT JOIN users u ON u.id=teams.principal_user_id",
    "teams.*,u.full_name AS principal_name",
)
crud_routes(
    "drivers",
    "drivers",
    ("id", "user_id", "licence_number", "number"),
    (
        "LEFT JOIN users u ON u.id=drivers.user_id LEFT JOIN team_memberships tm ON tm.driver_id="
        "drivers.id AND tm.end_date IS NULL LEFT JOIN teams t ON t.id=tm.team_id"
    ),
    "drivers.*,u.full_name,u.email,t.name AS team_name",
)
crud_routes(
    "events",
    "race_events",
    ("id", "championship_id", "circuit_id", "round_number", "name", "start_date"),
    (
        "LEFT JOIN championships ch ON ch.id=race_events.championship_id LEFT JOIN circuits c ON "
        "c.id=race_events.circuit_id"
    ),
    (
        "race_events.*,ch.name AS championship_name,c.name AS ci"
        "rcuit_name,c.country AS circuit_country"
    ),
)
crud_routes(
    "sessions",
    "race_sessions",
    ("id", "event_id", "session_type", "scheduled_at", "total_laps", "safety_car"),
    (
        "LEFT JOIN race_events e ON e.id=race_sessions.event_id LEFT JOIN circuits c ON c.id=e.ci"
        "rcuit_id"
    ),
    "race_sessions.*,e.name AS event_name,c.name AS circuit_name",
)


app.include_router(create_membership_router(current_user, roles, jsonable))


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


@app.post("/api/pit-reservations", status_code=201)
def reserve_pit(body: ReservationIn, user=admin_steward_principal_dependency):
    _require_principal_own_team(body.team_id, user)
    try:
        with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT reserve_pit_box(%s,%s,%s,%s,%s) AS id",
                (body.pit_box_id, body.session_id, body.team_id, body.starts_at, body.ends_at),
            )
            reservation_id = cur.fetchone()["id"]
            cur.execute(PIT_RESERVATION_SELECT + " WHERE r.id=%s", (reservation_id,))
            row = cur.fetchone()
    except (UniqueViolation, ExclusionViolation) as exc:
        raise HTTPException(409, "Pit box is already reserved for this time") from exc
    except ForeignKeyViolation as exc:
        raise HTTPException(404, "Pit box, session, or team not found") from exc
    except Exception as exc:
        if getattr(exc, "sqlstate", None) == "23514":
            raise HTTPException(422, "Pit box and session must belong to the same event") from exc
        if getattr(exc, "sqlstate", None) == "23P01":
            raise HTTPException(409, "Pit box is already reserved for this time") from exc
        raise
    result = jsonable(row)
    publish(body.session_id, "pit.update", result)
    return result


@app.post("/api/pit-reservations/auto", status_code=201)
def reserve_pit_auto(body: AutoReservationIn, user=admin_steward_principal_dependency):
    _require_principal_own_team(body.team_id, user)
    session = fetch_one("SELECT state FROM race_sessions WHERE id=%s", (body.session_id,))
    if not session:
        raise HTTPException(404, "Session not found")
    if session["state"] not in {"ACTIVE", "PAUSED"}:
        raise HTTPException(409, "Pit reservations require an active or paused session")
    sim = simulations.get(str(body.session_id))
    rate_hz = sim.rate_hz if sim else 2.0
    pit_duration = timedelta(seconds=max(0.6, 3.0 / max(rate_hz, 0.2)))
    try:
        reservation = create_automatic_reservation(
            body.session_id, body.team_id, body.driver_id, pit_duration
        )
    except (UniqueViolation, ExclusionViolation) as exc:
        raise HTTPException(409, "Driver or pit box already has a conflicting reservation") from exc
    except ForeignKeyViolation as exc:
        raise HTTPException(404, "Session, team, driver, or pit box not found") from exc
    except Exception as exc:
        sqlstate = getattr(exc, "sqlstate", None)
        if sqlstate == "P0002":
            raise HTTPException(409, "The event has no pit boxes") from exc
        if sqlstate == "23514":
            raise HTTPException(
                422, "Driver must be an eligible member of the team for this session"
            ) from exc
        if sqlstate == "23505":
            raise HTTPException(
                409, "Driver already has an open pit reservation for this session"
            ) from exc
        raise
    result = jsonable(reservation)
    publish(body.session_id, "pit.update", result)
    return result


@app.patch("/api/pit-reservations/{reservation_id}")
def update_pit_reservation(
    reservation_id: UUID, body: ReservationStatus, user=admin_steward_principal_dependency
):
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """SELECT r.*,t.principal_user_id FROM pit_reservations r
            JOIN teams t ON t.id=r.team_id WHERE r.id=%s FOR UPDATE OF r""",
            (reservation_id,),
        )
        reservation = cur.fetchone()
        if not reservation:
            raise HTTPException(404, "Pit reservation not found")
        if user["role"] == "PRINCIPAL" and str(reservation["principal_user_id"]) != user["id"]:
            raise HTTPException(403, "Principals may update reservations only for their own team")
        if reservation["status"] != "RESERVED":
            raise HTTPException(409, "Pit reservation is already closed")
        cur.execute(
            "UPDATE pit_reservations SET status=%s WHERE id=%s", (body.status, reservation_id)
        )
        cur.execute(PIT_RESERVATION_SELECT + " WHERE r.id=%s", (reservation_id,))
        updated = cur.fetchone()
    result = jsonable(updated)
    publish(updated["session_id"], "pit.update", result)
    return result


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
    if mongo_ready() is None:
        raise HTTPException(503, "MongoDB telemetry store is unavailable")
    seed = secrets.randbits(63)
    rng = random.Random(seed)  # noqa: S311 -- seeded race choices; seed is generated securely
    car_count = cars if cars is not None else rng.randint(8, 16)
    session_id, event_id = uuid4(), uuid4()
    now = datetime.now(UTC)
    given = [
        "Amelia",
        "Rafael",
        "Maya",
        "Theo",
        "Nina",
        "Luca",
        "Aisha",
        "Felix",
        "Sofia",
        "Ethan",
        "Leila",
        "Oscar",
        "Priya",
        "Mateo",
        "Zara",
        "Jonah",
        "Ines",
        "Kai",
        "Elena",
        "Arjun",
    ]
    family = [
        "Bennett",
        "Costa",
        "Shah",
        "Moreau",
        "Kim",
        "Novak",
        "Singh",
        "Fischer",
        "Alvarez",
        "Tanaka",
        "Dubois",
        "Reed",
        "Petrov",
        "Okafor",
        "Lindholm",
        "Santos",
        "Kaur",
        "Weber",
        "Nakamura",
        "Clarke",
    ]
    names = [
        f"{a} {b}"
        for a, b in zip(rng.sample(given, car_count), rng.sample(family, car_count), strict=False)
    ]
    try:
        generated, total_laps = create_demo_race_records(
            session_id, event_id, now, names, auto_repeat, seed=seed
        )
    except DemoRaceSetupError as exc:
        raise HTTPException(409, str(exc)) from exc
    sim = Simulation(session_id, generated, 2.0, total_laps=total_laps, seed=seed)
    sim.auto_repeat = auto_repeat
    sim.is_generated = True
    sim.pace_offsets_ms = {str(d["id"]): d["pace_offset_ms"] for d in generated}
    sim.lap_by_driver = {str(d["id"]): 1 for d in generated}
    sim.elapsed_by_driver = {str(d["id"]): 0 for d in generated}
    simulations[str(session_id)] = sim
    sim.status = "running"
    return demo_race_row(session_id)


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
    """Resume an active generated race without deleting its recorded laps."""
    col = mongo_ready()
    for driver in sim.drivers:
        driver_id = str(driver["id"])
        latest = col.find_one(
            {"session_id": str(sim.session_id), "driver_id": driver_id}, sort=[("ts", DESCENDING)]
        )
        sim.lap_by_driver[driver_id] = int(latest.get("lap", 1)) if latest else 1
        sim.sector_by_driver[driver_id] = int(latest.get("sector", 0)) if latest else 0
        sim.elapsed_by_driver[driver_id] = int(latest.get("elapsed_ms", 0)) if latest else 0
        sim.sector_splits_by_driver[driver_id] = (
            list(latest.get("sector_ms") or []) if latest else []
        )
        sim.next_sector_due_by_driver[driver_id] = sim.elapsed_by_driver[driver_id]
        if latest and latest.get("last_lap_ms"):
            sim.last_lap_by_driver[driver_id] = int(latest["last_lap_ms"])
        sim.tire_age_by_driver[driver_id] = int(latest.get("tire_age_laps", 0)) if latest else 0
        sim.tire_wear_by_driver[driver_id] = (
            float(latest.get("tire_wear_pct", 0)) if latest else 0.0
        )
        if latest and latest.get("tire_compound"):
            sim.compound_by_driver[driver_id] = latest["tire_compound"]
    sim.race_clock_ms = max(sim.elapsed_by_driver.values(), default=0)


def restore_simulated_incidents(sim: Simulation):
    """Keep a restarted simulator from duplicating reports already in the archive."""
    sim.incident_laps_recorded = {
        row["lap"]
        for row in fetch_all(
            "SELECT DISTINCT lap FROM incident_reports WHERE session_id=%s", (sim.session_id,)
        )
    }


async def resume_or_create_auto_demo_race(create_if_missing: bool = True):
    active_races = fetch_all(
        "SELECT s.id,s.total_laps,d.auto_repeat,d.simulation_seed FROM race_sessions s JOIN d"
        "emo_races d ON d.session_id=s.id WHERE s.state='ACTIVE' ORDER BY d.created_at"
    )
    for active in active_races:
        session_id = active["id"]
        entries = fetch_all(
            """SELECT d.id,d.number,de.pace_offset_ms,tm.team_id,t.name AS team_name
            FROM demo_race_entries de JOIN drivers d ON d.id=de.driver_id
            JOIN race_sessions s ON s.id=de.session_id
            JOIN team_memberships tm ON tm.driver_id=d.id AND tm.start_date<=s.scheduled_at::date
              AND (tm.end_date IS NULL OR tm.end_date>=s.scheduled_at::date)
            JOIN teams t ON t.id=tm.team_id WHERE de.session_id=%s ORDER BY d.number""",
            (session_id,),
        )
        if not entries:
            log.error("Active generated race %s has no entries", session_id)
            continue
        sim = Simulation(
            session_id,
            entries,
            2.0,
            total_laps=active["total_laps"],
            seed=active.get("simulation_seed"),
        )
        sim.pace_offsets_ms = {str(d["id"]): d["pace_offset_ms"] for d in entries}
        restore_simulation_from_telemetry(sim)
        sim.auto_repeat = active["auto_repeat"]
        sim.is_generated = True
        restore_simulated_incidents(sim)
        sim.status = "running"
        simulations[str(session_id)] = sim
        launch_demo_simulation(session_id)
    if any(race["auto_repeat"] for race in active_races) or not create_if_missing:
        return

    race = await asyncio.to_thread(_make_demo_race, None, True)
    launch_demo_simulation(race["session_id"])


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
    sim = simulations.get(str(session_id))
    if not sim:
        return
    if action == "pause" and sim.status == "running":
        sim.status = "paused"
    elif action == "resume" and sim.status == "paused":
        sim.status = "running"
    elif action in {"finish", "reset"}:
        sim.status = "stopped"
        if sim.task and not sim.task.done():
            sim.task.get_loop().call_soon_threadsafe(sim.task.cancel)
        if action == "reset":
            sim.lap_by_driver = {str(driver["id"]): 1 for driver in sim.drivers}
            sim.sector_by_driver.clear()
            sim.race_clock_ms = 0
            sim.next_sector_due_by_driver.clear()
            sim.last_lap_by_driver.clear()
            sim.elapsed_by_driver = {str(driver["id"]): 0 for driver in sim.drivers}
            sim.sector_splits_by_driver.clear()
            sim.tire_age_by_driver = {str(driver["id"]): 0 for driver in sim.drivers}
            sim.tire_wear_by_driver = {str(driver["id"]): 0.0 for driver in sim.drivers}
            sim.compound_by_driver.clear()
            sim.pit_reservations_by_driver.clear()
            sim.pit_due_tire_age_by_driver.clear()


def ensure_session_reset_allowed(session_id: UUID | str):
    row = fetch_one(
        """SELECT EXISTS(SELECT 1 FROM incident_reports i JOIN penalties p ON p.incident_id=i.id
        WHERE i.session_id=s.id) AS has_penalties FROM race_sessions s WHERE s.id=%s""",
        (session_id,),
    )
    if not row:
        raise HTTPException(404, "Session not found")
    if row["has_penalties"]:
        raise HTTPException(409, "A session with official penalties cannot be reset")


def clear_session_measurements(session_id: UUID | str):
    """Clear stored measurements after an explicit reset, preserving penalty history."""
    col = mongo_ready()
    cancelled = []
    with connection() as conn, conn.cursor() as cur:
        cur.execute(
            """SELECT e.championship_id,
            EXISTS(SELECT 1 FROM incident_reports i JOIN penalties p ON """
            """p.incident_id=i.id WHERE i.session_id=s.id) AS has_penalties
            FROM race_sessions s JOIN race_events e ON e.id=s.event_id WHERE s.id=%s""",
            (session_id,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Session not found")
        championship_id = row["championship_id"]
        if row["has_penalties"]:
            raise HTTPException(409, "A session with official penalties cannot be reset")
        try:
            col.delete_many({"session_id": str(session_id)})
        except PyMongoError as exc:
            raise HTTPException(503, "Telemetry store reset failed") from exc
        cur.execute("DELETE FROM session_results WHERE session_id=%s", (session_id,))
        cur.execute("SELECT recalculate_standings(%s)", (championship_id,))
        cur.execute(
            (
                "UPDATE pit_reservations SET status='CANCELLED'\n            WHERE session_id=%s "
                "AND allocation_source='AUTOMATIC' AND status='RESERVED' RETURNING id"
            ),
            (session_id,),
        )
        cancelled_ids = [item["id"] for item in cur.fetchall()]
        if cancelled_ids:
            cur.execute(PIT_RESERVATION_SELECT + " WHERE r.id=ANY(%s)", (cancelled_ids,))
            cancelled = cur.fetchall()
        cur.execute(
            "DELETE FROM pit_reservations WHERE session_id=%s AND allocation_source='AUTOMATIC'",
            (session_id,),
        )
    for reservation in cancelled:
        publish(session_id, "pit.update", reservation)


def refresh_simulation_pit_state(sim: Simulation, timestamp: datetime):
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """UPDATE pit_reservations SET status='COMPLETED'
            WHERE session_id=%s AND status='RESERVED' AND ends_at<=%s RETURNING id""",
            (sim.session_id, timestamp),
        )
        expired_ids = [row["id"] for row in cur.fetchall()]
        if expired_ids:
            cur.execute(PIT_RESERVATION_SELECT + " WHERE r.id=ANY(%s)", (expired_ids,))
            expired = cur.fetchall()
        else:
            expired = []
        cur.execute(
            PIT_RESERVATION_SELECT
            + """ WHERE r.session_id=%s AND r.driver_id IS NOT NULL
            AND r.status='RESERVED' AND r.ends_at>%s ORDER BY r.starts_at""",
            (sim.session_id, timestamp),
        )
        active = cur.fetchall()
    for reservation in expired:
        publish(sim.session_id, "pit.update", reservation)
        driver_id = reservation.get("driver_id")
        if driver_id and reservation.get("allocation_source") == "AUTOMATIC":
            key = str(driver_id)
            sim.pit_reservations_by_driver.pop(key, None)
            sim.tire_age_by_driver[key] = 0
            sim.tire_wear_by_driver[key] = 0.0
            current = sim.compound_by_driver.get(key)
            base = current or "SOFT"
            compounds = ("SOFT", "MEDIUM", "HARD")
            sim.compound_by_driver[key] = compounds[(compounds.index(base) + 1) % len(compounds)]
            car = next((row for row in sim.drivers if str(row["id"]) == key), {})
            sim.pit_due_tire_age_by_driver[key] = tire_stint_target(
                sim.compound_by_driver[key], int(car.get("number") or 1)
            )
    sim.pit_reservations_by_driver = {str(row["driver_id"]): row for row in active}
    return sim.pit_reservations_by_driver


def schedule_simulation_pit_stops(sim: Simulation, packets: list[dict[str, Any]]):
    completion_lap = min(sim.total_laps or MAX_SESSION_LAPS, MAX_SESSION_LAPS)
    for packet in packets:
        driver_id = str(packet["driver_id"])
        driver = next((row for row in sim.drivers if str(row["id"]) == driver_id), None)
        number = int((driver or {}).get("number") or 1)
        compound = sim.compound_by_driver.setdefault(
            driver_id, ("SOFT", "MEDIUM", "HARD")[number % 3]
        )
        target_age = sim.pit_due_tire_age_by_driver.setdefault(
            driver_id, tire_stint_target(compound, number)
        )
        if (
            packet["sector"] != 3
            or packet["lap"] >= completion_lap
            or packet["tire_age_laps"] < target_age
            or driver_id in sim.pit_reservations_by_driver
        ):
            continue
        if not driver or not driver.get("team_id"):
            sim.pit_due_tire_age_by_driver[driver_id] = MAX_SESSION_LAPS + 1
            continue
        duration = timedelta(seconds=max(0.6, 3.0 / max(sim.rate_hz, 0.2)))
        try:
            reservation = create_automatic_reservation(
                sim.session_id, driver["team_id"], driver["id"], duration
            )
        except Exception as exc:
            log.warning("Automatic pit stop allocation failed for %s: %s", driver_id, exc)
            sim.pit_due_tire_age_by_driver[driver_id] = MAX_SESSION_LAPS + 1
            continue
        sim.pit_reservations_by_driver[driver_id] = reservation
        sim.pit_due_tire_age_by_driver[driver_id] = tire_stint_target(compound, number)
        publish(sim.session_id, "pit.update", reservation)


def record_simulated_incidents(sim: Simulation, packets: list[dict[str, Any]]):
    """Create a few reviewable race reports as laps complete."""
    if not sim.is_generated:
        return
    descriptions = {
        7: "Track limits observed at corner exit",
        23: "Minor wheel-to-wheel contact under review",
        41: "Unsafe rejoin reported by race control",
    }
    for lap, description in descriptions.items():
        if lap >= (sim.total_laps or MAX_SESSION_LAPS) or lap in sim.incident_laps_recorded:
            continue
        finished = [
            packet
            for packet in packets
            if packet["lap"] == lap and packet["sector"] == 3 and packet["lap_time_ms"]
        ]
        if not finished:
            continue
        packet = finished[0]
        with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """INSERT INTO incident_reports(session_id,driver_id,lap,description)
                VALUES (%s,%s,%s,%s) RETURNING *""",
                (sim.session_id, packet["driver_id"], lap, description),
            )
            row = cur.fetchone()
        sim.incident_laps_recorded.add(lap)
        publish(sim.session_id, "incident.update", row)


def cancel_automatic_pit_reservations(session_id: UUID | str):
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            (
                "UPDATE pit_reservations SET status='CANCELLED'\n            WHERE session_id=%s "
                "AND allocation_source='AUTOMATIC' AND status='RESERVED' RETURNING id"
            ),
            (session_id,),
        )
        ids = [row["id"] for row in cur.fetchall()]
        if ids:
            cur.execute(PIT_RESERVATION_SELECT + " WHERE r.id=ANY(%s)", (ids,))
            rows = cur.fetchall()
        else:
            rows = []
    for row in rows:
        publish(session_id, "pit.update", row)


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
    rows = []
    with connection() as conn, conn.cursor() as cur:
        for position, packet in enumerate(ordered, start=1):
            driver_id = packet["driver_id"]
            best_lap_ms = best_laps.get(driver_id, packet["last_lap_ms"])
            pole = driver_id == pole_driver_id
            fastest_lap = driver_id == fastest_driver_id
            cur.execute(
                "INSERT INTO session_results(session_id,driver_id,position,"
                "lap_time_ms,pole,fastest_lap,"
                "classified) VALUES (%s,%s,%s,%s,%s,%s,TRUE) "
                "ON CONFLICT(session_id,driver_id) "
                "DO UPDATE SET "
                "position=excluded.position,lap_time_ms=excluded.lap_time_ms,"
                "pole=excluded.pole,fastest_lap=excluded.fastest_lap,classified=TRUE",
                (sim.session_id, driver_id, position, best_lap_ms, pole, fastest_lap),
            )
            rows.append(
                {
                    "driver_id": driver_id,
                    "position": position,
                    "lap_time_ms": best_lap_ms,
                    "pole": pole,
                    "fastest_lap": fastest_lap,
                    "classified": True,
                }
            )
        cur.execute(
            (
                "UPDATE race_sessions SET state='COMPLETED',ended_at=%s WHERE id=%s A"
                "ND state='ACTIVE' RETURNING *"
            ),
            (datetime.now(UTC), sim.session_id),
        )
        completed = cur.fetchone()
        if completed:
            cur.execute("SELECT recalculate_standings(%s)", (championship_id,))
    sim.status = "stopped"
    publish(sim.session_id, "timing.update", rows)
    if completed:
        publish(sim.session_id, "session.state", completed)
    sim.runs_completed += 1
    cancel_automatic_pit_reservations(sim.session_id)
    if not sim.auto_repeat or not completed:
        return
    await asyncio.sleep(5)
    race = await asyncio.to_thread(_make_demo_race, None, True)
    launch_demo_simulation(race["session_id"])
    simulations.pop(str(sim.session_id), None)


def _persist_simulation_tick(
    col: Collection[dict[str, Any]],
    sim: Simulation,
    packets: list[dict[str, Any]],
    timing: dict[str, Any],
) -> None:
    for packet in packets:
        inserted = col.insert_one(dict(packet))
        publish(
            sim.session_id,
            "telemetry.sample",
            telemetry_ws_payload(packet, inserted.inserted_id),
        )
    publish(sim.session_id, "timing.update", timing)
    schedule_simulation_pit_stops(sim, packets)
    record_simulated_incidents(sim, packets)


async def simulation_loop(sim: Simulation):
    if not _simulation_lease_is_valid(sim):
        return
    col = mongo_ready()
    while sim.status in {"running", "paused"}:
        if not _simulation_lease_is_valid(sim):
            return
        if sim.status == "paused":
            await asyncio.sleep(0.05)
            continue
        try:
            session = fetch_one(
                """SELECT s.state,s.safety_car,e.championship_id
                FROM race_sessions s JOIN race_events e ON e.id=s.event_id WHERE s.id=%s""",
                (sim.session_id,),
            )
            if not session or session["state"] != "ACTIVE":
                if session and session["state"] == "PAUSED":
                    sim.status = "paused"
                    continue
                sim.status = "error" if not session else "stopped"
                return
            timestamp = datetime.now(UTC)
            pit_assignments = refresh_simulation_pit_state(sim, timestamp)
            packets, timing = advance_simulation_tick(
                sim, timestamp, safety_car=session["safety_car"], pit_assignments=pit_assignments
            )
            _persist_simulation_tick(col, sim, packets, timing)
            completion_lap = min(sim.total_laps or MAX_SESSION_LAPS, MAX_SESSION_LAPS)
            if all(packet["lap"] == completion_lap and packet["sector"] == 3 for packet in packets):
                ordered = sorted(packets, key=lambda packet: packet["elapsed_ms"])
                best_laps = {
                    row["_id"]: row["best_lap_ms"]
                    for row in col.aggregate(
                        [
                            {
                                "$match": {
                                    "session_id": str(sim.session_id),
                                    "lap_time_ms": {"$gt": 0},
                                }
                            },
                            {
                                "$group": {
                                    "_id": "$driver_id",
                                    "best_lap_ms": {"$min": "$lap_time_ms"},
                                }
                            },
                        ]
                    )
                }
                fastest_driver_id = min(best_laps, key=best_laps.get) if best_laps else None
                pole_driver_id = (
                    min(sim.pace_offsets_ms, key=sim.pace_offsets_ms.get)
                    if sim.is_generated and sim.pace_offsets_ms
                    else None
                )
                await _finalize_simulation_results(
                    sim,
                    ordered,
                    best_laps,
                    pole_driver_id,
                    fastest_driver_id,
                    session["championship_id"],
                )
                return
        except PyMongoError:
            sim.status = "error"
            log.exception("Telemetry simulator could not write packet")
            return
        except Exception:
            sim.status = "error"
            log.exception("Telemetry simulator could not advance state")
            return
        await asyncio.sleep(1 / sim.rate_hz)


async def _start_session_simulation(
    session_id: UUID, body: SimulationControl, sim: Simulation | None
) -> Simulation:
    if sim and sim.status in {"running", "paused"}:
        raise HTTPException(409, "Simulation is already running")
    session = _require_crud_record(
        fetch_one(
            "SELECT state,total_laps,scheduled_at FROM race_sessions WHERE id=%s", (session_id,)
        ),
        "Session not found",
    )
    if session["state"] != "ACTIVE":
        raise HTTPException(409, "Session must be active before simulation starts")
    if sim and sim.status == "stopped":
        if sim.task and not sim.task.done():
            sim.task.cancel()
            await asyncio.gather(sim.task, return_exceptions=True)
        clear_session_measurements(session_id)
    generated_entries = fetch_all(
        """SELECT d.id,d.number,de.pace_offset_ms,tm.team_id,t.name AS team_name
        FROM demo_race_entries de JOIN drivers d ON d.id=de.driver_id
        JOIN team_memberships tm ON tm.driver_id=d.id
          AND tm.start_date<=%s::date AND (tm.end_date IS NULL OR tm.end_date>=%s::date)
        JOIN teams t ON t.id=tm.team_id WHERE de.session_id=%s ORDER BY d.number""",
        (session["scheduled_at"], session["scheduled_at"], session_id),
    )
    drivers = generated_entries or fetch_all(
        """SELECT d.id,d.number,tm.team_id,t.name AS team_name
        FROM drivers d JOIN team_memberships tm ON tm.driver_id=d.id
          AND tm.start_date<=%s::date AND (tm.end_date IS NULL OR tm.end_date>=%s::date)
        JOIN teams t ON t.id=tm.team_id WHERE d.eligibility='ACTIVE' ORDER BY """
        """d.number LIMIT %s""",
        (session["scheduled_at"], session["scheduled_at"], body.cars or 10),
    )
    if not drivers:
        raise HTTPException(409, "No eligible drivers are available")
    if body.cars and len(drivers) < body.cars:
        raise HTTPException(422, "Requested car count exceeds eligible drivers")
    sim = Simulation(
        session_id,
        drivers,
        body.rate_hz or 2.0,
        total_laps=session["total_laps"] or MAX_SESSION_LAPS,
    )
    sim.pace_offsets_ms = {str(d["id"]): d["pace_offset_ms"] for d in generated_entries}
    sim.is_generated = bool(generated_entries)
    marker = fetch_one("SELECT auto_repeat FROM demo_races WHERE session_id=%s", (session_id,))
    sim.auto_repeat = bool(marker and marker["auto_repeat"])
    sim.lap_by_driver = {str(d["id"]): 1 for d in drivers}
    if sim.is_generated:
        restore_simulated_incidents(sim)
    simulations[str(session_id)] = sim
    sim.task = asyncio.create_task(simulation_loop(sim))
    sim.status = "running"
    return sim


async def _reset_session_simulation(
    session_id: UUID, body: SimulationControl, sim: Simulation | None
) -> Simulation:
    session = fetch_one("SELECT state FROM race_sessions WHERE id=%s", (session_id,))
    if not session:
        raise HTTPException(404, "Session not found")
    if session["state"] != "PAUSED":
        raise HTTPException(409, "Pause the session before resetting its simulation")
    ensure_session_reset_allowed(session_id)
    if sim:
        sync_simulation_lifecycle(session_id, "reset")
        if sim.task and not sim.task.done():
            await asyncio.gather(sim.task, return_exceptions=True)
    clear_session_measurements(session_id)
    if not sim:
        sim = Simulation(session_id, [], body.rate_hz or 2.0)
        simulations[str(session_id)] = sim
    return sim


@app.post("/api/sessions/{session_id}/simulate")
async def control_simulation(
    session_id: UUID, body: SimulationControl, user=admin_steward_dependency
):
    if mongo_ready() is None:
        raise HTTPException(503, "MongoDB telemetry store is unavailable")
    sim = simulations.get(str(session_id))
    if body.action == "start":
        sim = await _start_session_simulation(session_id, body, sim)
    elif body.action in {"pause", "resume"}:
        expected, next_status, detail = {
            "pause": ("running", "paused", "Simulation is not running"),
            "resume": ("paused", "running", "Simulation is not paused"),
        }[body.action]
        if not sim or sim.status != expected:
            raise HTTPException(409, detail)
        sim.status = next_status
    elif body.action == "stop":
        if not sim:
            raise HTTPException(409, "Simulation has not started")
        sim.status = "stopped"
        if sim.task and not sim.task.done():
            sim.task.cancel()
            await asyncio.gather(sim.task, return_exceptions=True)
        cancel_automatic_pit_reservations(session_id)
        sim.pit_reservations_by_driver.clear()
    elif body.action == "reset":
        sim = await _reset_session_simulation(session_id, body, sim)
    return {
        "session_id": str(session_id),
        "state": sim.status,
        "cars": len(sim.drivers),
        "rate_hz": sim.rate_hz,
    }


async def _check_ws_runtime_lease(ws: WebSocket) -> bool:
    runtime_lease = getattr(ws.app.state, "runtime_lease", None)
    if runtime_lease is None:
        return True
    try:
        check_runtime_lease(runtime_lease)
    except RuntimeError:
        await ws.close(
            code=1011,
            reason=("Runtime ownership was lost; restart the backend after PostgreSQL recovery."),
        )
        return False
    return True


async def _wait_for_ws_event(ws: WebSocket, queue: asyncio.Queue[Any]) -> dict[str, Any] | None:
    while True:
        try:
            return await asyncio.wait_for(queue.get(), timeout=0.5)
        except TimeoutError:
            if not await _check_ws_runtime_lease(ws):
                return None


def _websocket_authenticated_user(token: str) -> Any:
    claims = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    if _token_is_revoked(claims):
        return None
    return (
        fetch_one("SELECT id FROM users WHERE id=%s", (claims.get("sub"),))
        if claims.get("sub")
        else None
    )


@app.websocket("/api/ws/sessions/{session_id}")
async def session_ws(ws: WebSocket, session_id: UUID):
    if not await _check_ws_runtime_lease(ws):
        return
    origin = ws.headers.get("origin")
    if origin is not None and origin not in CORS_ORIGINS:
        await ws.close(code=4403, reason="Origin not allowed")
        return
    protocols = ws.scope.get("subprotocols", [])
    subprotocol_token = websocket_bearer(protocols)
    cookie_token = ws.cookies.get("apexgrid_session")
    token = subprotocol_token or cookie_token
    if not token:
        await ws.close(code=4401, reason="Expected apexgrid.jwt subprotocol and bearer token")
        return
    try:
        user = _websocket_authenticated_user(token)
    except Exception:
        user = None
    if not user:
        await ws.close(code=4401, reason="Invalid or expired token")
        return
    await ws.accept(subprotocol="apexgrid.jwt" if subprotocol_token else None)
    q = bus.subscribe(session_id)
    try:
        while True:
            event = await _wait_for_ws_event(ws, q)
            if event is None:
                return
            if not await _check_ws_runtime_lease(ws):
                return
            await ws.send_json(event)
    except WebSocketDisconnect:
        pass
    finally:
        bus.unsubscribe(session_id, q)


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
