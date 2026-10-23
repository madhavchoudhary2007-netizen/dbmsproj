"""Browser and legacy login route."""

import secrets
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response

from .auth_cookie import clear_auth_cookies, create_csrf_token, set_auth_cookies
from .config import JWT_ALGORITHM, JWT_MINUTES, JWT_SECRET
from .login_limiter import LoginLimiter
from .schemas_auth import Login


def create_auth_router(
    require_allowed_origin: Callable[[Request], None],
    fetch_one_getter: Callable[[], Callable[..., Any]],
    jsonable: Callable[[Any], Any],
    secure_cookies: Callable[[], bool],
    current_user_dependency: Callable[..., Any],
) -> APIRouter:
    router = APIRouter()
    limiter = LoginLimiter()
    current_user_dep = Depends(current_user_dependency)

    @router.post("/api/auth/login")
    def login(body: Login, response: Response, request: Request) -> dict[str, Any]:
        require_allowed_origin(request)
        account = body.email.strip().casefold()
        source = request.client.host if request.client else ""
        admission = limiter.admit(account, source)
        if admission.retry_after is not None:
            raise HTTPException(
                429,
                "Too many login attempts",
                headers={"Retry-After": str(admission.retry_after)},
            )
        try:
            user = fetch_one_getter()(
                "SELECT id,email,password_hash,full_name,role "
                "FROM users WHERE lower(email)=lower(%s)",
                (body.email,),
            )
        except Exception:
            limiter.release(account, source, admission.token)
            raise HTTPException(503, "PostgreSQL is unavailable") from None
        try:
            valid_password = bool(
                user and bcrypt.checkpw(body.password.encode(), user["password_hash"].encode())
            )
        except (ValueError, TypeError):
            valid_password = False
        if not valid_password:
            raise HTTPException(401, "Invalid email or password")
        limiter.release(account, source, admission.token)
        expiry = datetime.now(UTC) + timedelta(minutes=JWT_MINUTES)
        session_id = secrets.token_urlsafe(32)
        token = jwt.encode(
            {"sub": str(user["id"]), "role": user["role"], "exp": expiry, "jti": session_id},
            JWT_SECRET,
            algorithm=JWT_ALGORITHM,
        )
        csrf_token = create_csrf_token(session_id, JWT_SECRET)
        set_auth_cookies(response, token, csrf_token, secure=secure_cookies())
        user_data = jsonable({key: user[key] for key in ("id", "email", "full_name", "role")})
        if request.headers.get("origin"):
            return {"user": user_data}
        return {"access_token": token, "token_type": "bearer", "user": user_data}

    @router.get("/api/auth/me")
    def me(user: Any = current_user_dep) -> Any:
        return user

    @router.post("/api/auth/logout")
    def logout(response: Response, user: Any = current_user_dep) -> dict[str, str]:
        clear_auth_cookies(response, secure=secure_cookies())
        return {"detail": "Logged out"}

    return router
