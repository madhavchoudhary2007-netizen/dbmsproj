from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from typing import Any

from psycopg import Connection
from psycopg_pool import ConnectionPool

DatabaseRow = dict[str, Any]


class DatabaseSession:
    def __init__(self, pool: ConnectionPool[Connection[DatabaseRow]]) -> None:
        self.pool = pool

    @contextmanager
    def connection(self) -> Iterator[Connection[DatabaseRow]]:
        with self.pool.connection() as conn:
            yield conn

    def fetch_one(self, sql: str, params: Sequence[Any] = ()) -> DatabaseRow | None:
        with self.connection() as conn, conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            return dict(row) if row else None

    def fetch_all(self, sql: str, params: Sequence[Any] = ()) -> list[DatabaseRow]:
        with self.connection() as conn, conn.cursor() as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]
