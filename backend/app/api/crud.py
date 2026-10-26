from __future__ import annotations

from collections.abc import Callable
from typing import Annotated, Any, cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from psycopg import sql
from pymongo.collection import Collection

from ..core.request_auth import current_user
from ..core.request_database import DatabaseSession
from ..core.runtime import RuntimeState
from ..core.serialization import jsonable
from ..core.validation import (
    _crud_write_payload,
    _require_crud_record,
    limit_offset,
    validate_session_laps,
)
from ..crud_repository import (
    CrudDeleteError,
    create_crud_row,
    delete_crud_row,
    get_crud_row,
    list_crud_rows,
    update_crud_row,
)
from ..database import fetch_one
from .laps import admin, get_race_db, get_race_telemetry

_DEFAULT_REQUEST: Any = None


def _resolve_db(database: DatabaseSession | None = None) -> DatabaseSession:
    if database is not None:
        return database
    import sys

    from .. import database as db_module

    main_module = sys.modules.get("backend.app.main")
    cur_fetch_one = (
        getattr(main_module, "fetch_one", db_module.fetch_one)
        if main_module is not None
        else db_module.fetch_one
    )
    cur_fetch_all = (
        getattr(main_module, "fetch_all", db_module.fetch_all)
        if main_module is not None
        else db_module.fetch_all
    )
    from .laps import _MonkeypatchedDatabaseSession

    return _MonkeypatchedDatabaseSession(cur_fetch_one, cur_fetch_all)


def _resolve_telemetry(
    request: Request | None = None,
    telemetry: Collection[dict[str, Any]] | None = None,
) -> Collection[dict[str, Any]] | None:
    if telemetry is not None:
        return telemetry
    if request is not None:
        runtime = getattr(request.app.state, "runtime", None)
        if isinstance(runtime, RuntimeState) and runtime.telemetry_collection is not None:
            return runtime.telemetry_collection
        try:
            return get_race_telemetry(request)
        except HTTPException:
            pass
    import sys

    main_module = sys.modules.get("backend.app.main")
    if main_module is not None:
        t_col = getattr(main_module, "telemetry_collection", None)
        if t_col is not None:
            return cast(Collection[dict[str, Any]], t_col)
        m_ready = getattr(main_module, "mongo_ready", None)
        if m_ready is not None:
            try:
                return cast(Collection[dict[str, Any]], m_ready())
            except HTTPException:
                pass
    return None


def _fetch_listing_rows(
    base: str,
    page_limit: int,
    page_offset: int,
    db: DatabaseSession,
    list_rows_fn: Callable[..., Any],
) -> list[Any]:
    if list_rows_fn is not list_crud_rows:
        return cast(list[Any], list_rows_fn(base, page_limit, page_offset))
    return db.fetch_all(base + " ORDER BY 1 LIMIT %s OFFSET %s", (page_limit, page_offset))


def _check_session_update(
    item_id: UUID,
    clean: dict[str, Any],
    db: DatabaseSession,
    fetch_one_fn: Callable[..., Any],
) -> None:
    if fetch_one_fn is not fetch_one:
        existing = fetch_one_fn("SELECT state FROM race_sessions WHERE id=%s", (item_id,))
    else:
        existing = db.fetch_one("SELECT state FROM race_sessions WHERE id=%s", (item_id,))
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


def _get_delete_telemetry(
    request: Request | None,
    telemetry: Any,
    get_col_fn: Callable[[], Any] | None,
) -> Collection[dict[str, Any]] | None:
    if get_col_fn is not None:
        return cast(Collection[dict[str, Any]] | None, get_col_fn())
    return _resolve_telemetry(request, cast(Collection[dict[str, Any]] | None, telemetry))


