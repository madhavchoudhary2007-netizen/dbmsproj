from __future__ import annotations

import hmac
from collections.abc import Callable
from typing import Any

import jwt
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials


def authenticate_http_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None,
    *,
    JWT_SECRET: str,
    JWT_ALGORITHM: str,
    _token_is_revoked: Callable[..., Any],
    require_allowed_origin: Callable[..., Any],
    verify_csrf_token: Callable[..., Any],
    fetch_one: Callable[..., Any],
    jsonable: Callable[..., Any],
) -> Any:
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
