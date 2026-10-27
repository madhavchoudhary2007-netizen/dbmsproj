import sys
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

_REQUEST_AUTH_MODULE = sys.modules[__name__]
_RUNTIME_MODULE = sys.modules[f"{__package__}.runtime"]
if __name__ == "app.core.request_auth":
    sys.modules["backend.app.core"] = sys.modules[__package__]
    sys.modules["backend.app.core.request_auth"] = _REQUEST_AUTH_MODULE
    sys.modules["backend.app.core.runtime"] = _RUNTIME_MODULE
elif __name__ == "backend.app.core.request_auth":
    sys.modules["app.core"] = sys.modules[__package__]
    sys.modules["app.core.request_auth"] = _REQUEST_AUTH_MODULE
    sys.modules["app.core.runtime"] = _RUNTIME_MODULE
for _package_name, _module_name in (
    ("app.core", "app.core.request_auth"),
    ("backend.app.core", "backend.app.core.request_auth"),
):
    _package = sys.modules.get(_package_name)
    _module = sys.modules.get(_module_name)
    if _package is not None and _module is not None:
        vars(_package)["request_auth"] = _module
for _package_name in ("app.core", "backend.app.core"):
    _package = sys.modules.get(_package_name)
    if _package is not None:
        vars(_package)["runtime"] = _RUNTIME_MODULE

_INITIAL_JWT_SECRET = JWT_SECRET


def _resolve_jwt_secret() -> str:
    if JWT_SECRET != _INITIAL_JWT_SECRET:
        return JWT_SECRET

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
