from __future__ import annotations

import asyncio
import hmac
import logging
import random
import secrets
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from uuid import UUID, uuid4

import bcrypt
import jwt
from bson import ObjectId
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
from psycopg.errors import CheckViolation, ExclusionViolation, ForeignKeyViolation, UniqueViolation
from psycopg.rows import dict_row, tuple_row
from psycopg_pool import PoolClosed, PoolTimeout
from pydantic import BaseModel
from pymongo import DESCENDING, MongoClient
from pymongo.errors import PyMongoError
from starlette.middleware.base import RequestResponseEndpoint

from .analytics_router import create_analytics_router
from .auth_cookie import clear_auth_cookies, create_csrf_token, set_auth_cookies, verify_csrf_token
from .config import (
    APP_ENV,
    AUTO_DEMO_RACE,
    CORS_ORIGINS,
    JWT_ALGORITHM,
    JWT_MINUTES,
    JWT_SECRET,
    MONGODB_DATABASE,
    MONGODB_URL,
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
from .demo_race_repository import get_demo_race_row, list_demo_race_ids
from .demo_race_router import create_demo_race_router
from .pit_repository import PIT_RESERVATION_SELECT, load_pit_strategy_rows, load_pit_telemetry
from .pit_router import create_pit_router
from .pit_strategy_router import create_pit_strategy_router
from .pit_strategy_service import project_pit_strategy
from .runtime_lease import acquire_runtime_lease, check_runtime_lease
from .schemas_auth import Login, UserCreate, UserPatch
from .schemas_competition import MembershipIn, MembershipPatch, ResultIn
from .schemas_operations import Action, AutoReservationIn, Decision, IncidentIn, ReservationIn
from .schemas_simulation import DemoRaceCreate, SimulationControl
from .simulation_core import MAX_SESSION_LAPS, Simulation, calculate_sector_performance
from .telemetry_router import create_telemetry_router
from .user_router import create_user_router

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("apexgrid")
bearer = HTTPBearer(auto_error=False)
PIT_TIRE_STINT_LAPS = 18


def tire_stint_target(compound: str, car_number: int) -> int:
    base = {"SOFT": 16, "MEDIUM": 20, "HARD": 24}.get(compound, PIT_TIRE_STINT_LAPS)
    return max(12, min(28, base + int(car_number) % 5 - 2))
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
            try:
                close_pool()
            except Exception:
                pass
        finally:
            application.state.runtime_lease = None
            runtime_lease.close()


app = FastAPI(title="ApexGrid API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def require_runtime_lease(request: Request, call_next: RequestResponseEndpoint) -> Response:
    runtime_lease = getattr(request.app.state, "runtime_lease", None)
    if runtime_lease is not None:
        try:
            check_runtime_lease(runtime_lease)
        except RuntimeError:
            return JSONResponse(
                status_code=503,
                content={"detail": "PostgreSQL runtime ownership was lost. Restart the backend to restore service."},
            )
    return await call_next(request)


def jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat().replace("+00:00", "Z")
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, ObjectId):
        return str(value)
    return value


def telemetry_ws_payload(packet: dict[str, Any], inserted_id: ObjectId | str) -> dict[str, Any]:
    """Build a JSON-safe telemetry packet without leaking Mongo's `_id`."""
    payload = {key: value for key, value in packet.items() if key != "_id"}
    payload["id"] = str(inserted_id)
    return jsonable(payload)


def websocket_bearer(subprotocols: list[str]) -> str | None:
    if len(subprotocols) >= 2 and subprotocols[0] == "apexgrid.jwt" and subprotocols[1]:
        return subprotocols[1]
    return None


@app.exception_handler(UniqueViolation)
@app.exception_handler(ExclusionViolation)
async def conflict_handler(_, exc):
    return JSONResponse(status_code=409, content={"detail": "Resource conflicts with an existing record"})


@app.exception_handler(ForeignKeyViolation)
async def reference_conflict_handler(_, exc):
    return JSONResponse(status_code=409, content={"detail": "Resource is referenced by official records"})


@app.exception_handler(IntegrityError)
async def integrity_handler(_, exc):
    code=getattr(exc,"sqlstate",None)
    if code in {"23502","23514","22001","22003"}:
        status,detail=422,"Record violates a required field or value constraint"
    else:
        status,detail=409,"Record conflicts with existing data"
    return JSONResponse(status_code=status,content={"detail":detail})


@app.exception_handler(OperationalError)
@app.exception_handler(PoolTimeout)
@app.exception_handler(PoolClosed)
async def database_unavailable_handler(_, exc):
    return JSONResponse(status_code=503,content={"detail":"PostgreSQL is unavailable"})


def require_db():
    if get_pool().closed:
        raise HTTPException(503, "PostgreSQL is unavailable")


def require_allowed_origin(request: Request):
    origin = request.headers.get("origin")
    if origin is not None and origin not in CORS_ORIGINS:
        raise HTTPException(403, "Origin not allowed")


bearer_dependency = Depends(bearer)


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
    return jsonable(user)


def roles(*allowed):
    def check(user=Depends(current_user)):
        if user["role"] not in allowed:
            raise HTTPException(403, "Insufficient role")
        return user
    return check


def create_automatic_reservation(session_id: UUID | str, team_id: UUID | str,
                                 driver_id: UUID | str | None, duration: timedelta):
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT reserve_pit_box_auto(%s,%s,%s,%s) AS id",
                    (session_id, team_id, driver_id, duration))
        reservation_id = cur.fetchone()["id"]
        cur.execute(PIT_RESERVATION_SELECT + " WHERE r.id=%s", (reservation_id,))
        return cur.fetchone()


def limit_offset(limit: int, offset: int):
    return min(limit, 200), max(offset, 0)


def validate_session_laps(table: str, values: dict[str, Any]):
    if table != "race_sessions" or "total_laps" not in values or values["total_laps"] is None:
        return
    value = values["total_laps"]
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= MAX_SESSION_LAPS:
        raise HTTPException(422, f"total_laps must be an integer between 0 and {MAX_SESSION_LAPS}")


def crud_routes(resource: str, table: str, cols: tuple[str, ...], joins: str = "", select: str | None = None):
    # Names here are hard-coded contract identifiers, never user supplied SQL.
    columns = ",".join(cols)
    projection = select or f"{table}.*"
    base = f"SELECT {projection} FROM {table} {joins}"
    prefix = f"/api/{resource}"

    @app.get(prefix)
    def listing(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0), user=Depends(current_user)):
        l, o = limit_offset(limit, offset)
        return jsonable(list_crud_rows(base, l, o))

    @app.get(prefix + "/{item_id}")
    def get_item(item_id: UUID, user=Depends(current_user)):
        result = get_crud_row(base, table, item_id)
        if not result:
            raise HTTPException(404, f"{resource[:-1].capitalize()} not found")
        return jsonable(result)

    @app.post(prefix, status_code=201)
    def create_item(payload: dict[str, Any], user=Depends(roles("ADMIN"))):
        clean = {k: v for k, v in payload.items() if k in cols and k != "id"}
        if not clean:
            raise HTTPException(422, "At least one writable field is required")
        validate_session_laps(table, clean)
        row = create_crud_row(table, clean)
        return jsonable(row)

    @app.patch(prefix + "/{item_id}")
    def update_item(item_id: UUID, payload: dict[str, Any], user=Depends(roles("ADMIN"))):
        clean = {k: v for k, v in payload.items() if k in cols and k != "id"}
        if not clean:
            raise HTTPException(422, "At least one writable field is required")
        validate_session_laps(table, clean)
        if table == "race_sessions":
            existing = fetch_one("SELECT state FROM race_sessions WHERE id=%s", (item_id,))
            if not existing:
                raise HTTPException(404, "Session not found")
            if existing["state"] != "SCHEDULED" and set(clean) & {"event_id", "session_type", "scheduled_at", "total_laps"}:
                raise HTTPException(409, "Session context and lap count cannot change after a session starts")
        row = update_crud_row(table, item_id, clean)
        if not row:
            raise HTTPException(404, f"{resource[:-1].capitalize()} not found")
        return jsonable(row)

    @app.delete(prefix + "/{item_id}", status_code=204)
    def delete_item(item_id: UUID, user=Depends(roles("ADMIN"))):
        try:
            delete_crud_row(table, resource, item_id, telemetry_collection)
        except CrudDeleteError as exc:
            raise HTTPException(exc.status_code, exc.detail) from exc
        return None


crud_routes("championships", "championships", ("id", "name", "season"))
crud_routes("circuits", "circuits", ("id", "name", "country", "length_km"))
crud_routes("teams", "teams", ("id", "name", "principal_user_id"), "LEFT JOIN users u ON u.id=teams.principal_user_id", "teams.*,u.full_name AS principal_name")
crud_routes("drivers", "drivers", ("id", "user_id", "licence_number", "number"), "LEFT JOIN users u ON u.id=drivers.user_id LEFT JOIN team_memberships tm ON tm.driver_id=drivers.id AND tm.end_date IS NULL LEFT JOIN teams t ON t.id=tm.team_id", "drivers.*,u.full_name,u.email,t.name AS team_name")
crud_routes("events", "race_events", ("id", "championship_id", "circuit_id", "round_number", "name", "start_date"), "LEFT JOIN championships ch ON ch.id=race_events.championship_id LEFT JOIN circuits c ON c.id=race_events.circuit_id", "race_events.*,ch.name AS championship_name,c.name AS circuit_name,c.country AS circuit_country")
crud_routes("sessions", "race_sessions", ("id", "event_id", "session_type", "scheduled_at", "total_laps", "safety_car"), "LEFT JOIN race_events e ON e.id=race_sessions.event_id LEFT JOIN circuits c ON c.id=e.circuit_id", "race_sessions.*,e.name AS event_name,c.name AS circuit_name")


@app.get("/api/drivers/{driver_id}/memberships")
def driver_memberships(driver_id: UUID, user=Depends(current_user)):
    return jsonable(fetch_all("SELECT m.*,t.name AS team_name FROM team_memberships m JOIN teams t ON t.id=m.team_id WHERE m.driver_id=%s ORDER BY m.start_date DESC", (driver_id,)))


@app.get("/api/teams/{team_id}/memberships")
def team_memberships(team_id: UUID, user=Depends(current_user)):
    return jsonable(fetch_all("SELECT m.*,u.full_name AS driver_name,d.number,d.licence_number FROM team_memberships m JOIN drivers d ON d.id=m.driver_id LEFT JOIN users u ON u.id=d.user_id WHERE m.team_id=%s ORDER BY m.start_date DESC", (team_id,)))


@app.post("/api/team-memberships", status_code=201)
def create_membership(body: MembershipIn, user=Depends(roles("ADMIN"))):
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute("INSERT INTO team_memberships(driver_id,team_id,start_date,end_date) VALUES (%s,%s,%s,%s) RETURNING *", (body.driver_id,body.team_id,body.start_date,body.end_date))
        row=cur.fetchone()
    return jsonable(row)


