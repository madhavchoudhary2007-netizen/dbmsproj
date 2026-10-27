from collections.abc import Callable
from typing import Annotated, Any, cast

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..auth_cookie import verify_csrf_token
from ..config import CORS_ORIGINS, JWT_ALGORITHM, JWT_SECRET
from ..token_revocation import revocation_key
from .auth_dependencies import check_allowed_origin, create_role_check, token_is_revoked
from .http_auth import authenticate_http_user
from .request_database import DatabaseSession
from .runtime import RuntimeState, get_pool, get_runtime
from .serialization import jsonable


def _resolve_jwt_secret() -> str:
    import sys

    for mod_name in ("backend.app.main", "app.main"):
        mod = sys.modules.get(mod_name)
        if mod is not None and hasattr(mod, "JWT_SECRET"):
            return str(mod.JWT_SECRET)
    return JWT_SECRET


def current_user(
    request: Request,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(HTTPBearer(auto_error=False)),
    ],
    runtime: Annotated[RuntimeState, Depends(get_runtime)],
) -> dict[str, Any]:
    def query(sql: str, params: tuple[Any, ...]) -> dict[str, Any] | None:
        return DatabaseSession(get_pool(runtime)).fetch_one(sql, params)

    def is_revoked(jti: str) -> bool:
        row = query(
            "SELECT jti FROM revoked_tokens WHERE jti = %s AND expires_at >= now()",
            (revocation_key(jti),),
        )
        return row is not None

    def revoked(claims: dict[str, Any], *, fail_closed: bool = False) -> bool:
        return token_is_revoked(claims, fail_closed=fail_closed, is_revoked=is_revoked)

    return cast(
        dict[str, Any],
        authenticate_http_user(
            request,
            credentials,
            JWT_SECRET=_resolve_jwt_secret(),
            JWT_ALGORITHM=JWT_ALGORITHM,
            _token_is_revoked=revoked,
            require_allowed_origin=lambda req: check_allowed_origin(req, CORS_ORIGINS),
            verify_csrf_token=verify_csrf_token,
            fetch_one=query,
            jsonable=jsonable,
        ),
    )


def require_roles(*allowed: str) -> Callable[..., Any]:
    return create_role_check(allowed, Depends(current_user))
