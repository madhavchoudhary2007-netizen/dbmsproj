from __future__ import annotations

from collections.abc import Callable
from typing import Any
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect


def create_live_router(  # noqa: C901
    _check_ws_runtime_lease: Callable[..., Any],
    _websocket_authenticated_user: Callable[..., Any],
    _wait_for_ws_event: Callable[..., Any],
    get_bus: Callable[[], Any],
    get_cors_origins: Callable[[], Any],
    websocket_bearer: Callable[..., Any],
) -> tuple[APIRouter, Callable[..., Any]]:
    router = APIRouter()

    @router.websocket("/api/ws/sessions/{session_id}")
    async def session_ws(ws: WebSocket, session_id: UUID):
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

    return router, session_ws