@app.patch("/api/team-memberships/{membership_id}")
def update_membership(membership_id: UUID, body: MembershipPatch, user=Depends(roles("ADMIN"))):
    values=body.model_dump(exclude_unset=True)
    if not values: raise HTTPException(422,"At least one field is required")
    fields=list(values)
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute("UPDATE team_memberships SET "+",".join(f"{f}=%s" for f in fields)+" WHERE id=%s RETURNING *",[values[f] for f in fields]+[membership_id])
        row=cur.fetchone()
    if not row: raise HTTPException(404,"Membership not found")
    return jsonable(row)


@app.post("/api/auth/login")
def login(body: Login, response: Response, request: Request):
    require_allowed_origin(request)
    try:
        user = fetch_one(
            "SELECT id,email,password_hash,full_name,role "
            "FROM users WHERE lower(email)=lower(%s)",
            (body.email,),
        )
    except Exception:
        raise HTTPException(503, "PostgreSQL is unavailable")
    try:
        valid_password = bool(
            user
            and bcrypt.checkpw(
                body.password.encode(), user["password_hash"].encode()
            )
        )
    except (ValueError, TypeError):
        valid_password = False
    if not valid_password:
        raise HTTPException(401, "Invalid email or password")
    expiry = datetime.now(timezone.utc) + timedelta(minutes=JWT_MINUTES)
    session_id = secrets.token_urlsafe(32)
    token = jwt.encode(
        {
            "sub": str(user["id"]),
            "role": user["role"],
            "exp": expiry,
            "jti": session_id,
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )
    csrf_token = create_csrf_token(session_id, JWT_SECRET)
    set_auth_cookies(response, token, csrf_token, secure=APP_ENV != "local")
    user_data = jsonable(
        {key: user[key] for key in ("id", "email", "full_name", "role")}
    )
    if request.headers.get("origin"):
        return {"user": user_data}
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user_data,
    }


@app.get("/api/auth/me")
def me(user=Depends(current_user)):
    return user


@app.post("/api/auth/logout")
def logout(response: Response, user=Depends(current_user)):
    clear_auth_cookies(response, secure=APP_ENV != "local")
    return {"detail": "Logged out"}


app.include_router(create_user_router(roles, jsonable))


@app.post("/api/sessions/{session_id}/action")
async def session_action(session_id: UUID, body: Action, user=Depends(roles("ADMIN", "STEWARD"))):
    transitions = {"start": ("SCHEDULED", "ACTIVE"), "pause": ("ACTIVE", "PAUSED"), "resume": ("PAUSED", "ACTIVE"), "finish": (("ACTIVE", "PAUSED"), "COMPLETED"), "reset": (("ACTIVE", "PAUSED", "COMPLETED", "CANCELLED"), "SCHEDULED")}
    before, after = transitions[body.action]
    states = before if isinstance(before, tuple) else (before,)
    now = datetime.now(timezone.utc)
    if body.action == "reset":
        existing = fetch_one("SELECT state FROM race_sessions WHERE id=%s", (session_id,))
        if not existing:
            raise HTTPException(404, "Session not found")
        if existing["state"] not in states:
            raise HTTPException(409, "Invalid session state transition")
        ensure_session_reset_allowed(session_id)
        sim = simulations.get(str(session_id))
        if sim:
            sim.status = "stopped"
            if sim.task and not sim.task.done():
                sim.task.cancel()
        if sim and sim.task and not sim.task.done():
            await asyncio.gather(sim.task, return_exceptions=True)
    set_fields = "state=%s"
    params: list[Any] = [after]
    if body.action == "start":
        set_fields += ",started_at=%s,ended_at=NULL"; params.append(now)
    elif body.action == "finish":
        set_fields += ",ended_at=%s"; params.append(now)
    elif body.action == "reset":
        set_fields += ",started_at=NULL,ended_at=NULL,safety_car=FALSE"; 
    params.extend([session_id, list(states)])
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(f"UPDATE race_sessions SET {set_fields} WHERE id=%s AND state=ANY(%s) RETURNING *", params)
        row = cur.fetchone()
    if not row:
        if not fetch_one("SELECT id FROM race_sessions WHERE id=%s", (session_id,)):
            raise HTTPException(404, "Session not found")
        raise HTTPException(409, "Invalid session state transition")
    if body.action == "reset":
        clear_session_measurements(session_id)
        sync_simulation_lifecycle(session_id, "reset")
    else:
        sync_simulation_lifecycle(session_id, body.action)
        if body.action == "finish":
            cancel_automatic_pit_reservations(session_id)
            sim = simulations.get(str(session_id))
            if sim:
                sim.pit_reservations_by_driver.clear()
    result = jsonable(row)
    publish(session_id, "session.state", result)
    return result


@app.get("/api/sessions/{session_id}/results")
def results(session_id: UUID, user=Depends(current_user)):
    return jsonable(fetch_all("""SELECT r.*,u.full_name AS driver_name,d.number,t.name AS team_name,
      EXISTS(SELECT 1 FROM incident_reports i JOIN penalties p ON p.incident_id=i.id
        WHERE i.session_id=r.session_id AND (p.time_seconds>0 OR p.grid_places>0)) AS provisional
      FROM session_results r JOIN race_sessions s ON s.id=r.session_id
      JOIN drivers d ON d.id=r.driver_id JOIN users u ON u.id=d.user_id
      LEFT JOIN LATERAL (SELECT team_id FROM team_memberships m WHERE m.driver_id=d.id
        AND m.start_date<=s.scheduled_at::date AND (m.end_date IS NULL OR m.end_date>=s.scheduled_at::date)
        ORDER BY m.start_date DESC LIMIT 1) membership ON true
      LEFT JOIN teams t ON t.id=membership.team_id WHERE r.session_id=%s ORDER BY r.position""", (session_id,)))


@app.post("/api/sessions/{session_id}/results")
def save_results(session_id: UUID, rows: list[ResultIn], user=Depends(roles("ADMIN", "STEWARD"))):
    if len(rows) > 100:
        raise HTTPException(422, "At most 100 results per request")
    session = fetch_one("""SELECT s.state,EXISTS(SELECT 1 FROM demo_races d WHERE d.session_id=s.id) AS generated
        FROM race_sessions s WHERE s.id=%s""", (session_id,))
    if not session:
        raise HTTPException(404, "Session not found")
    if session["state"] not in {"ACTIVE", "PAUSED", "COMPLETED"}:
        raise HTTPException(409, "Results cannot be recorded for a scheduled or cancelled session")
    sim = simulations.get(str(session_id))
    if session["generated"] and session["state"] == "ACTIVE" and sim and sim.status == "running":
        raise HTTPException(409, "The active demo simulator owns this session's results")
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        for r in rows:
            cur.execute("INSERT INTO session_results(session_id,driver_id,position,lap_time_ms,pole,fastest_lap,classified) VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(session_id,driver_id) DO UPDATE SET position=excluded.position,lap_time_ms=excluded.lap_time_ms,pole=excluded.pole,fastest_lap=excluded.fastest_lap,classified=excluded.classified", (session_id,r.driver_id,r.position,r.lap_time_ms,r.pole,r.fastest_lap,r.classified))
        cur.execute("SELECT r.*,u.full_name AS driver_name FROM session_results r JOIN drivers d ON d.id=r.driver_id JOIN users u ON u.id=d.user_id WHERE r.session_id=%s ORDER BY r.position", (session_id,))
        result = cur.fetchall()
        if session["state"] == "COMPLETED":
            classified_positions = [r["position"] for r in result if r["classified"]]
            if (any(position is None for position in classified_positions)
                    or sorted(classified_positions) != list(range(1, len(classified_positions) + 1))):
                raise HTTPException(422, "Classified result positions must be contiguous starting at 1")
    publish(session_id, "timing.update", jsonable(result))
    return jsonable(result)


@app.post("/api/championships/{championship_id}/recalculate")
def recalculate(championship_id: UUID, user=Depends(roles("ADMIN", "STEWARD"))):
    with connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT recalculate_standings(%s)", (championship_id,))
    return {"championship_id": str(championship_id), "recalculated": True}


@app.get("/api/championships/{championship_id}/standings")
def standings(championship_id: UUID, user=Depends(current_user)):
    return jsonable(fetch_all("""SELECT s.*,u.full_name AS driver_name,d.number,t.name AS team_name,
      EXISTS(SELECT 1 FROM race_events re JOIN race_sessions rs ON rs.event_id=re.id
        JOIN incident_reports i ON i.session_id=rs.id JOIN penalties p ON p.incident_id=i.id
        WHERE re.championship_id=s.championship_id AND rs.session_type='RACE'
          AND rs.state='COMPLETED' AND (p.time_seconds>0 OR p.grid_places>0)) AS provisional
      FROM driver_standings s JOIN drivers d ON d.id=s.driver_id JOIN users u ON u.id=d.user_id
      LEFT JOIN team_memberships tm ON tm.driver_id=d.id AND tm.end_date IS NULL
      LEFT JOIN teams t ON t.id=tm.team_id WHERE s.championship_id=%s ORDER BY s.rank""", (championship_id,)))


@app.get("/api/incidents")
def get_incidents(state: str | None = None, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0), user=Depends(current_user)):
    sql = "SELECT i.*,u.full_name AS driver_name,d.number,s.session_type,e.name AS event_name FROM incident_reports i JOIN drivers d ON d.id=i.driver_id JOIN users u ON u.id=d.user_id JOIN race_sessions s ON s.id=i.session_id JOIN race_events e ON e.id=s.event_id"
    params: list[Any] = []
    if state:
        if state not in {"OPEN", "APPROVED", "REJECTED"}: raise HTTPException(422, "Invalid incident state")
        sql += " WHERE i.state=%s"; params.append(state)
    sql += " ORDER BY i.reported_at DESC LIMIT %s OFFSET %s"; params.extend(limit_offset(limit,offset))
    return jsonable(fetch_all(sql, params))


@app.post("/api/incidents", status_code=201)
def create_incident(body: IncidentIn, user=Depends(roles("ADMIN", "STEWARD"))):
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT total_laps FROM race_sessions WHERE id=%s", (body.session_id,))
        session = cur.fetchone()
        if not session:
            raise HTTPException(404, "Session not found")
        if session["total_laps"] and body.lap > session["total_laps"]:
            raise HTTPException(422, "Incident lap exceeds the session lap count")
        cur.execute("SELECT 1 FROM demo_races WHERE session_id=%s", (body.session_id,))
        if cur.fetchone():
            cur.execute("SELECT 1 FROM demo_race_entries WHERE session_id=%s AND driver_id=%s", (body.session_id, body.driver_id))
            if not cur.fetchone():
                raise HTTPException(422, "Driver is not entered in this generated race")
        cur.execute("INSERT INTO incident_reports(session_id,driver_id,lap,description) VALUES (%s,%s,%s,%s) RETURNING *", (body.session_id,body.driver_id,body.lap,body.description))
        row=cur.fetchone()
    result=jsonable(row); publish(body.session_id,"incident.update",result); return result


