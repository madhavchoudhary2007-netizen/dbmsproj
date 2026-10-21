"""Cookie helpers shared by browser authentication and CSRF handlers."""

import hashlib
import hmac
import secrets


SESSION_COOKIE = "apexgrid_session"
CSRF_COOKIE = "apexgrid_csrf"


def create_csrf_token(session_id: str, secret: str) -> str:
    """Return a random nonce signed for one JWT session identifier."""
    nonce = secrets.token_urlsafe(32)
    message = f"{session_id}.{nonce}".encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
    return f"{nonce}.{signature}"


def verify_csrf_token(value: str, session_id: str, secret: str) -> bool:
    """Check a nonce/signature pair against the session identifier."""
    try:
        nonce, signature = value.rsplit(".", 1)
    except (AttributeError, ValueError):
        return False
    if not nonce or not signature:
        return False
    message = f"{session_id}.{nonce}".encode("utf-8")
    expected = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected)


def set_auth_cookies(response, token: str, csrf_token: str, *, secure: bool) -> None:
    """Set host-only browser session cookies with shared ADR-002 flags."""
    response.set_cookie(
        SESSION_COOKIE, token, httponly=True, secure=secure, samesite="lax", path="/"
    )
    response.set_cookie(
        CSRF_COOKIE, csrf_token, httponly=False, secure=secure, samesite="lax", path="/"
    )
