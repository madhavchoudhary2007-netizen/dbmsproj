from __future__ import annotations

import asyncio
import importlib
import logging
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Annotated, Any, cast
from uuid import UUID

from fastapi import Depends, HTTPException, Request, WebSocket
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pymongo.collection import Collection
from pymongo.database import Database

from .. import token_revocation
from ..api.crud import create_crud_router
from ..api.laps import admin
from ..auth_cookie import verify_csrf_token
from ..config import CORS_ORIGINS, JWT_ALGORITHM, JWT_SECRET, MONGODB_DATABASE
from ..core.auth_dependencies import check_allowed_origin, create_role_check, token_is_revoked
from ..core.http_auth import authenticate_http_user
from ..core.serialization import jsonable
from ..core.websocket_runtime import check_ws_runtime_lease as _check_ws_runtime_lease_impl
from ..core.websocket_runtime import wait_for_ws_event as _wait_for_ws_event_impl
from ..core.websocket_runtime import (
    websocket_authenticated_user as _websocket_authenticated_user_impl,
)
from ..database import fetch_one, get_pool
from ..runtime_lease import check_runtime_lease

log = logging.getLogger("apexgrid")
bearer = HTTPBearer(auto_error=False)
bearer_dependency = Depends(bearer)


def _iter_main_modules() -> list[Any]:
    mods: list[Any] = []
    for mod_name in ("app.main", "backend.app.main"):
        mod = sys.modules.get(mod_name)
        if mod is not None and mod not in mods:
            mods.append(mod)
    return mods


def require_db() -> None:
    if get_pool().closed:
        raise HTTPException(503, "PostgreSQL is unavailable")


def require_allowed_origin(request: Request) -> None:
    return check_allowed_origin(request, CORS_ORIGINS)


def _get_fetch_one() -> Callable[..., Any]:
    for mod in _iter_main_modules():
        if (fn := getattr(mod, "fetch_one", None)) is not None:
            return cast(Callable[..., Any], fn)
    return fetch_one


def _resolve_jwt_secret() -> str:
    for mod in _iter_main_modules():
        if (sec := getattr(mod, "JWT_SECRET", None)) is not None:
            return str(sec)
    return JWT_SECRET


def _get_token_revocation() -> Any:
    for mod in _iter_main_modules():
        if (rev := getattr(mod, "token_revocation", None)) is not None:
            return rev
    return token_revocation


def _token_is_revoked(claims: dict[str, Any], *, fail_closed: bool = False) -> bool:
    rev = _get_token_revocation()
    return token_is_revoked(claims, fail_closed=fail_closed, is_revoked=rev.is_revoked)


def current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = bearer_dependency,
) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        authenticate_http_user(
            request,
            credentials,
            JWT_SECRET=_resolve_jwt_secret(),
            JWT_ALGORITHM=JWT_ALGORITHM,
            _token_is_revoked=_token_is_revoked,
            require_allowed_origin=require_allowed_origin,
            verify_csrf_token=verify_csrf_token,
            fetch_one=_get_fetch_one(),
            jsonable=jsonable,
        ),
    )


authenticated_user_dependency = Depends(current_user)


def roles(*allowed: str) -> Callable[..., Any]:
    return create_role_check(allowed, authenticated_user_dependency)


admin_role_dependency = Depends(roles("ADMIN"))
admin_steward_dependency = Depends(roles("ADMIN", "STEWARD"))
admin_steward_principal_dependency = Depends(roles("ADMIN", "STEWARD", "PRINCIPAL"))
admin_dependency = Depends(admin)


def admin_steward(user: Annotated[dict[str, Any], admin_steward_dependency]) -> dict[str, Any]:
    return user


def crud_routes(
    resource: str, table: str, cols: tuple[str, ...], joins: str = "", select: str | None = None
) -> None:
    for mod in _iter_main_modules():
        app = getattr(mod, "app", None)
        if app is not None:
            app.include_router(create_crud_router(resource, table, cols, joins, select))
            return


def _require_principal_own_team(team_id: UUID, user: dict[str, Any]) -> None:
    if user["role"] == "PRINCIPAL":
        own_team = fetch_one(
            "SELECT id FROM teams WHERE id=%s AND principal_user_id=%s", (team_id, user["id"])
        )
        if not own_team:
            raise HTTPException(403, "Principals may reserve pit boxes only for their own team")


_default_require_principal_own_team = _require_principal_own_team


def mongo_ready() -> Collection[dict[str, Any]]:
    for mod in _iter_main_modules():
        if (col := getattr(mod, "telemetry_collection", None)) is not None:
            return cast(Collection[dict[str, Any]], col)
    raise HTTPException(503, "MongoDB telemetry store is unavailable")


_default_mongo_ready = mongo_ready