@app.post("/api/incidents/{incident_id}/decision")
def decide_incident(incident_id: UUID, body: Decision, user=Depends(roles("ADMIN", "STEWARD"))):
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT * FROM incident_reports WHERE id=%s FOR UPDATE", (incident_id,)); incident=cur.fetchone()
        if not incident: raise HTTPException(404,"Incident not found")
        if incident["state"] != "OPEN": raise HTTPException(409,"Incident has already been decided")
        state="APPROVED" if body.approve else "REJECTED"
        cur.execute("UPDATE incident_reports SET state=%s,decided_by=%s,decision_notes=%s WHERE id=%s RETURNING *",(state,user["id"],body.notes,incident_id)); updated=cur.fetchone()
        penalty=None
        if body.approve and (body.points or body.time_seconds or body.grid_places):
            cur.execute("INSERT INTO penalties(incident_id,driver_id,points,time_seconds,grid_places) VALUES (%s,%s,%s,%s,%s) RETURNING *",(incident_id,incident["driver_id"],body.points,body.time_seconds,body.grid_places)); penalty=cur.fetchone()
        cur.execute("SELECT d.eligibility,COALESCE((SELECT pp.points FROM penalty_points pp JOIN championships c ON c.season=pp.season JOIN race_events e ON e.championship_id=c.id JOIN race_sessions s ON s.event_id=e.id WHERE s.id=%s AND pp.driver_id=d.id LIMIT 1),0) AS season_points FROM drivers d WHERE d.id=%s",(incident["session_id"],incident["driver_id"]))
        driver=cur.fetchone()
    out={"incident":jsonable(updated),"penalty":jsonable(penalty),"driver":jsonable(driver)}
    publish(incident["session_id"],"incident.update",out)
    return out


app.include_router(create_pit_router(current_user, jsonable))


@app.post("/api/pit-reservations", status_code=201)
def reserve_pit(body: ReservationIn, user=Depends(roles("ADMIN", "STEWARD", "PRINCIPAL"))):
    if user["role"] == "PRINCIPAL":
        own_team=fetch_one("SELECT id FROM teams WHERE id=%s AND principal_user_id=%s",(body.team_id,user["id"]))
        if not own_team:
            raise HTTPException(403,"Principals may reserve pit boxes only for their own team")
    try:
        with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT reserve_pit_box(%s,%s,%s,%s,%s) AS id",(body.pit_box_id,body.session_id,body.team_id,body.starts_at,body.ends_at))
            reservation_id=cur.fetchone()["id"]
            cur.execute(PIT_RESERVATION_SELECT + " WHERE r.id=%s",(reservation_id,)); row=cur.fetchone()
    except (UniqueViolation,ExclusionViolation):
        raise HTTPException(409,"Pit box is already reserved for this time")
    except ForeignKeyViolation as exc:
        raise HTTPException(404,"Pit box, session, or team not found") from exc
    except Exception as exc:
        if getattr(exc,"sqlstate",None)=="23514":
            raise HTTPException(422,"Pit box and session must belong to the same event") from exc
        if getattr(exc,"sqlstate",None)=="23P01":
            raise HTTPException(409,"Pit box is already reserved for this time") from exc
        raise
    result=jsonable(row); publish(body.session_id,"pit.update",result); return result


@app.post("/api/pit-reservations/auto", status_code=201)
def reserve_pit_auto(body: AutoReservationIn, user=Depends(roles("ADMIN", "STEWARD", "PRINCIPAL"))):
    if user["role"] == "PRINCIPAL":
        own_team = fetch_one("SELECT id FROM teams WHERE id=%s AND principal_user_id=%s", (body.team_id, user["id"]))
        if not own_team:
            raise HTTPException(403, "Principals may reserve pit boxes only for their own team")
    session = fetch_one("SELECT state FROM race_sessions WHERE id=%s", (body.session_id,))
    if not session:
        raise HTTPException(404, "Session not found")
    if session["state"] not in {"ACTIVE", "PAUSED"}:
        raise HTTPException(409, "Pit reservations require an active or paused session")
    sim = simulations.get(str(body.session_id))
    rate_hz = sim.rate_hz if sim else 2.0
    pit_duration = timedelta(seconds=max(0.6, 3.0 / max(rate_hz, 0.2)))
    try:
        reservation = create_automatic_reservation(body.session_id, body.team_id, body.driver_id,
                                                   pit_duration)
    except (UniqueViolation, ExclusionViolation) as exc:
        raise HTTPException(409, "Driver or pit box already has a conflicting reservation") from exc
    except ForeignKeyViolation as exc:
        raise HTTPException(404, "Session, team, driver, or pit box not found") from exc
    except Exception as exc:
        sqlstate = getattr(exc, "sqlstate", None)
        if sqlstate == "P0002":
            raise HTTPException(409, "The event has no pit boxes") from exc
        if sqlstate == "23514":
            raise HTTPException(422, "Driver must be an eligible member of the team for this session") from exc
        if sqlstate == "23505":
            raise HTTPException(409, "Driver already has an open pit reservation for this session") from exc
        raise
    result = jsonable(reservation)
    publish(body.session_id, "pit.update", result)
    return result


class ReservationStatus(BaseModel):
    status: Literal["CANCELLED", "COMPLETED"]


@app.patch("/api/pit-reservations/{reservation_id}")
def update_pit_reservation(reservation_id: UUID, body: ReservationStatus, user=Depends(roles("ADMIN", "STEWARD", "PRINCIPAL"))):
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute("""SELECT r.*,t.principal_user_id FROM pit_reservations r
            JOIN teams t ON t.id=r.team_id WHERE r.id=%s FOR UPDATE OF r""", (reservation_id,))
        reservation = cur.fetchone()
        if not reservation:
            raise HTTPException(404, "Pit reservation not found")
        if user["role"] == "PRINCIPAL" and str(reservation["principal_user_id"]) != user["id"]:
            raise HTTPException(403, "Principals may update reservations only for their own team")
        if reservation["status"] != "RESERVED":
            raise HTTPException(409, "Pit reservation is already closed")
        cur.execute("UPDATE pit_reservations SET status=%s WHERE id=%s", (body.status, reservation_id))
        cur.execute(PIT_RESERVATION_SELECT + " WHERE r.id=%s", (reservation_id,))
        updated = cur.fetchone()
    result = jsonable(updated)
    publish(updated["session_id"], "pit.update", result)
    return result


def mongo_ready():
    if telemetry_collection is None:
        raise HTTPException(503,"MongoDB telemetry store is unavailable")
    return telemetry_collection


def publish(session_id, kind, data):
    bus.send(session_id,{"type":kind,"ts":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),"session_id":str(session_id),"data":jsonable(data)})


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


def list_demo_races(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0), user=Depends(current_user)):
    ids = list_demo_race_ids(limit, offset)
    return [demo_race_row(row["session_id"]) for row in ids]


app.include_router(create_demo_race_router(current_user, demo_race_row, list_demo_race_ids))


def choose_demo_car_numbers(car_count: int) -> list[int]:
    # Numbers are unique in this grid; historical drivers may reuse them.
    return random.sample(range(11, 100), car_count)


def _make_demo_race(cars: int | None = None, auto_repeat: bool = False):
    if mongo_ready() is None:
        raise HTTPException(503, "MongoDB telemetry store is unavailable")
    car_count = cars if cars is not None else random.randint(8, 16)
    session_id, event_id = uuid4(), uuid4()
    now = datetime.now(timezone.utc)
    given = ["Amelia", "Rafael", "Maya", "Theo", "Nina", "Luca", "Aisha", "Felix", "Sofia", "Ethan", "Leila", "Oscar", "Priya", "Mateo", "Zara", "Jonah", "Ines", "Kai", "Elena", "Arjun"]
    family = ["Bennett", "Costa", "Shah", "Moreau", "Kim", "Novak", "Singh", "Fischer", "Alvarez", "Tanaka", "Dubois", "Reed", "Petrov", "Okafor", "Lindholm", "Santos", "Kaur", "Weber", "Nakamura", "Clarke"]
    names = [f"{a} {b}" for a, b in zip(random.sample(given, car_count), random.sample(family, car_count))]
    generated = []
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT id FROM championships WHERE name='ApexGrid Live Demo' AND season=extract(year from current_date)::int")
        championship = cur.fetchone()
        if not championship:
            cur.execute("INSERT INTO championships(name,season) VALUES ('ApexGrid Live Demo',extract(year from current_date)::int) RETURNING id")
            championship = cur.fetchone()
        cur.execute("SELECT id,name FROM circuits ORDER BY name")
        circuits = cur.fetchall()
        cur.execute("SELECT id,name FROM teams ORDER BY name")
        teams = cur.fetchall()
        if not circuits or not teams:
            raise HTTPException(409, "Demo race requires at least one circuit and one team")
        cur.execute("SELECT pg_advisory_xact_lock(hashtext('apexgrid-demo-race-create'))")
        cur.execute("SELECT COALESCE(max(round_number),0)+1 AS round FROM race_events WHERE championship_id=%s", (championship["id"],))
        round_number = cur.fetchone()["round"]
        numbers = choose_demo_car_numbers(car_count)
        circuit = random.choice(circuits)
        event_name = f"{circuit['name']} Grand Prix — {random.choice(['Sprint Weekend', 'Night Race', 'Coastal Classic', 'Autumn Round'])}"
        total_laps = random.randint(45, MAX_SESSION_LAPS)
        cur.execute("INSERT INTO race_events(id,championship_id,circuit_id,round_number,name,start_date) VALUES (%s,%s,%s,%s,%s,%s)", (event_id, championship["id"], circuit["id"], round_number, event_name, now))
        cur.execute("INSERT INTO race_sessions(id,event_id,session_type,state,scheduled_at,started_at,total_laps) VALUES (%s,%s,'RACE','ACTIVE',%s,%s,%s)", (session_id,event_id,now,now,total_laps))
        cur.execute("INSERT INTO demo_races(session_id,event_id,auto_repeat) VALUES (%s,%s,%s)", (session_id,event_id,auto_repeat))
        cur.execute("INSERT INTO pit_boxes(event_id,number) SELECT %s,n FROM generate_series(1,4) AS n ON CONFLICT(event_id,number) DO NOTHING", (event_id,))
        for idx, full_name in enumerate(names):
            number = numbers[idx]
            user_id, driver_id = uuid4(), uuid4()
            email = f"demo-{user_id.hex}@apexgrid.invalid"
            secret = secrets.token_urlsafe(40)
            password_hash = bcrypt.hashpw(secret.encode(), bcrypt.gensalt(rounds=10)).decode()
            cur.execute("INSERT INTO users(id,email,password_hash,full_name,role) VALUES (%s,%s,%s,%s,'DRIVER')", (user_id,email,password_hash,full_name))
            cur.execute("INSERT INTO drivers(id,user_id,licence_number,number) VALUES (%s,%s,%s,%s)", (driver_id,user_id,f"AGD-{driver_id.hex[:12].upper()}",number))
            team = teams[idx % len(teams)]
            cur.execute("INSERT INTO team_memberships(driver_id,team_id,start_date) VALUES (%s,%s,%s)", (driver_id,team["id"],now.date()))
            offset = random.randint(-1200, 1600)
            cur.execute("INSERT INTO demo_race_entries(session_id,driver_id,pace_offset_ms) VALUES (%s,%s,%s)", (session_id,driver_id,offset))
            generated.append({"id":driver_id,"number":number,"pace_offset_ms":offset,
                              "team_id":team["id"],"team_name":team["name"]})
    sim = Simulation(session_id, generated, 2.0, total_laps=total_laps)
    sim.auto_repeat = auto_repeat
    sim.is_generated = True
    sim.pace_offsets_ms = {str(d["id"]):d["pace_offset_ms"] for d in generated}
    sim.lap_by_driver = {str(d["id"]):1 for d in generated}
    sim.elapsed_by_driver = {str(d["id"]):0 for d in generated}
    simulations[str(session_id)] = sim
    sim.status = "running"
    return demo_race_row(session_id)