def create_crud_router(
    resource: str,
    table: str,
    cols: tuple[str, ...],
    joins: str = "",
    select: str | None = None,
    *,
    authenticated_user_dependency: Any = None,
    admin_role_dependency: Any = None,
    limit_offset: Callable[..., Any] = limit_offset,
    jsonable: Callable[..., Any] = jsonable,
    list_crud_rows: Callable[..., Any] = list_crud_rows,
    get_crud_row: Callable[..., Any] = get_crud_row,
    _require_crud_record: Callable[..., Any] = _require_crud_record,
    _crud_write_payload: Callable[..., Any] = _crud_write_payload,
    validate_session_laps: Callable[..., Any] = validate_session_laps,
    create_crud_row: Callable[..., Any] = create_crud_row,
    fetch_one: Callable[..., Any] = fetch_one,
    update_crud_row: Callable[..., Any] = update_crud_row,
    delete_crud_row: Callable[..., Any] = delete_crud_row,
    get_telemetry_collection: Callable[[], Any] | None = None,
) -> APIRouter:
    router = APIRouter()
    auth_dep = (
        authenticated_user_dependency
        if authenticated_user_dependency is not None
        else Depends(current_user)
    )
    admin_dep = admin_role_dependency if admin_role_dependency is not None else Depends(admin)
    telemetry_dep: Any = (
        Depends(get_race_telemetry) if table == "race_sessions" else Depends(lambda: None)
    )
    projection = select or f"{table}.*"
    base = (
        sql.SQL("SELECT {} FROM {} {}")
        .format(sql.SQL(projection), sql.Identifier(table), sql.SQL(joins))
        .as_string()
    )
    prefix = f"/api/{resource}"

    @router.get(prefix, response_model=None)
    def listing(
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0),
        user: dict[str, object] = auth_dep,
        database: Annotated[DatabaseSession | None, Depends(get_race_db)] = None,
    ) -> list[dict[str, object]]:
        page_limit, page_offset = limit_offset(limit, offset)
        db = _resolve_db(database)
        raw_rows = _fetch_listing_rows(base, page_limit, page_offset, db, list_crud_rows)
        return cast(list[dict[str, object]], jsonable(raw_rows))

    @router.get(prefix + "/{item_id}", response_model=None)
    def get_item(
        item_id: UUID,
        user: dict[str, object] = auth_dep,
        database: Annotated[DatabaseSession | None, Depends(get_race_db)] = None,
    ) -> dict[str, object]:
        _resolve_db(database)
        result = get_crud_row(base, table, item_id)
        return cast(
            dict[str, object],
            jsonable(_require_crud_record(result, f"{resource[:-1].capitalize()} not found")),
        )

    @router.post(prefix, status_code=201, response_model=None)
    def create_item(
        payload: dict[str, Any],
        user: dict[str, object] = admin_dep,
        database: Annotated[DatabaseSession | None, Depends(get_race_db)] = None,
    ) -> dict[str, object]:
        clean = _crud_write_payload(payload, cols)
        validate_session_laps(table, clean)
        _resolve_db(database)
        row = create_crud_row(table, clean)
        return cast(dict[str, object], jsonable(row))

    @router.patch(prefix + "/{item_id}", response_model=None)
    def update_item(
        item_id: UUID,
        payload: dict[str, Any],
        user: dict[str, object] = admin_dep,
        database: Annotated[DatabaseSession | None, Depends(get_race_db)] = None,
    ) -> dict[str, object]:
        clean = _crud_write_payload(payload, cols)
        validate_session_laps(table, clean)
        if table == "race_sessions":
            db = _resolve_db(database)
            _check_session_update(item_id, clean, db, fetch_one)
        row = update_crud_row(table, item_id, clean)
        return cast(
            dict[str, object],
            jsonable(_require_crud_record(row, f"{resource[:-1].capitalize()} not found")),
        )

    @router.delete(prefix + "/{item_id}", status_code=204, response_model=None)
    def delete_item(
        item_id: UUID,
        request: Request = _DEFAULT_REQUEST,
        user: dict[str, object] = admin_dep,
        database: Annotated[DatabaseSession | None, Depends(get_race_db)] = None,
        telemetry: Any = telemetry_dep,
    ) -> None:
        _resolve_db(database)
        telemetry_collection = _get_delete_telemetry(request, telemetry, get_telemetry_collection)
        try:
            delete_crud_row(table, resource, item_id, telemetry_collection)
        except CrudDeleteError as exc:
            raise HTTPException(exc.status_code, exc.detail) from exc
        return None

    return router


CRUD_RESOURCES: tuple[tuple[str, str, tuple[str, ...], str, str | None], ...] = (
    ("championships", "championships", ("id", "name", "season"), "", None),
    ("circuits", "circuits", ("id", "name", "country", "length_km"), "", None),
    (
        "teams",
        "teams",
        ("id", "name", "principal_user_id"),
        "LEFT JOIN users u ON u.id=teams.principal_user_id",
        "teams.*,u.full_name AS principal_name",
    ),
    (
        "drivers",
        "drivers",
        ("id", "user_id", "licence_number", "number"),
        (
            "LEFT JOIN users u ON u.id=drivers.user_id LEFT JOIN "
            "team_memberships tm ON tm.driver_id="
            "drivers.id AND tm.end_date IS NULL LEFT JOIN teams t ON t.id=tm.team_id"
        ),
        "drivers.*,u.full_name,u.email,t.name AS team_name",
    ),
    (
        "events",
        "race_events",
        ("id", "championship_id", "circuit_id", "round_number", "name", "start_date"),
        (
            "LEFT JOIN championships ch ON ch.id=race_events.championship_id LEFT JOIN "
            "circuits c ON "
            "c.id=race_events.circuit_id"
        ),
        (
            "race_events.*,ch.name AS championship_name,c.name AS ci"
            "rcuit_name,c.country AS circuit_country"
        ),
    ),
    (
        "sessions",
        "race_sessions",
        ("id", "event_id", "session_type", "scheduled_at", "total_laps", "safety_car"),
        (
            "LEFT JOIN race_events e ON e.id=race_sessions.event_id LEFT JOIN "
            "circuits c ON c.id=e.ci"
            "rcuit_id"
        ),
        "race_sessions.*,e.name AS event_name,c.name AS circuit_name",
    ),
)


def build_crud_router() -> APIRouter:
    router = APIRouter()
    for res, tbl, cols, joins, select in CRUD_RESOURCES:
        router.include_router(create_crud_router(res, tbl, cols, joins, select))
    return router


crud_router = build_crud_router()
