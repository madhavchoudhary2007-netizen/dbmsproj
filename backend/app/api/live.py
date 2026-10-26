from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Annotated, Any, cast
from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from ..core.events import EventBus
from ..core.runtime import get_bus
from ..core.security import websocket_bearer

router = APIRouter()
live_router = router


def _resolve_bus(bus: EventBus | None = None) -> EventBus:
    if bus is not None:
        return bus
    import sys

    main_module = sys.modules.get("backend.app.main")
    if main_module is not None and hasattr(main_module, "bus"):
        return cast(EventBus, main_module.bus)
    return EventBus()


def _resolve_check_ws_runtime_lease() -> Callable[[WebSocket], Any]:
    import sys

    main_module = sys.modules.get("backend.app.main")
    if main_module is not None and hasattr(main_module, "_check_ws_runtime_lease"):
        return cast(Callable[[WebSocket], Any], main_module._check_ws_runtime_lease)
    from ..core.websocket_runtime import check_ws_runtime_lease

    return lambda ws: check_ws_runtime_lease(ws, lambda _lease: None)


def _resolve_websocket_authenticated_user() -> Callable[[str], Any]:
    import sys

    main_module = sys.modules.get("backend.app.main")
    if main_module is not None and hasattr(main_module, "_websocket_authenticated_user"):
        return cast(Callable[[str], Any], main_module._websocket_authenticated_user)
    return lambda _token: None


def _resolve_wait_for_ws_event() -> Callable[[WebSocket, asyncio.Queue[Any]], Any]:
    import sys

    main_module = sys.modules.get("backend.app.main")
    if main_module is not None and hasattr(main_module, "_wait_for_ws_event"):
        return cast(Callable[[WebSocket, asyncio.Queue[Any]], Any], main_module._wait_for_ws_event)
    from ..core.websocket_runtime import wait_for_ws_event

    return lambda ws, q: wait_for_ws_event(ws, q, lambda _ws: True)


def _resolve_cors_origins() -> list[str]:
    import sys

    main_module = sys.modules.get("backend.app.main")
    if main_module is not None and hasattr(main_module, "CORS_ORIGINS"):
        return cast(list[str], main_module.CORS_ORIGINS)
    from ..config import CORS_ORIGINS

    return CORS_ORIGINS


@router.websocket("/api/ws/sessions/{session_id}")
async def session_ws(
    ws: WebSocket,
    session_id: UUID,
    bus: Annotated[EventBus | None, Depends(get_bus)] = None,
) -> None:
    check_lease = _resolve_check_ws_runtime_lease()
    if not await check_lease(ws):
        return
    cors_origins = _resolve_cors_origins()
    origin = ws.headers.get("origin")
    if origin is not None and origin not in cors_origins:
        await ws.close(code=4403, reason="Origin not allowed")
        return
    protocols = ws.scope.get("subprotocols", [])
    subprotocol_token = websocket_bearer(protocols)
    cookie_token = ws.cookies.get("apexgrid_session")
    token = subprotocol_token or cookie_token
    if not token:
        await ws.close(code=4401, reason="Expected apexgrid.jwt subprotocol and bearer token")
        return
    auth_user_fn = _resolve_websocket_authenticated_user()
    try:
        user = auth_user_fn(token)
    except Exception:
        user = None
    if not user:
        await ws.close(code=4401, reason="Invalid or expired token")
        return
    await ws.accept(subprotocol="apexgrid.jwt" if subprotocol_token else None)
    event_bus = _resolve_bus(bus)
    q = event_bus.subscribe(session_id)
    wait_event = _resolve_wait_for_ws_event()
    try:
        while True:
            event = await wait_event(ws, q)
            if event is None:
                return
            if not await check_lease(ws):
                return
            await ws.send_json(event)
    except WebSocketDisconnect:
        pass
    finally:
        event_bus.unsubscribe(session_id, q)


def create_live_router(  # noqa: C901
    _check_ws_runtime_lease: Callable[..., Any],
    _websocket_authenticated_user: Callable[..., Any],
    _wait_for_ws_event: Callable[..., Any],
    get_bus: Callable[[], Any],
    get_cors_origins: Callable[[], Any],
    websocket_bearer: Callable[..., Any],
) -> tuple[APIRouter, Callable[..., Any]]:
    legacy_router = APIRouter()

    @legacy_router.websocket("/api/ws/sessions/{session_id}")
    async def session_ws(ws: WebSocket, session_id: UUID) -> None:
        if not await _check_ws_runtime_lease(ws):
            return
        origin = ws.headers.get("origin")
        if origin is not None and origin not in get_cors_origins():
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
        q = get_bus().subscribe(session_id)
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
            get_bus().unsubscribe(session_id, q)

    return legacy_router, session_ws
