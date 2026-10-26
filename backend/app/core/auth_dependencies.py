from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from fastapi import HTTPException, Request


def check_allowed_origin(request: Request, CORS_ORIGINS: Sequence[str]) -> None:
    origin = request.headers.get("origin")
    if origin is not None and origin not in CORS_ORIGINS:
        raise HTTPException(403, "Origin not allowed")


def token_is_revoked(
    claims: dict[str, Any],
    *,
    fail_closed: bool = False,
    is_revoked: Callable[..., Any],
) -> bool:
    if "jti" not in claims:
        return False
    jti = claims["jti"]
    if not isinstance(jti, str) or not jti:
        raise ValueError()
    try:
        return bool(is_revoked(jti))
    except Exception:
        if not fail_closed:
            raise
        raise HTTPException(503, "PostgreSQL is unavailable") from None


def create_role_check(
    allowed: tuple[str, ...], authenticated_user_dependency: Any
) -> Callable[..., Any]:
    def check(user: Any = authenticated_user_dependency) -> Any:
        if user["role"] not in allowed:
            raise HTTPException(403, "Insufficient role")
        return user

    return check