def launch_demo_simulation(session_id: UUID | str):
    sim = simulations[str(session_id)]
    sim.status = "running"
    sim.task = asyncio.create_task(simulation_loop(sim))


def restore_simulation_from_telemetry(sim: "Simulation"):
    """Resume an active generated race without deleting its recorded laps."""
    col = mongo_ready()
    for driver in sim.drivers:
        driver_id = str(driver["id"])
        latest = col.find_one({"session_id": str(sim.session_id), "driver_id": driver_id}, sort=[("ts", DESCENDING)])
        sim.lap_by_driver[driver_id] = int(latest.get("lap", 1)) if latest else 1
        sim.sector_by_driver[driver_id] = int(latest.get("sector", 0)) if latest else 0
        sim.elapsed_by_driver[driver_id] = int(latest.get("elapsed_ms", 0)) if latest else 0
        sim.sector_splits_by_driver[driver_id] = list(latest.get("sector_ms") or []) if latest else []
        sim.next_sector_due_by_driver[driver_id] = sim.elapsed_by_driver[driver_id]
        if latest and latest.get("last_lap_ms"):
            sim.last_lap_by_driver[driver_id] = int(latest["last_lap_ms"])
        sim.tire_age_by_driver[driver_id] = int(latest.get("tire_age_laps", 0)) if latest else 0
        sim.tire_wear_by_driver[driver_id] = float(latest.get("tire_wear_pct", 0)) if latest else 0.0
        if latest and latest.get("tire_compound"):
            sim.compound_by_driver[driver_id] = latest["tire_compound"]
    sim.race_clock_ms = max(sim.elapsed_by_driver.values(), default=0)


def restore_simulated_incidents(sim: "Simulation"):
    """Keep a restarted simulator from duplicating reports already in the archive."""
    sim.incident_laps_recorded = {
        row["lap"] for row in fetch_all(
            "SELECT DISTINCT lap FROM incident_reports WHERE session_id=%s", (sim.session_id,)
        )
    }


async def resume_or_create_auto_demo_race(create_if_missing: bool = True):
    active_races = fetch_all("SELECT s.id,s.total_laps,d.auto_repeat FROM race_sessions s JOIN demo_races d ON d.session_id=s.id WHERE s.state='ACTIVE' ORDER BY d.created_at")
    for active in active_races:
        session_id = active["id"]
        entries = fetch_all("""SELECT d.id,d.number,de.pace_offset_ms,tm.team_id,t.name AS team_name
            FROM demo_race_entries de JOIN drivers d ON d.id=de.driver_id
            JOIN race_sessions s ON s.id=de.session_id
            JOIN team_memberships tm ON tm.driver_id=d.id AND tm.start_date<=s.scheduled_at::date
              AND (tm.end_date IS NULL OR tm.end_date>=s.scheduled_at::date)
            JOIN teams t ON t.id=tm.team_id WHERE de.session_id=%s ORDER BY d.number""", (session_id,))
        if not entries:
            log.error("Active generated race %s has no entries", session_id)
            continue
        sim = Simulation(session_id, entries, 2.0, total_laps=active["total_laps"])
        sim.pace_offsets_ms = {str(d["id"]):d["pace_offset_ms"] for d in entries}
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


@app.post("/api/demo-races", status_code=201)
async def create_demo_race(body: DemoRaceCreate = DemoRaceCreate(), user=Depends(roles("ADMIN", "STEWARD"))):
    race = await asyncio.to_thread(_make_demo_race, body.cars)
    launch_demo_simulation(race["session_id"])
    return demo_race_row(race["session_id"])


@app.delete("/api/demo-races/{session_id}", status_code=204)
async def delete_demo_race(session_id: UUID, user=Depends(roles("ADMIN", "STEWARD"))):
    sim = simulations.get(str(session_id))
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute("""SELECT d.session_id,d.event_id,e.championship_id FROM demo_races d
            JOIN race_events e ON e.id=d.event_id WHERE d.session_id=%s FOR UPDATE OF d""", (session_id,))
        marker = cur.fetchone()
        if not marker:
            raise HTTPException(404, "Generated demo race not found")
        col = mongo_ready()
        if col is None:
            raise HTTPException(503, "MongoDB telemetry store is unavailable")
        cur.execute("SELECT 1 FROM incident_reports i JOIN penalties p ON p.incident_id=i.id WHERE i.session_id=%s LIMIT 1", (session_id,))
        if cur.fetchone():
            raise HTTPException(409, "Demo race has official penalties and cannot be deleted")
        cur.execute("""SELECT 1 FROM driver_standings st JOIN demo_race_entries de ON de.driver_id=st.driver_id
            WHERE de.session_id=%s AND st.championship_id<>%s LIMIT 1""",
            (session_id, marker["championship_id"]))
        if cur.fetchone():
            raise HTTPException(409, "Demo race drivers are referenced by another championship's standings")
        cur.execute("SELECT 1 FROM race_sessions WHERE event_id=%s AND id<>%s LIMIT 1", (marker["event_id"],session_id))
        if cur.fetchone():
            raise HTTPException(409, "Demo race event is referenced by another session")
        cur.execute("SELECT 1 FROM pit_reservations p JOIN pit_boxes b ON b.id=p.pit_box_id WHERE b.event_id=%s AND p.session_id<>%s LIMIT 1", (marker["event_id"],session_id))
        if cur.fetchone():
            raise HTTPException(409, "Demo race event has reservations for another session")
        cur.execute("""SELECT 1 FROM demo_race_entries de WHERE de.session_id=%s AND (
            EXISTS (SELECT 1 FROM session_results sr WHERE sr.driver_id=de.driver_id AND sr.session_id<>%s) OR
            EXISTS (SELECT 1 FROM incident_reports ir WHERE ir.driver_id=de.driver_id AND ir.session_id<>%s) OR
            EXISTS (SELECT 1 FROM demo_race_entries other WHERE other.driver_id=de.driver_id AND other.session_id<>%s)) LIMIT 1""", (session_id,session_id,session_id,session_id))
        if cur.fetchone():
            raise HTTPException(409, "Demo race drivers are referenced by another session")
        cur.execute("""SELECT 1 FROM demo_race_entries de JOIN drivers d ON d.id=de.driver_id
            LEFT JOIN team_memberships tm ON tm.driver_id=d.id
            LEFT JOIN teams t ON t.principal_user_id=d.user_id
            WHERE de.session_id=%s GROUP BY de.driver_id
            HAVING count(DISTINCT tm.id)<>1 OR count(DISTINCT t.id)>0 LIMIT 1""", (session_id,))
        # Keep generated drivers that gained additional team or principal references.
        if cur.fetchone():
            raise HTTPException(409, "Demo race drivers have additional team references")
        if sim:
            sim.status = "stopped"
            if sim.task and not sim.task.done():
                sim.task.cancel()
                await asyncio.gather(sim.task, return_exceptions=True)
        cur.execute("SELECT driver_id FROM demo_race_entries WHERE session_id=%s", (session_id,))
        driver_ids = [row["driver_id"] for row in cur.fetchall()]
        cur.execute("SELECT d.user_id FROM demo_race_entries de JOIN drivers d ON d.id=de.driver_id WHERE de.session_id=%s AND d.user_id IS NOT NULL", (session_id,))
        user_ids = [row["user_id"] for row in cur.fetchall()]
        cur.execute("DELETE FROM pit_reservations WHERE session_id=%s", (session_id,))
        cur.execute("DELETE FROM pit_boxes WHERE event_id=%s", (marker["event_id"],))
        cur.execute("DELETE FROM incident_reports WHERE session_id=%s", (session_id,))
        cur.execute("DELETE FROM session_results WHERE session_id=%s", (session_id,))
        # Generated drivers are unique to this race. Rebuild this championship's
        # derived standings after removing the race results so stale rows for those
        # drivers disappear and the remaining ranks stay correct.
        cur.execute("SELECT recalculate_standings(%s)", (marker["championship_id"],))
        cur.execute("DELETE FROM demo_race_entries WHERE session_id=%s", (session_id,))
        cur.execute("DELETE FROM demo_races WHERE session_id=%s", (session_id,))
        cur.execute("DELETE FROM race_sessions WHERE id=%s", (session_id,))
        cur.execute("DELETE FROM race_events WHERE id=%s", (marker["event_id"],))
        if driver_ids:
            cur.execute("DELETE FROM team_memberships WHERE driver_id=ANY(%s)", (driver_ids,))
            cur.execute("DELETE FROM drivers WHERE id=ANY(%s)", (driver_ids,))
        if user_ids:
            cur.execute("DELETE FROM users WHERE id=ANY(%s)", (user_ids,))
    if sim:
        simulations.pop(str(session_id), None)
    col.delete_many({"session_id":str(session_id)})
    return None


class EventBus:
    def __init__(self):
        self.clients: dict[str,set[tuple[asyncio.AbstractEventLoop,asyncio.Queue]]]={}
        self.lock=threading.RLock()
    def subscribe(self,sid):
        q=asyncio.Queue(maxsize=50); loop=asyncio.get_running_loop()
        with self.lock: self.clients.setdefault(str(sid),set()).add((loop,q))
        return q
    def unsubscribe(self,sid,q):
        with self.lock:
            clients=self.clients.get(str(sid),set())
            clients.difference_update(item for item in list(clients) if item[1] is q)
    @staticmethod
    def _enqueue(q,event):
        if q.full():
            try: q.get_nowait()
            except asyncio.QueueEmpty: pass
        try: q.put_nowait(event)
        except asyncio.QueueFull: pass
    def send(self,sid,event):
        try: current=asyncio.get_running_loop()
        except RuntimeError: current=None
        with self.lock: subscribers=list(self.clients.get(str(sid),set()))
        for loop,q in subscribers:
            if loop is current: self._enqueue(q,event)
            else: loop.call_soon_threadsafe(self._enqueue,q,event)

bus=EventBus()


simulations: dict[str, Simulation] = {}


