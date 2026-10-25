from collections.abc import Callable
from typing import Any, cast
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from psycopg import sql

from ..crud_repository import CrudDeleteError


def create_crud_router(
    resource: str,
    table: str,
    cols: tuple[str, ...],
    joins: str = "",
    select: str | None = None,
    *,
    authenticated_user_dependency: Any,
    admin_role_dependency: Any,
    limit_offset: Callable[..., Any],
    jsonable: Callable[..., Any],
    list_crud_rows: Callable[..., Any],
    get_crud_row: Callable[..., Any],
    _require_crud_record: Callable[..., Any],
    _crud_write_payload: Callable[..., Any],
    validate_session_laps: Callable[..., Any],
    create_crud_row: Callable[..., Any],
    fetch_one: Callable[..., Any],
    update_crud_row: Callable[..., Any],
    delete_crud_row: Callable[..., Any],
    get_telemetry_collection: Callable[[], Any],
) -> APIRouter:
    router = APIRouter()
    # Names here are hard-coded contract identifiers, never user supplied SQL.
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
        user: dict[str, object] = authenticated_user_dependency,
    ) -> list[dict[str, object]]:
        page_limit, page_offset = limit_offset(limit, offset)
        rows = jsonable(list_crud_rows(base, page_limit, page_offset))
        return cast(list[dict[str, object]], rows)

    @router.get(prefix + "/{item_id}", response_model=None)
    def get_item(
        item_id: UUID, user: dict[str, object] = authenticated_user_dependency
    ) -> dict[str, object]:
        result = get_crud_row(base, table, item_id)
        return cast(
            dict[str, object],
            jsonable(_require_crud_record(result, f"{resource[:-1].capitalize()} not found")),
        )

    @router.post(prefix, status_code=201, response_model=None)
    def create_item(
        payload: dict[str, Any], user: dict[str, object] = admin_role_dependency
    ) -> dict[str, object]:
        clean = _crud_write_payload(payload, cols)
        validate_session_laps(table, clean)
        row = create_crud_row(table, clean)
        return cast(dict[str, object], jsonable(row))

    @router.patch(prefix + "/{item_id}", response_model=None)
    def update_item(
        item_id: UUID,
        payload: dict[str, Any],
        user: dict[str, object] = admin_role_dependency,
    ) -> dict[str, object]:
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
        return cast(
            dict[str, object],
            jsonable(_require_crud_record(row, f"{resource[:-1].capitalize()} not found")),
        )

    @router.delete(prefix + "/{item_id}", status_code=204, response_model=None)
    def delete_item(item_id: UUID, user: dict[str, object] = admin_role_dependency) -> None:
        telemetry_collection = get_telemetry_collection()
        try:
            delete_crud_row(table, resource, item_id, telemetry_collection)
        except CrudDeleteError as exc:
            raise HTTPException(exc.status_code, exc.detail) from exc
        return None

    return router
