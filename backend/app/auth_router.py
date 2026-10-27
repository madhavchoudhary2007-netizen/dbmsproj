"""Browser and legacy login and authentication routes."""

from __future__ import annotations

import secrets
import sys
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any, cast

if __name__ == "app.auth_router":
    sys.modules.setdefault("backend.app.auth_router", sys.modules[__name__])
elif __name__ == "backend.app.auth_router":
    sys.modules.setdefault("app.auth_router", sys.modules[__name__])

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from . import token_revocation
from .api.laps import get_race_db
from .auth_cookie import clear_auth_cookies, create_csrf_token, set_auth_cookies, verify_csrf_token
from .config import APP_ENV, CORS_ORIGINS, JWT_ALGORITHM, JWT_MINUTES, JWT_SECRET
from .core.auth_dependencies import check_allowed_origin, token_is_revoked
from .core.http_auth import authenticate_http_user
from .core.request_database import DatabaseSession
from .core.serialization import jsonable
from .login_limiter import LoginLimiter
from .schemas_auth import Login

router = APIRouter()
auth_router = router

bearer = HTTPBearer(auto_error=False)
bearer_dependency = Depends(bearer)
limiter = LoginLimiter()


def _resolve_jwt_secret() -> str:
    import sys

    auth_module = sys.modules.get("backend.app.auth_router")
    if auth_module is not None and hasattr(auth_module, "JWT_SECRET"):
        return str(auth_module.JWT_SECRET)
    main_module = sys.modules.get("backend.app.main")
    if main_module is not None and hasattr(main_module, "JWT_SECRET"):
        return str(main_module.JWT_SECRET)
    return JWT_SECRET


def _require_allowed_origin(request: Request) -> None:
    import sys

    main_module = sys.modules.get("backend.app.main")
    if main_module is not None and hasattr(main_module, "require_allowed_origin"):
        main_module.require_allowed_origin(request)
    else:
        check_allowed_origin(request, CORS_ORIGINS)


def _is_secure_cookie() -> bool:
    import sys

    main_module = sys.modules.get("backend.app.main")
    env = getattr(main_module, "APP_ENV", APP_ENV) if main_module is not None else APP_ENV
    return env != "local"


def _get_token_revocation() -> Any:
    import sys

    for mod_name in ("backend.app.main", "app.main"):
        mod = sys.modules.get(mod_name)
        if mod is not None and hasattr(mod, "token_revocation"):
            return mod.token_revocation
    return token_revocation


def _purge_revocations(
    limiter: LoginLimiter, account: str, source: str, token: object | None
) -> None:
    try:
        _get_token_revocation().purge_expired_revocations()
    except Exception:
        limiter.release(account, source, token)
        raise HTTPException(503, "PostgreSQL is unavailable") from None


def _revoke_claims(claims: dict[str, Any]) -> None:
    if "jti" not in claims:
        return
    try:
        expiry = datetime.fromtimestamp(claims["exp"], UTC)
        _get_token_revocation().revoke_token(claims["jti"], expiry)
    except Exception:
        raise HTTPException(503, "PostgreSQL is unavailable") from None


def current_user(
    request: Request,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        bearer_dependency,
    ] = None,
) -> dict[str, Any]:
    import sys

    main_module = sys.modules.get("backend.app.main")
    if main_module is not None and hasattr(main_module, "current_user"):
        return cast(dict[str, Any], main_module.current_user(request, credentials))

    def _tok_revoked(claims: dict[str, Any], *, fail_closed: bool = False) -> bool:
        rev = _get_token_revocation()
        return token_is_revoked(
            claims,
            fail_closed=fail_closed,
            is_revoked=rev.is_revoked,
        )

    def _query(sql: str, params: tuple[Any, ...]) -> dict[str, Any] | None:
        from . import database as db_module

        cur_fetch_one = (
            getattr(main_module, "fetch_one", db_module.fetch_one)
            if main_module is not None
            else db_module.fetch_one
        )
        return cast(dict[str, Any] | None, cur_fetch_one(sql, params))

    return cast(
        dict[str, Any],
        authenticate_http_user(
            request,
            credentials,
            JWT_SECRET=_resolve_jwt_secret(),
            JWT_ALGORITHM=JWT_ALGORITHM,
            _token_is_revoked=_tok_revoked,
            require_allowed_origin=_require_allowed_origin,
            verify_csrf_token=verify_csrf_token,
            fetch_one=_query,
            jsonable=jsonable,
        ),
    )


authenticated_user_dependency = Depends(current_user)


