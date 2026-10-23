from datetime import datetime
from uuid import NAMESPACE_URL, UUID, uuid5

from .database import connection, fetch_one


def revocation_key(jti: str) -> UUID:
    return uuid5(NAMESPACE_URL, "apexgrid.jwt:" + jti)


def is_revoked(jti: str) -> bool:
    row = fetch_one(
        "SELECT jti FROM revoked_tokens WHERE jti = %s AND expires_at >= now()",
        (revocation_key(jti),),
    )
    return row is not None


def revoke_token(jti: str, expires_at: datetime) -> None:
    with connection() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO revoked_tokens (jti, expires_at) VALUES (%s, %s) "
            "ON CONFLICT (jti) DO NOTHING",
            (revocation_key(jti), expires_at),
        )


def purge_expired_revocations() -> None:
    with connection() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM revoked_tokens WHERE expires_at < now()")
