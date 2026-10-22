"""PostgreSQL session advisory lock for single-process runtime ownership."""

from typing import Any

import psycopg
from psycopg import Connection

from .config import DATABASE_URL

_LOCK_CLASS_ID = 1_097_292_881
_LOCK_OBJECT_ID = 1_097_292_884


def acquire_runtime_lease() -> Connection[Any]:
    """Acquire the process-wide runtime lease on a dedicated connection."""
    try:
        connection = psycopg.connect(DATABASE_URL, autocommit=True)
    except Exception as error:
        raise RuntimeError("Could not connect to PostgreSQL for runtime ownership") from error

    try:
        result = connection.execute(
            "SELECT pg_try_advisory_lock(%s, %s)",
            (_LOCK_CLASS_ID, _LOCK_OBJECT_ID),
        ).fetchone()
        if result is None or result[0] is not True:
            raise RuntimeError("Runtime lease has an active owner")
    except Exception:
        connection.close()
        raise
    return connection


def check_runtime_lease(connection: Connection[Any]) -> None:
    """Raise when the lease's owner connection is closed or unreachable."""
    if connection.closed:
        raise RuntimeError("Runtime lease owner connection is closed")
    try:
        connection.execute("SELECT 1")
    except psycopg.Error as error:
        connection.close()
        raise RuntimeError("Runtime lease owner connection lost database connectivity") from error