def sync_simulation_lifecycle(session_id: UUID, action: str):
    sim=simulations.get(str(session_id))
    if not sim:
        return
    if action == "pause" and sim.status == "running":
        sim.status="paused"
    elif action == "resume" and sim.status == "paused":
        sim.status="running"
    elif action in {"finish", "reset"}:
        sim.status="stopped"
        if sim.task and not sim.task.done():
            sim.task.get_loop().call_soon_threadsafe(sim.task.cancel)
        if action == "reset":
            sim.lap_by_driver={str(driver["id"]):1 for driver in sim.drivers}
            sim.sector_by_driver.clear()
            sim.race_clock_ms=0
            sim.next_sector_due_by_driver.clear()
            sim.last_lap_by_driver.clear()
            sim.elapsed_by_driver={str(driver["id"]):0 for driver in sim.drivers}
            sim.sector_splits_by_driver.clear()
            sim.tire_age_by_driver={str(driver["id"]):0 for driver in sim.drivers}
            sim.tire_wear_by_driver={str(driver["id"]):0.0 for driver in sim.drivers}
            sim.compound_by_driver.clear()
            sim.pit_reservations_by_driver.clear()
            sim.pit_due_tire_age_by_driver.clear()


def ensure_session_reset_allowed(session_id: UUID | str):
    row = fetch_one("""SELECT EXISTS(SELECT 1 FROM incident_reports i JOIN penalties p ON p.incident_id=i.id
        WHERE i.session_id=s.id) AS has_penalties FROM race_sessions s WHERE s.id=%s""", (session_id,))
    if not row:
        raise HTTPException(404, "Session not found")
    if row["has_penalties"]:
        raise HTTPException(409, "A session with official penalties cannot be reset")


def clear_session_measurements(session_id: UUID | str):
    """Clear stored measurements after an explicit reset, preserving penalty history."""
    col = mongo_ready()
    cancelled = []
    with connection() as conn, conn.cursor() as cur:
        cur.execute("""SELECT e.championship_id,
            EXISTS(SELECT 1 FROM incident_reports i JOIN penalties p ON p.incident_id=i.id WHERE i.session_id=s.id) AS has_penalties
            FROM race_sessions s JOIN race_events e ON e.id=s.event_id WHERE s.id=%s""", (session_id,))
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
        cur.execute("""UPDATE pit_reservations SET status='CANCELLED'
            WHERE session_id=%s AND allocation_source='AUTOMATIC' AND status='RESERVED' RETURNING id""", (session_id,))
        cancelled_ids = [item["id"] for item in cur.fetchall()]
        if cancelled_ids:
            cur.execute(PIT_RESERVATION_SELECT + " WHERE r.id=ANY(%s)", (cancelled_ids,))
            cancelled = cur.fetchall()
        cur.execute("DELETE FROM pit_reservations WHERE session_id=%s AND allocation_source='AUTOMATIC'", (session_id,))
    for reservation in cancelled:
        publish(session_id, "pit.update", reservation)


def advance_simulation_tick(sim: Simulation, timestamp: datetime, rng=None, safety_car: bool = False,
                            pit_driver_ids: set[str] | None = None,
                            pit_assignments: dict[str, dict[str, Any]] | None = None):
    """Advance every car by one sector and return internally consistent packets and timing."""
    rng = rng or random
    pit_driver_ids = pit_driver_ids or set()
    pit_assignments = pit_assignments or {}
    compounds = ("SOFT", "MEDIUM", "HARD")
    current: list[dict[str, Any]] = []
    race_clock = sim.race_clock_ms
    for driver in sim.drivers:
        driver_id = str(driver["id"])
        previous_sector = sim.sector_by_driver.get(driver_id, 0)
        lap = sim.lap_by_driver.get(driver_id, 1)
        lap_limit = min(sim.total_laps or MAX_SESSION_LAPS, MAX_SESSION_LAPS)
        frozen = previous_sector == 3 and lap >= lap_limit
        due = sim.next_sector_due_by_driver.get(driver_id, 0)
        advancing = not frozen and race_clock >= due
        if previous_sector == 3 and advancing:
            lap += 1
            sim.sector_splits_by_driver[driver_id] = []
        sector = 3 if frozen else previous_sector % 3 + 1 if advancing else previous_sector
        sim.lap_by_driver[driver_id] = lap
        sim.sector_by_driver[driver_id] = sector

        number = int(driver.get("number") or 1)
        pace_offset = sim.pace_offsets_ms.get(driver_id, (number % 7 - 3) * 95)
        assignment = pit_assignments.get(driver_id)
        in_pit = (driver_id in pit_driver_ids) or bool(assignment and assignment["starts_at"] <= timestamp < assignment["ends_at"])
        sector_ms, throttle, brake, speed = calculate_sector_performance(
            sector, pace_offset, safety_car, in_pit, rng
        )

        splits = sim.sector_splits_by_driver.setdefault(driver_id, [])
        if advancing:
            splits.append(sector_ms)
            sim.elapsed_by_driver[driver_id] = sim.elapsed_by_driver.get(driver_id, 0) + sector_ms
            sim.next_sector_due_by_driver[driver_id] = due + sector_ms
        tire_age = sim.tire_age_by_driver.setdefault(driver_id, 0)
        wear = sim.tire_wear_by_driver.setdefault(driver_id, 0.0)
        if sector == 3 and advancing:
            tire_age += 1
            wear = min(100.0, wear + (0.65 if safety_car else 0.9 if in_pit else 1.1))
            sim.tire_age_by_driver[driver_id] = tire_age
            sim.tire_wear_by_driver[driver_id] = wear

        compound = sim.compound_by_driver.setdefault(driver_id, compounds[number % len(compounds)])
        lap_time_ms = sum(splits) if sector == 3 and advancing else None
        if lap_time_ms is not None:
            sim.last_lap_by_driver[driver_id] = lap_time_ms
        current.append({
            "session_id": str(sim.session_id), "driver_id": driver_id,
            "ts": timestamp, "lap": lap, "sector": sector,
            "elapsed_ms": sim.elapsed_by_driver[driver_id],
            "lap_time_ms": lap_time_ms,
            "last_lap_ms": sim.last_lap_by_driver.get(driver_id),
            "sector_ms": list(splits), "speed_kph": speed,
            "throttle_pct": round(throttle, 1), "brake_pct": round(brake, 1),
            "tire_compound": compound, "tire_age_laps": tire_age,
            "tire_wear_pct": round(wear, 1),
            "tire_temp_c": [round(70 + speed * 0.09 + wear * 0.12 + rng.uniform(-2, 2), 1) for _ in range(4)],
            "pit_state": "IN_PIT" if in_pit else "PIT_SCHEDULED" if assignment else "TRACK",
            "pit_reservation_id": str(assignment["id"]) if assignment and assignment.get("id") else None,
            "pit_box_number": assignment.get("box_number") if assignment else None,
            "pit_team_id": str(assignment["team_id"]) if assignment and assignment.get("team_id") else None,
            "pit_starts_at": assignment.get("starts_at") if assignment else None,
            "pit_ends_at": assignment.get("ends_at") if assignment else None,
        })

    ordered = sorted(current, key=lambda packet: (-packet["lap"], -packet["sector"], packet["elapsed_ms"]))
    positions = {packet["driver_id"]: position for position, packet in enumerate(ordered, start=1)}
    for packet in current:
        packet["position"] = positions[packet["driver_id"]]
    timing = [{key: packet[key] for key in ("driver_id", "position", "lap", "sector", "elapsed_ms", "lap_time_ms", "last_lap_ms", "sector_ms", "pit_state", "pit_reservation_id", "pit_box_number", "pit_team_id")}
              for packet in ordered]
    sim.race_clock_ms += 15_000
    return current, {"cars": timing, "safety_car": safety_car}


def refresh_simulation_pit_state(sim: Simulation, timestamp: datetime):
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute("""UPDATE pit_reservations SET status='COMPLETED'
            WHERE session_id=%s AND status='RESERVED' AND ends_at<=%s RETURNING id""", (sim.session_id, timestamp))
        expired_ids = [row["id"] for row in cur.fetchall()]
        if expired_ids:
            cur.execute(PIT_RESERVATION_SELECT + " WHERE r.id=ANY(%s)", (expired_ids,))
            expired = cur.fetchall()
        else:
            expired = []
        cur.execute(PIT_RESERVATION_SELECT + """ WHERE r.session_id=%s AND r.driver_id IS NOT NULL
            AND r.status='RESERVED' AND r.ends_at>%s ORDER BY r.starts_at""", (sim.session_id, timestamp))
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
                sim.compound_by_driver[key], int(car.get("number") or 1))
    sim.pit_reservations_by_driver = {str(row["driver_id"]): row for row in active}
    return sim.pit_reservations_by_driver


