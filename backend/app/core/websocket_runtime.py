import asyncio
from collections.abc import Callable
from typing import Any

import jwt
from fastapi import WebSocket


async def check_ws_runtime_lease(ws: WebSocket, check_runtime_lease: Callable[..., Any]) -> bool:
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


async def wait_for_ws_event(
    ws: WebSocket,
    queue: asyncio.Queue[Any],
    _check_ws_runtime_lease: Callable[..., Any],
) -> dict[str, Any] | None:
    while True:
        try:
            return await asyncio.wait_for(queue.get(), timeout=0.5)
        except TimeoutError:
            if not await _check_ws_runtime_lease(ws):
                return None


def websocket_authenticated_user(
    token: str,
    JWT_SECRET: str,
    JWT_ALGORITHM: str,
    _token_is_revoked: Callable[..., Any],
    fetch_one: Callable[..., Any],
) -> Any:
    claims = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    if _token_is_revoked(claims):
        return None
    return (
        fetch_one("SELECT id FROM users WHERE id=%s", (claims.get("sub"),))
        if claims.get("sub")
        else None
    )