@router.post("/api/auth/login")
def login(
    body: Login,
    response: Response,
    request: Request,
    db: Annotated[DatabaseSession, Depends(get_race_db)],
) -> dict[str, Any]:
    _require_allowed_origin(request)
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
        user = db.fetch_one(
            "SELECT id,email,password_hash,full_name,role FROM users WHERE lower(email)=lower(%s)",
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
    if not valid_password or user is None:
        raise HTTPException(401, "Invalid email or password")
    _purge_revocations(limiter, account, source, admission.token)
    limiter.release(account, source, admission.token)
    expiry = datetime.now(UTC) + timedelta(minutes=JWT_MINUTES)
    session_id = secrets.token_urlsafe(32)
    jwt_secret = _resolve_jwt_secret()
    token = jwt.encode(
        {"sub": str(user["id"]), "role": user["role"], "exp": expiry, "jti": session_id},
        jwt_secret,
        algorithm=JWT_ALGORITHM,
    )
    csrf = create_csrf_token(session_id, jwt_secret)
    set_auth_cookies(response, token, csrf, secure=_is_secure_cookie())
    user_data = jsonable({key: user[key] for key in ("id", "email", "full_name", "role")})
    if request.headers.get("origin"):
        return {"user": user_data}
    return {"access_token": token, "token_type": "bearer", "user": user_data}


@router.get("/api/auth/me")
def me(user: Annotated[dict[str, Any], authenticated_user_dependency]) -> Any:
    return user


@router.post("/api/auth/logout")
def logout(
    request: Request,
    response: Response,
    user: Annotated[dict[str, Any], authenticated_user_dependency],
) -> dict[str, str]:
    _revoke_claims(request.state.auth_claims)
    clear_auth_cookies(response, secure=_is_secure_cookie())
    return {"detail": "Logged out"}


@router.post("/api/auth/refresh")
def refresh(
    request: Request,
    response: Response,
    user: Annotated[dict[str, Any], authenticated_user_dependency],
) -> dict[str, Any]:
    claims = getattr(request.state, "auth_claims", None)
    if isinstance(claims, dict) and "jti" in claims:
        _revoke_claims(claims)
    expiry = datetime.now(UTC) + timedelta(minutes=JWT_MINUTES)
    session_id = secrets.token_urlsafe(32)
    jwt_secret = _resolve_jwt_secret()
    token = jwt.encode(
        {"sub": str(user["id"]), "role": user["role"], "exp": expiry, "jti": session_id},
        jwt_secret,
        algorithm=JWT_ALGORITHM,
    )
    csrf = create_csrf_token(session_id, jwt_secret)
    set_auth_cookies(response, token, csrf, secure=_is_secure_cookie())
    user_data = jsonable({key: user[key] for key in ("id", "email", "full_name", "role")})
    if request.headers.get("origin"):
        return {"user": user_data}
    return {"access_token": token, "token_type": "bearer", "user": user_data}


def create_auth_router(
    require_allowed_origin: Callable[[Request], None],
    fetch_one_getter: Callable[[], Callable[..., Any]],
    jsonable: Callable[[Any], Any],
    secure_cookies: Callable[[], bool],
    current_user_dependency: Callable[..., Any],
) -> APIRouter:
    rt = APIRouter()
    factory_limiter = LoginLimiter()
    current_user_dep = Depends(current_user_dependency)

    @rt.post("/api/auth/login")
    def legacy_login(body: Login, response: Response, request: Request) -> dict[str, Any]:
        require_allowed_origin(request)
        account = body.email.strip().casefold()
        source = request.client.host if request.client else ""
        admission = factory_limiter.admit(account, source)
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
            factory_limiter.release(account, source, admission.token)
            raise HTTPException(503, "PostgreSQL is unavailable") from None
        try:
            valid_password = bool(
                user and bcrypt.checkpw(body.password.encode(), user["password_hash"].encode())
            )
        except (ValueError, TypeError):
            valid_password = False
        if not valid_password or user is None:
            raise HTTPException(401, "Invalid email or password")
        _purge_revocations(factory_limiter, account, source, admission.token)
        factory_limiter.release(account, source, admission.token)
        expiry = datetime.now(UTC) + timedelta(minutes=JWT_MINUTES)
        session_id = secrets.token_urlsafe(32)
        jwt_secret = _resolve_jwt_secret()
        token = jwt.encode(
            {"sub": str(user["id"]), "role": user["role"], "exp": expiry, "jti": session_id},
            jwt_secret,
            algorithm=JWT_ALGORITHM,
        )
        csrf = create_csrf_token(session_id, jwt_secret)
        set_auth_cookies(response, token, csrf, secure=secure_cookies())
        user_data = jsonable({key: user[key] for key in ("id", "email", "full_name", "role")})
        if request.headers.get("origin"):
            return {"user": user_data}
        return {"access_token": token, "token_type": "bearer", "user": user_data}

    @rt.get("/api/auth/me")
    def legacy_me(user: Any = current_user_dep) -> Any:
        return user

    @rt.post("/api/auth/logout")
    def legacy_logout(
        request: Request, response: Response, user: Any = current_user_dep
    ) -> dict[str, str]:
        _revoke_claims(request.state.auth_claims)
        clear_auth_cookies(response, secure=secure_cookies())
        return {"detail": "Logged out"}

    return rt


__all__ = [
    "authenticated_user_dependency",
    "auth_router",
    "create_auth_router",
    "current_user",
    "login",
    "logout",
    "me",
    "refresh",
    "router",
]