def schedule_simulation_pit_stops(sim: Simulation, packets: list[dict[str, Any]]):
    completion_lap = min(sim.total_laps or MAX_SESSION_LAPS, MAX_SESSION_LAPS)
    for packet in packets:
        driver_id = str(packet["driver_id"])
        driver = next((row for row in sim.drivers if str(row["id"]) == driver_id), None)
        number = int((driver or {}).get("number") or 1)
        compound = sim.compound_by_driver.setdefault(driver_id, ("SOFT", "MEDIUM", "HARD")[number % 3])
        target_age = sim.pit_due_tire_age_by_driver.setdefault(driver_id, tire_stint_target(compound, number))
        if (packet["sector"] != 3 or packet["lap"] >= completion_lap
                or packet["tire_age_laps"] < target_age
                or driver_id in sim.pit_reservations_by_driver):
            continue
        if not driver or not driver.get("team_id"):
            sim.pit_due_tire_age_by_driver[driver_id] = MAX_SESSION_LAPS + 1
            continue
        duration = timedelta(seconds=max(0.6, 3.0 / max(sim.rate_hz, 0.2)))
        try:
            reservation = create_automatic_reservation(sim.session_id, driver["team_id"], driver["id"], duration)
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
    descriptions = {7: "Track limits observed at corner exit", 23: "Minor wheel-to-wheel contact under review", 41: "Unsafe rejoin reported by race control"}
    for lap, description in descriptions.items():
        if lap >= (sim.total_laps or MAX_SESSION_LAPS) or lap in sim.incident_laps_recorded:
            continue
        finished = [packet for packet in packets if packet["lap"] == lap and packet["sector"] == 3 and packet["lap_time_ms"]]
        if not finished:
            continue
        packet = finished[0]
        with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""INSERT INTO incident_reports(session_id,driver_id,lap,description)
                VALUES (%s,%s,%s,%s) RETURNING *""", (sim.session_id, packet["driver_id"], lap, description))
            row = cur.fetchone()
        sim.incident_laps_recorded.add(lap)
        publish(sim.session_id, "incident.update", row)


def cancel_automatic_pit_reservations(session_id: UUID | str):
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute("""UPDATE pit_reservations SET status='CANCELLED'
            WHERE session_id=%s AND allocation_source='AUTOMATIC' AND status='RESERVED' RETURNING id""", (session_id,))
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
            session = fetch_one("""SELECT s.state,s.safety_car,e.championship_id
                FROM race_sessions s JOIN race_events e ON e.id=s.event_id WHERE s.id=%s""", (sim.session_id,))
            if not session:
                sim.status = "error"
                return
            if session["state"] == "PAUSED":
                sim.status = "paused"
                continue
            if session["state"] != "ACTIVE":
                sim.status = "stopped"
                return
            timestamp = datetime.now(timezone.utc)
            pit_assignments = refresh_simulation_pit_state(sim, timestamp)
            packets, timing = advance_simulation_tick(sim, timestamp, safety_car=session["safety_car"], pit_assignments=pit_assignments)
            for packet in packets:
                inserted = col.insert_one(dict(packet))
                publish(sim.session_id, "telemetry.sample", telemetry_ws_payload(packet, inserted.inserted_id))
            publish(sim.session_id, "timing.update", timing)
            schedule_simulation_pit_stops(sim, packets)
            record_simulated_incidents(sim, packets)
            completion_lap = min(sim.total_laps or MAX_SESSION_LAPS, MAX_SESSION_LAPS)
            if all(packet["lap"] == completion_lap and packet["sector"] == 3 for packet in packets):
                ordered = sorted(packets, key=lambda packet: packet["elapsed_ms"])
                best_laps = {row["_id"]: row["best_lap_ms"] for row in col.aggregate([
                    {"$match": {"session_id": str(sim.session_id), "lap_time_ms": {"$gt": 0}}},
                    {"$group": {"_id": "$driver_id", "best_lap_ms": {"$min": "$lap_time_ms"}}},
                ])}
                fastest_driver_id = min(best_laps, key=best_laps.get) if best_laps else None
                pole_driver_id = (min(sim.pace_offsets_ms, key=sim.pace_offsets_ms.get)
                                  if sim.is_generated and sim.pace_offsets_ms else None)
                rows = []
                with connection() as conn, conn.cursor() as cur:
                    for position, packet in enumerate(ordered, start=1):
                        driver_id = packet["driver_id"]
                        best_lap_ms = best_laps.get(driver_id, packet["last_lap_ms"])
                        pole = driver_id == pole_driver_id
                        fastest_lap = driver_id == fastest_driver_id
                        cur.execute("INSERT INTO session_results(session_id,driver_id,position,lap_time_ms,pole,fastest_lap,classified) VALUES (%s,%s,%s,%s,%s,%s,TRUE) ON CONFLICT(session_id,driver_id) DO UPDATE SET position=excluded.position,lap_time_ms=excluded.lap_time_ms,pole=excluded.pole,fastest_lap=excluded.fastest_lap,classified=TRUE", (sim.session_id,driver_id,position,best_lap_ms,pole,fastest_lap))
                        rows.append({"driver_id":driver_id,"position":position,"lap_time_ms":best_lap_ms,"pole":pole,"fastest_lap":fastest_lap,"classified":True})
                    cur.execute("UPDATE race_sessions SET state='COMPLETED',ended_at=%s WHERE id=%s AND state='ACTIVE' RETURNING *", (datetime.now(timezone.utc),sim.session_id))
                    completed = cur.fetchone()
                    if completed:
                        cur.execute("SELECT recalculate_standings(%s)", (session["championship_id"],))
                sim.status = "stopped"
                publish(sim.session_id,"timing.update",rows)
                if completed:
                    publish(sim.session_id,"session.state",completed)
                sim.runs_completed += 1
                cancel_automatic_pit_reservations(sim.session_id)
                if not sim.auto_repeat or not completed:
                    return
                await asyncio.sleep(5)
                race = await asyncio.to_thread(_make_demo_race, None, True)
                launch_demo_simulation(race["session_id"])
                simulations.pop(str(sim.session_id), None)
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


@app.post("/api/sessions/{session_id}/simulate")
async def control_simulation(session_id: UUID, body: SimulationControl, user=Depends(roles("ADMIN", "STEWARD"))):
    if mongo_ready() is None:
        raise HTTPException(503, "MongoDB telemetry store is unavailable")
    sim = simulations.get(str(session_id))
    if body.action == "start":
        if sim and sim.status in {"running", "paused"}:
            raise HTTPException(409, "Simulation is already running")
        session = fetch_one("SELECT state,total_laps,scheduled_at FROM race_sessions WHERE id=%s", (session_id,))
        if not session: raise HTTPException(404, "Session not found")
        if session["state"] != "ACTIVE": raise HTTPException(409, "Session must be active before simulation starts")
        if sim and sim.status == "stopped":
            if sim.task and not sim.task.done():
                sim.task.cancel()
                await asyncio.gather(sim.task, return_exceptions=True)
            clear_session_measurements(session_id)
        generated_entries = fetch_all("""SELECT d.id,d.number,de.pace_offset_ms,tm.team_id,t.name AS team_name
            FROM demo_race_entries de JOIN drivers d ON d.id=de.driver_id
            JOIN team_memberships tm ON tm.driver_id=d.id
              AND tm.start_date<=%s::date AND (tm.end_date IS NULL OR tm.end_date>=%s::date)
            JOIN teams t ON t.id=tm.team_id WHERE de.session_id=%s ORDER BY d.number""",
            (session["scheduled_at"], session["scheduled_at"], session_id))
        drivers = generated_entries or fetch_all("""SELECT d.id,d.number,tm.team_id,t.name AS team_name
            FROM drivers d JOIN team_memberships tm ON tm.driver_id=d.id
              AND tm.start_date<=%s::date AND (tm.end_date IS NULL OR tm.end_date>=%s::date)
            JOIN teams t ON t.id=tm.team_id WHERE d.eligibility='ACTIVE' ORDER BY d.number LIMIT %s""",
            (session["scheduled_at"], session["scheduled_at"], body.cars or 10))
        if not drivers: raise HTTPException(409, "No eligible drivers are available")
        if body.cars and len(drivers) < body.cars: raise HTTPException(422, "Requested car count exceeds eligible drivers")
        sim = Simulation(session_id, drivers, body.rate_hz or 2.0, total_laps=session["total_laps"] or MAX_SESSION_LAPS)
        sim.pace_offsets_ms = {str(d["id"]):d["pace_offset_ms"] for d in generated_entries}
        sim.is_generated = bool(generated_entries)
        marker = fetch_one("SELECT auto_repeat FROM demo_races WHERE session_id=%s", (session_id,))
        sim.auto_repeat = bool(marker and marker["auto_repeat"])
        sim.lap_by_driver = {str(d["id"]): 1 for d in drivers}
        if sim.is_generated:
            restore_simulated_incidents(sim)
        simulations[str(session_id)] = sim
        sim.task = asyncio.create_task(simulation_loop(sim))
        sim.status = "running"
    elif body.action == "pause":
        if not sim or sim.status != "running": raise HTTPException(409, "Simulation is not running")
        sim.status = "paused"
    elif body.action == "resume":
        if not sim or sim.status != "paused": raise HTTPException(409, "Simulation is not paused")
        sim.status = "running"
    elif body.action == "stop":
        if not sim: raise HTTPException(409, "Simulation has not started")
        sim.status = "stopped"
        if sim.task and not sim.task.done():
            sim.task.cancel()
            await asyncio.gather(sim.task, return_exceptions=True)
        cancel_automatic_pit_reservations(session_id)
        sim.pit_reservations_by_driver.clear()
    elif body.action == "reset":
        session = fetch_one("SELECT state FROM race_sessions WHERE id=%s", (session_id,))
        if not session: raise HTTPException(404, "Session not found")
        if session["state"] != "PAUSED":
            raise HTTPException(409, "Pause the session before resetting its simulation")
        ensure_session_reset_allowed(session_id)
        if sim:
            sync_simulation_lifecycle(session_id,"reset")
            if sim.task and not sim.task.done():
                await asyncio.gather(sim.task, return_exceptions=True)
        clear_session_measurements(session_id)
        if not sim:
            sim = Simulation(session_id, [], body.rate_hz or 2.0)
            simulations[str(session_id)] = sim
    return {"session_id": str(session_id), "state": sim.status, "cars": len(sim.drivers), "rate_hz": sim.rate_hz}


async def _check_ws_runtime_lease(ws: WebSocket) -> bool:
    runtime_lease = getattr(ws.app.state, "runtime_lease", None)
    if runtime_lease is None:
        return True
    try:
        check_runtime_lease(runtime_lease)
    except RuntimeError:
        await ws.close(
            code=1011,
            reason=(
                "Runtime ownership was lost; restart the backend "
                "after PostgreSQL recovery."
            ),
        )
        return False
    return True


async def _wait_for_ws_event(
    ws: WebSocket, queue: asyncio.Queue[Any]
) -> dict[str, Any] | None:
    while True:
        try:
            return await asyncio.wait_for(queue.get(), timeout=0.5)
        except TimeoutError:
            if not await _check_ws_runtime_lease(ws):
                return None


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
        claims = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = (
            fetch_one("SELECT id FROM users WHERE id=%s", (claims.get("sub"),))
            if claims.get("sub")
            else None
        )
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


@app.get("/api/health")
def health():
    state={"postgres":"down","mongodb":"down"}
    try: fetch_one("SELECT 1 AS ok"); state["postgres"]="up"
    except Exception: pass
    try:
        if mongo_client: mongo_client.admin.command("ping"); state["mongodb"]="up"
    except Exception: pass
    return {"status":"ok" if all(v=="up" for v in state.values()) else "degraded","services":state}


def admin(user=Depends(roles("ADMIN"))): return user


@app.get("/api/dbms/schema")
def dbms_schema(user=Depends(admin)):
    return jsonable(fetch_all("SELECT table_name,column_name,data_type,is_nullable FROM information_schema.columns WHERE table_schema='public' ORDER BY table_name,ordinal_position"))


@app.get("/api/dbms/overview")
def dbms_overview(user=Depends(admin)):
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
    return jsonable({**counts, "telemetry_samples": telemetry_samples,
      "postgres": "up", "mongodb": mongo_status, "updated_at": datetime.now(timezone.utc)})


def public_dbms_tables():
    return [row["table_name"] for row in fetch_all("""SELECT table_name FROM information_schema.tables
      WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY table_name""")]


@app.get("/api/dbms/tables")
def dbms_tables(user=Depends(admin)):
    names = public_dbms_tables()
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        rows = []
        for name in names:
            cur.execute(sql.SQL("SELECT count(*) AS count FROM public.{}").format(sql.Identifier(name)))
            rows.append({"table_name": name, "row_count": cur.fetchone()["count"]})
    return jsonable({"tables": rows, "updated_at": datetime.now(timezone.utc)})


@app.get("/api/dbms/tables/{table_name}")
def dbms_table_rows(table_name: str, limit: int = Query(50, ge=1, le=100),
                    offset: int = Query(0, ge=0), user=Depends(admin)):
    if table_name not in public_dbms_tables():
        raise HTTPException(404, "Database table not found")
    columns = fetch_all("""SELECT column_name FROM information_schema.columns
      WHERE table_schema='public' AND table_name=%s ORDER BY ordinal_position""", (table_name,))
    visible_columns = [row["column_name"] for row in columns if row["column_name"] not in {"password_hash"}]
    primary_keys = fetch_all("""SELECT k.column_name FROM information_schema.table_constraints t
      JOIN information_schema.key_column_usage k ON k.constraint_name=t.constraint_name
        AND k.constraint_schema=t.constraint_schema AND k.table_name=t.table_name
      WHERE t.table_schema='public' AND t.table_name=%s AND t.constraint_type='PRIMARY KEY'
      ORDER BY k.ordinal_position""", (table_name,))
    order_columns = [row["column_name"] for row in primary_keys] or visible_columns[:1]
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql.SQL("SELECT {} FROM public.{} ORDER BY {} LIMIT %s OFFSET %s").format(
          sql.SQL(",").join(map(sql.Identifier, visible_columns)), sql.Identifier(table_name),
          sql.SQL(",").join(map(sql.Identifier, order_columns))), (limit, offset))
        rows = cur.fetchall()
        cur.execute(sql.SQL("SELECT count(*) AS count FROM public.{}").format(sql.Identifier(table_name)))
        count = cur.fetchone()["count"]
    return jsonable({"table_name": table_name, "columns": visible_columns,
      "rows": rows, "total": count, "limit": limit, "offset": offset,
      "updated_at": datetime.now(timezone.utc)})


@app.get("/api/dbms/races")
def dbms_races(user=Depends(admin)):
    return jsonable(fetch_all("""SELECT s.id,s.state,s.total_laps,s.started_at,s.ended_at,e.name AS event_name,c.name AS circuit_name
      FROM race_sessions s JOIN race_events e ON e.id=s.event_id JOIN circuits c ON c.id=e.circuit_id LEFT JOIN demo_races d ON d.session_id=s.id
      WHERE s.session_type='RACE' ORDER BY CASE WHEN s.state='ACTIVE' THEN 0 WHEN s.state='PAUSED' THEN 1 ELSE 2 END,COALESCE(d.auto_repeat,false) DESC,s.scheduled_at DESC"""))


@app.get("/api/dbms/races/{session_id}")
def dbms_race(session_id: UUID, include_laps: bool = True, user=Depends(admin)):
    session = fetch_one("""SELECT s.*,e.name AS event_name,c.name AS circuit_name FROM race_sessions s
      JOIN race_events e ON e.id=s.event_id JOIN circuits c ON c.id=e.circuit_id WHERE s.id=%s AND s.session_type='RACE'""", (session_id,))
    if not session:
        raise HTTPException(404, "Race not found")
    results = fetch_all("""SELECT r.*,u.full_name AS driver_name,d.number,d.licence_number FROM session_results r
      JOIN drivers d ON d.id=r.driver_id LEFT JOIN users u ON u.id=d.user_id WHERE r.session_id=%s ORDER BY r.position NULLS LAST""", (session_id,))
    incidents = fetch_all("""SELECT i.*,u.full_name AS driver_name FROM incident_reports i
      JOIN drivers d ON d.id=i.driver_id JOIN users u ON u.id=d.user_id
      WHERE i.session_id=%s ORDER BY i.lap,i.id""", (session_id,))
    penalties = fetch_all("SELECT p.* FROM penalties p JOIN incident_reports i ON i.id=p.incident_id WHERE i.session_id=%s", (session_id,))
    provisional = session["state"] == "COMPLETED" and any(
        (penalty.get("time_seconds") or 0) > 0 or (penalty.get("grid_places") or 0) > 0
        for penalty in penalties)
    for result in results:
        result["provisional"] = provisional
    reservations = fetch_all(PIT_RESERVATION_SELECT + " WHERE r.session_id=%s ORDER BY r.starts_at", (session_id,))
    col = mongo_ready()
    match = {"session_id": str(session_id)}
    # Full lap history is optional for the 1s live poll; it grows with every race lap.
    laps = race_lap_measurements(col, match) if include_laps else []
    driver_ids = col.distinct("driver_id", match)
    latest = [col.find_one({**match, "driver_id": driver_id}, sort=[("ts", DESCENDING)]) for driver_id in driver_ids]
    latest = sorted((row for row in latest if row), key=lambda row: (row.get("position") is None, row.get("position") or 0))
    ids = {row["driver_id"] for row in latest} | {str(row["driver_id"]) for row in results}
    drivers = fetch_all("SELECT d.id,d.number,d.licence_number,u.full_name AS driver_name FROM drivers d LEFT JOIN users u ON u.id=d.user_id WHERE d.id=ANY(%s::uuid[])", (list(ids),)) if ids else []
    if include_laps:
        lap_source = "historical_demo" if laps and all(x.get("source")=="historical_demo" for x in laps) else "recorded_telemetry"
    else:
        lap_source = "historical_demo" if col.find_one({**match, "sector":3, "lap_time_ms":{"$gt":0}, "source":"historical_demo"}, {"_id":1}) else "recorded_telemetry"
    completed_count = list(col.aggregate([
        {"$match": {**match, "sector": 3, "lap_time_ms": {"$gt": 0}}},
        {"$group": {"_id": {"driver_id": "$driver_id", "lap": "$lap"}}},
        {"$count": "count"},
    ]))
    return jsonable({"session": session, "results": results, "incidents": incidents, "penalties": penalties,
      "pit_reservations": reservations, "drivers": drivers, "laps": laps, "laps_included": include_laps,
      "completed_driver_laps": completed_count[0]["count"] if completed_count else 0, "latest": latest,
      "telemetry_count": col.count_documents(match), "updated_at": datetime.now(timezone.utc),
      "lap_source": lap_source})


def race_lap_measurements(col, match: dict[str, Any]):
    # Collapse retries to one complete lap per driver, retaining the latest stored measurement.
    return list(col.aggregate([{"$match": {**match, "sector": 3, "lap_time_ms": {"$gt": 0}}},
      {"$sort": {"ts": 1}}, {"$group": {"_id": {"driver_id": "$driver_id", "lap": "$lap"}, "record": {"$last": "$$ROOT"}}},
      {"$replaceRoot": {"newRoot": "$record"}}, {"$project": {"_id": 0}}, {"$sort": {"lap": 1, "position": 1}}]))


@app.get("/api/dbms/races/{session_id}/laps")
def dbms_race_laps(session_id: UUID, user=Depends(admin)):
    session = fetch_one("SELECT id FROM race_sessions WHERE id=%s AND session_type='RACE'", (session_id,))
    if not session:
        raise HTTPException(404, "Race not found")
    col = mongo_ready()
    match = {"session_id": str(session_id)}
    laps = race_lap_measurements(col, match)
    source = "historical_demo" if laps and all(x.get("source")=="historical_demo" for x in laps) else "recorded_telemetry"
    return jsonable({"session_id": session_id, "laps": laps, "lap_source": source})


@app.get("/api/sessions/{session_id}/laps")
def session_laps(session_id: UUID, user=Depends(current_user)):
    session = fetch_one("SELECT id FROM race_sessions WHERE id=%s", (session_id,))
    if not session:
        raise HTTPException(404, "Session not found")
    laps = race_lap_measurements(mongo_ready(), {"session_id": str(session_id)})
    incidents = fetch_all("""SELECT i.*,u.full_name AS driver_name FROM incident_reports i
        JOIN drivers d ON d.id=i.driver_id JOIN users u ON u.id=d.user_id
        WHERE i.session_id=%s ORDER BY i.lap,i.id""", (session_id,))
    stops = fetch_all(PIT_RESERVATION_SELECT + " WHERE r.session_id=%s ORDER BY r.starts_at", (session_id,))
    return jsonable({"session_id": session_id, "laps": laps, "incidents": incidents, "pit_reservations": stops})


@app.get("/api/dbms/eer")
def dbms_eer(user=Depends(admin)):
    columns = fetch_all("""SELECT c.table_name,c.column_name,c.data_type,EXISTS(SELECT 1 FROM information_schema.key_column_usage k
      JOIN information_schema.table_constraints t ON t.constraint_name=k.constraint_name AND t.constraint_schema=k.constraint_schema
      WHERE t.constraint_type='PRIMARY KEY' AND k.table_schema='public' AND k.table_name=c.table_name AND k.column_name=c.column_name) AS primary_key
      FROM information_schema.columns c WHERE c.table_schema='public' ORDER BY c.table_name,c.ordinal_position""")
    relationships = fetch_all("""SELECT DISTINCT child.relname AS child,ca.attname AS foreign_key,parent.relname AS parent,
      pa.attname AS parent_key,NOT ca.attnotnull AS optional,
      CASE WHEN EXISTS(SELECT 1 FROM pg_constraint uq WHERE uq.conrelid=f.conrelid AND uq.contype IN ('p','u') AND uq.conkey <@ f.conkey)
        THEN '0..1' ELSE '0..many' END AS children_per_parent
      FROM pg_constraint f JOIN pg_class child ON child.oid=f.conrelid JOIN pg_namespace ns ON ns.oid=child.relnamespace
      JOIN pg_class parent ON parent.oid=f.confrelid
      CROSS JOIN LATERAL unnest(f.conkey,f.confkey) AS pair(child_num,parent_num)
      JOIN pg_attribute ca ON ca.attrelid=f.conrelid AND ca.attnum=pair.child_num
      JOIN pg_attribute pa ON pa.attrelid=f.confrelid AND pa.attnum=pair.parent_num
      WHERE f.contype='f' AND ns.nspname='public' ORDER BY child.relname,ca.attname""")
    return {"columns": columns, "relationships": relationships}


@app.get("/api/dbms/indexes")
def dbms_indexes(user=Depends(admin)):
    return jsonable(fetch_all("SELECT tablename,indexname,indexdef FROM pg_indexes WHERE schemaname='public' ORDER BY tablename,indexname"))


@app.get("/api/dbms/explain")
def dbms_explain(query: Literal["leaderboard","licence"], user=Depends(admin)):
    sql={"leaderboard":"SELECT driver_id,lap_time_ms FROM session_results WHERE session_id=(SELECT id FROM race_sessions WHERE session_type='RACE' ORDER BY scheduled_at LIMIT 1) AND lap_time_ms IS NOT NULL ORDER BY session_id,lap_time_ms LIMIT 20","licence":"SELECT id,licence_number FROM drivers WHERE licence_number='APX-DEMO'"}[query]
    with connection() as conn,conn.cursor(row_factory=tuple_row) as cur: cur.execute("EXPLAIN (FORMAT JSON) "+sql); plan=cur.fetchone()[0]
    return {"query":query,"plan":plan}


@app.post("/api/dbms/constraint-demo")
def constraint_demo(user=Depends(admin)):
    with connection() as conn,conn.cursor(row_factory=tuple_row) as cur:
        cur.execute("SAVEPOINT constraint_demo")
        try:
            cur.execute("INSERT INTO drivers(licence_number,number,eligibility) VALUES ('APX-DEMO-CONSTRAINT',-1,'ACTIVE')")
            result={"constraint":"unexpectedly accepted"}
            cur.execute("ROLLBACK TO SAVEPOINT constraint_demo")
        except CheckViolation as exc:
            constraint = getattr(exc.diag, "constraint_name", None)
            cur.execute("ROLLBACK TO SAVEPOINT constraint_demo")
            if constraint != "drivers_number_check":
                raise HTTPException(500, "Invalid driver row failed an unexpected check constraint") from exc
            result={"constraint":constraint,"rejected":True,"sqlstate":exc.sqlstate}
        cur.execute("RELEASE SAVEPOINT constraint_demo")
    if result.get("constraint") == "unexpectedly accepted":
        raise HTTPException(500, "Database accepted a driver number outside the allowed range")
    return result


@app.get("/api/dbms/locks")
def dbms_locks(user=Depends(admin)):
    return jsonable(fetch_all("SELECT locktype,mode,granted,relation::regclass::text AS relation,pid FROM pg_locks WHERE database=(SELECT oid FROM pg_database WHERE datname=current_database()) ORDER BY granted,mode"))


@app.get("/api/dbms/telemetry")
def dbms_telemetry(user=Depends(admin)):
    try:
        col=mongo_ready(); return {"store":"MongoDB","count":col.count_documents({}),"indexes":list(col.index_information().keys()),"sample":jsonable(list(col.find({}, {"_id":0}).sort("ts",DESCENDING).limit(3)))}
    except HTTPException: raise
    except Exception as exc: raise HTTPException(503,"Could not inspect MongoDB telemetry") from exc


def mongo_database_ready():
    if mongo_client is None:
        raise HTTPException(503, "MongoDB document store is unavailable")
    return mongo_client[MONGODB_DATABASE]


@app.get("/api/dbms/mongo/collections")
def dbms_mongo_collections(user=Depends(admin)):
    """List application collections with their actual document and index metadata."""
    try:
        database = mongo_database_ready()
        collections = []
        for name in sorted(name for name in database.list_collection_names() if not name.startswith("system.")):
            collection = database[name]
            indexes = collection.index_information()
            collections.append({
                "name": name,
                "document_count": collection.count_documents({}),
                "indexes": [{"name": index_name, **index} for index_name, index in indexes.items()],
            })
        return {"store": "MongoDB", "database": MONGODB_DATABASE, "collections": collections,
                "updated_at": datetime.now(timezone.utc)}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(503, "Could not inspect MongoDB collections") from exc


@app.get("/api/dbms/mongo/collections/{collection_name}")
def dbms_mongo_collection_documents(
    collection_name: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session_id: str | None = Query(None, max_length=64),
    driver_id: str | None = Query(None, max_length=64),
    lap: int | None = Query(None, ge=1),
    sector: int | None = Query(None, ge=1, le=3),
    user=Depends(admin),
):
    """Browse one real Mongo collection without permitting arbitrary collection names or query syntax."""
    try:
        database = mongo_database_ready()
        if collection_name.startswith("system.") or collection_name not in database.list_collection_names():
            raise HTTPException(404, "MongoDB collection not found")
        filters = {key: value for key, value in {
            "session_id": session_id, "driver_id": driver_id, "lap": lap, "sector": sector,
        }.items() if value is not None}
        collection = database[collection_name]
        total = collection.count_documents(filters)
        cursor = collection.find(filters).sort("ts", DESCENDING).skip(offset).limit(limit)
        documents = [{**jsonable({key: value for key, value in document.items() if key != "_id"}),
                       "id": str(document["_id"])} for document in cursor]
        return jsonable({"collection": collection_name, "filters": filters, "documents": documents,
                         "total": total, "limit": limit, "offset": offset,
                         "updated_at": datetime.now(timezone.utc)})
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(503, "Could not read MongoDB collection") from exc


@app.get("/api/dbms/polyglot")
def dbms_polyglot(user=Depends(admin)):
    sql="""SELECT s.id AS session_id,s.state,d.id AS driver_id,u.full_name
      FROM race_sessions s JOIN (
        SELECT session_id,driver_id FROM session_results
        UNION SELECT session_id,driver_id FROM demo_race_entries
      ) entry ON entry.session_id=s.id
      JOIN drivers d ON d.id=entry.driver_id JOIN users u ON u.id=d.user_id
      ORDER BY s.scheduled_at DESC LIMIT 50"""
    rows=jsonable(fetch_all(sql)); col=mongo_ready(); grouped={}
    recent_cutoff=datetime.now(timezone.utc)-timedelta(days=30)
    pipeline=[{"$match":{"ts":{"$gte":recent_cutoff}}},{"$sort":{"ts":-1}},{"$limit":5000},{"$group":{"_id":{"session_id":"$session_id","driver_id":"$driver_id"},"samples":{"$sum":1},"latest":{"$max":"$ts"}}}]
    for doc in col.aggregate(pipeline): grouped[(doc["_id"]["session_id"],doc["_id"]["driver_id"])]=doc
    return {"relational_rows":len(rows),"rows":[{**r,"telemetry":grouped.get((str(r["session_id"]),str(r["driver_id"])),{"samples":0})} for r in rows]}


lock_demo_guard = threading.Lock()


@app.post("/api/dbms/lock-demo")
def dbms_lock_demo(user=Depends(admin)):
    """Demonstrate two real transactions contending on a pit box row."""
    if not lock_demo_guard.acquire(blocking=False):
        raise HTTPException(409, "A lock demonstration is already running")
    first_reservation_id = None
    second_reservation_id = None
    future = None
    worker = None
    outcome = None
    try:
        target = fetch_one("SELECT b.id AS pit_box_id,s.id AS session_id,t.id AS team_id FROM pit_boxes b JOIN race_sessions s ON s.event_id=b.event_id CROSS JOIN teams t ORDER BY b.number,s.scheduled_at LIMIT 1")
        if not target:
            raise HTTPException(503, "Seeded pit box, session, or team is unavailable")
        starts_at = datetime.now(timezone.utc) + timedelta(days=3650 + random.randrange(10000), seconds=random.randrange(86400))
        ends_at = starts_at + timedelta(minutes=2)
        ready = threading.Event()
        competitor = {"pid": None}
        worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="apexgrid-lock-demo")

        def competing_reservation():
            with connection() as conn:
                with conn.transaction():
                    conn.execute("SET LOCAL lock_timeout='8s'")
                    pid = conn.execute("SELECT pg_backend_pid() AS pid").fetchone()["pid"]
                    competitor["pid"] = pid
                    ready.set()
                    started = time.perf_counter()
                    try:
                        row = conn.execute("SELECT reserve_pit_box(%s,%s,%s,%s,%s) AS id", (target["pit_box_id"],target["session_id"],target["team_id"],starts_at,ends_at)).fetchone()
                        return {"outcome":"reserved","reservation_id":row["id"],"sqlstate":None,"wait_ms":round((time.perf_counter()-started)*1000,2),"pid":pid}
                    except ExclusionViolation as exc:
                        return {"outcome":"rejected","reservation_id":None,"sqlstate":exc.sqlstate,"wait_ms":round((time.perf_counter()-started)*1000,2),"pid":pid}
                    except Exception as exc:
                        return {"outcome":"error","reservation_id":None,"sqlstate":getattr(exc,"sqlstate",None),"wait_ms":round((time.perf_counter()-started)*1000,2),"pid":pid,"error":type(exc).__name__}

        wait_observed = False
        with connection() as owner:
            with owner.transaction():
                owner.execute("SET LOCAL lock_timeout='8s'")
                first_reservation_id = owner.execute("SELECT reserve_pit_box(%s,%s,%s,%s,%s) AS id", (target["pit_box_id"],target["session_id"],target["team_id"],starts_at,ends_at)).fetchone()["id"]
                future = worker.submit(competing_reservation)
                if not ready.wait(timeout=2):
                    raise HTTPException(503, "Second database connection did not become ready")
                # The worker publishes its backend PID just before it issues the blocking function.
                # Observe the database wait itself before committing the first reservation.
                deadline = time.monotonic() + 3
                while time.monotonic() < deadline:
                    lock_row = owner.execute("SELECT wait_event_type FROM pg_stat_activity WHERE pid=%s", (competitor["pid"],)).fetchone()
                    if lock_row and lock_row["wait_event_type"] == "Lock":
                        wait_observed = True
                        break
                    time.sleep(0.025)
        try:
            outcome = future.result(timeout=9) if future else None
        except FutureTimeout as exc:
            raise HTTPException(504, "Competing reservation did not finish before timeout") from exc
        second_reservation_id = outcome.get("reservation_id") if outcome else None
        if not outcome or outcome["outcome"] != "rejected" or outcome["sqlstate"] != "23P01":
            raise HTTPException(500, "Overlapping reservation was not rejected as expected")
        if not wait_observed:
            raise HTTPException(503, "Database did not report the competitor waiting on the pit box lock")
        return {
            "pit_box_id":str(target["pit_box_id"]),
            "lock_wait_observed":True,
            "lock_wait_ms":outcome["wait_ms"],
            "first_reservation":"committed",
            "overlapping_reservation":"rejected",
            "rejection_sqlstate":outcome["sqlstate"],
        }
    finally:
        try:
            if worker:
                worker.shutdown(wait=True, cancel_futures=True)
            if future and future.done() and outcome is None:
                try:
                    outcome = future.result()
                except Exception:
                    pass
            if outcome:
                second_reservation_id = outcome.get("reservation_id")
            reservation_ids=[rid for rid in (first_reservation_id,second_reservation_id) if rid]
            if reservation_ids:
                with connection() as conn:
                    conn.execute("DELETE FROM pit_reservations WHERE id=ANY(%s)", (reservation_ids,))
        finally:
            lock_demo_guard.release()


@app.post("/api/dbms/transaction-demo")
def transaction_demo(user=Depends(admin)):
    with connection() as conn,conn.cursor(row_factory=tuple_row) as cur:
        cur.execute("SELECT txid_current()")
        txid=cur.fetchone()[0]
        cur.execute("CREATE TEMP TABLE IF NOT EXISTS transaction_demo_probe(value integer) ON COMMIT DROP")
        cur.execute("TRUNCATE transaction_demo_probe")
        cur.execute("INSERT INTO transaction_demo_probe VALUES (1)")
        cur.execute("SELECT count(*) FROM transaction_demo_probe")
        before=cur.fetchone()[0]
        cur.execute("SAVEPOINT tx_demo")
        cur.execute("INSERT INTO transaction_demo_probe VALUES (2)")
        cur.execute("SELECT count(*) FROM transaction_demo_probe")
        during=cur.fetchone()[0]
        cur.execute("ROLLBACK TO SAVEPOINT tx_demo")
        cur.execute("SELECT count(*) FROM transaction_demo_probe")
        after=cur.fetchone()[0]
    return {"transaction_id":txid,"before":before,"during":during,"after_rollback":after,"savepoint_rolled_back":during==2 and after==before,"committed_effects":0}


@app.post("/api/dbms/recalculate")
def dbms_recalculate(championship_id: UUID, user=Depends(admin)):
    return recalculate(championship_id,user)