def publish(session_id: UUID | str, kind: str, data: Any) -> None:
    for mod in _iter_main_modules():
        bus = getattr(mod, "bus", None)
        if bus is not None and hasattr(bus, "send"):
            bus.send(
                session_id,
                {
                    "type": kind,
                    "ts": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                    "session_id": str(session_id),
                    "data": jsonable(data),
                },
            )
            return


_default_publish = publish


async def _check_ws_runtime_lease(ws: WebSocket) -> bool:
    return await _check_ws_runtime_lease_impl(ws, check_runtime_lease)


async def _wait_for_ws_event(ws: WebSocket, queue: asyncio.Queue[Any]) -> dict[str, Any] | None:
    return await _wait_for_ws_event_impl(ws, queue, _check_ws_runtime_lease)


def _websocket_authenticated_user(token: str) -> Any:
    return _websocket_authenticated_user_impl(
        token, _resolve_jwt_secret(), JWT_ALGORITHM, _token_is_revoked, _get_fetch_one()
    )


def mongo_database_ready() -> Database[dict[str, Any]]:
    for mod in _iter_main_modules():
        if (client := getattr(mod, "mongo_client", None)) is not None:
            return cast(Database[dict[str, Any]], client[MONGODB_DATABASE])
    raise HTTPException(503, "MongoDB document store is unavailable")


_default_mongo_database_ready = mongo_database_ready

_SYMBOL_MAP: dict[str, str] = {
    sym: mod
    for mod, syms in (
        ("app.config", "APP_ENV CORS_ORIGINS JWT_ALGORITHM JWT_SECRET MONGODB_DATABASE"),
        ("app.runtime_lease", "acquire_runtime_lease check_runtime_lease"),
        ("app.core.events", "EventBus"),
        ("app.schemas_simulation", "SimulationControl"),
        ("app.simulation_core", "Simulation calculate_sector_performance"),
        ("app.core.simulation_tick", "advance_simulation_tick"),
        ("app.core.validation", "validate_session_laps"),
        ("app.core.security", "websocket_bearer"),
        ("app.core.serialization", "jsonable telemetry_ws_payload"),
        ("app.schemas_competition", "ResultIn"),
        ("app.schemas_operations", "Action AutoReservationIn Decision"),
        ("app.schemas_operations", "IncidentIn ReservationIn ReservationStatus"),
        ("app.demo_race_repository", "choose_demo_car_numbers"),
        ("app.demo_race_repository", "DemoRaceDeleteConflict DemoRaceSetupError"),
        ("app.api.dbms_sql", "constraint_demo"),
        ("app.api.dbms_lock", "dbms_recalculate"),
        ("app.api.dbms_mongo", "dbms_mongo_collection_documents dbms_mongo_collections"),
        ("app.api.laps", "admin dbms_race dbms_race_laps session_laps"),
        ("app.api.race_operation_routes", "recalculate results save_results"),
        ("app.api.race_operation_routes", "session_action standings"),
        ("app.api.simulation", "control_simulation"),
        ("app.api.stewards", "create_incident decide_incident"),
        ("app.api.stewards", "get_incidents stewards_handlers"),
        ("app.user_router", "create_user delete_user get_user"),
        ("app.user_router", "update_user user_router users"),
        ("app.auth_router", "login logout me refresh"),
        ("app.pit_strategy_router", "pit_strategy"),
        ("app.api.pit_write", "reserve_pit reserve_pit_auto update_pit_reservation"),
        ("app.api.pit_write", "_pit_write_handlers pit_write_router _pit_write_router"),
        ("app.database", "connection fetch_all fetch_one get_pool"),
    )
    for sym in syms.split()
}


def _import_symbol(mod_path: str, sym: str, prefer_backend: bool = False) -> Any:
    lookup_sym = "pit_write_router" if sym == "_pit_write_router" else sym
    prefixes = ("backend.", "") if prefer_backend else ("", "backend.")
    for prefix in prefixes:
        full_mod = f"{prefix}{mod_path}"
        if full_mod in sys.modules:
            val = getattr(sys.modules[full_mod], lookup_sym, None)
            if val is not None:
                return val
    for prefix in prefixes:
        candidate = f"{prefix}{mod_path}"
        try:
            mod = importlib.import_module(candidate)
            val = getattr(mod, lookup_sym, None)
            if val is not None:
                return val
        except ImportError:
            continue
    return None


def resolve_legacy_symbol(name: str, module_name: str = "") -> Any:
    if name == "jwt":
        import jwt

        return jwt
    if name == "token_revocation":
        return token_revocation
    if name in globals() and not name.startswith("_import") and not name.startswith("_SYMBOL"):
        return globals()[name]
    from . import simulation_service

    val = getattr(simulation_service, name, None)
    if val is not None:
        return val
    mod_path = _SYMBOL_MAP.get(name)
    if mod_path:
        prefer_backend = module_name.startswith("backend.")
        return _import_symbol(mod_path, name, prefer_backend=prefer_backend)
    return None
