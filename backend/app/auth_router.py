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
from .schemas_auth import Login


def create_auth_router(
    require_allowed_origin: Callable[[Request], None],
    fetch_one_getter: Callable[[], Callable[..., Any]],
    jsonable: Callable[[Any], Any],
    secure_cookies: Callable[[], bool],
    current_user_dependency: Callable[..., Any],
) -> APIRouter:
    router = APIRouter()

    @router.post("/api/auth/login")
    def login(body: Login, response: Response, request: Request) -> dict[str, Any]:
        require_allowed_origin(request)
        try:
            user = fetch_one_getter()(
                "SELECT id,email,password_hash,full_name,role "
                "FROM users WHERE lower(email)=lower(%s)",
                (body.email,),
            )
        except Exception:
            raise HTTPException(503, "PostgreSQL is unavailable") from None
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
        expiry = datetime.now(UTC) + timedelta(minutes=JWT_MINUTES)
        session_id = secrets.token_urlsafe(32)
        token = jwt.encode(
            {"sub": str(user["id"]), "role": user["role"], "exp": expiry, "jti": session_id},
            JWT_SECRET,
            algorithm=JWT_ALGORITHM,
        )
        csrf_token = create_csrf_token(session_id, JWT_SECRET)
        set_auth_cookies(response, token, csrf_token, secure=secure_cookies())
        user_data = jsonable(
            {key: user[key] for key in ("id", "email", "full_name", "role")}
        )
        if request.headers.get("origin"):
            return {"user": user_data}
        return {"access_token": token, "token_type": "bearer", "user": user_data}

    @router.get("/api/auth/me")
    def me(user: Any = Depends(current_user_dependency)) -> Any:
        return user

    @router.post("/api/auth/logout")
    def logout(
        response: Response, user: Any = Depends(current_user_dependency)
    ) -> dict[str, str]:
        clear_auth_cookies(response, secure=secure_cookies())
        return {"detail": "Logged out"}

    return router
