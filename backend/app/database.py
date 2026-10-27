import sys
from collections.abc import Iterator, Sequence
from contextlib import contextmanager, suppress
from typing import Any

if __name__ == "app.database":
    sys.modules.setdefault("backend.app.database", sys.modules[__name__])
elif __name__ == "backend.app.database":
    sys.modules.setdefault("app.database", sys.modules[__name__])

from psycopg import Connection
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .config import DATABASE_URL

DatabaseRow = dict[str, Any]


def _new_pool() -> ConnectionPool[Connection[DatabaseRow]]:
    return ConnectionPool(
        DATABASE_URL,
        min_size=1,
        max_size=10,
        kwargs={"row_factory": dict_row},
        open=False,
    )


pool: ConnectionPool[Connection[DatabaseRow]] = _new_pool()


def get_pool() -> ConnectionPool[Connection[DatabaseRow]]:
    return pool


def open_pool() -> None:
    global pool
    if pool.closed:
        pool = _new_pool()
    pool.open(wait=True)
    import sys

    for mod_name in ("app.database", "backend.app.database"):
        mod = sys.modules.get(mod_name)
        if mod is not None and mod is not sys.modules.get(__name__):
            setattr(mod, "pool", pool)  # noqa: B010


def close_pool() -> None:
    pool.close()
    import sys

    for mod_name in ("app.database", "backend.app.database"):
        mod = sys.modules.get(mod_name)
        if mod is not None and mod is not sys.modules.get(__name__):
            with suppress(Exception):
                other_pool = getattr(mod, "pool", None)
                if other_pool is not None:
                    other_pool.close()


@contextmanager
def connection() -> Iterator[Connection[DatabaseRow]]:
    with pool.connection() as conn:
        yield conn


def fetch_one(sql: str, params: Sequence[Any] = ()) -> Any:
    with connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row else None


def fetch_all(sql: str, params: Sequence[Any] = ()) -> list[DatabaseRow]:
    with connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]
