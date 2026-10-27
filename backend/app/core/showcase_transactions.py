from __future__ import annotations

import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from contextlib import AbstractContextManager
from typing import Any
from uuid import UUID, uuid4

from psycopg import Connection

from ..database import DatabaseRow

_ISOLATION_SQL = {
    "read_committed": "READ COMMITTED",
    "repeatable_read": "REPEATABLE READ",
    "serializable": "SERIALIZABLE",
}
_TIMEOUT_SQL = ("SET LOCAL statement_timeout = '8s'", "SET LOCAL lock_timeout = '5s'")


def _set_timeouts(conn: Connection[DatabaseRow]) -> None:
    for statement in _TIMEOUT_SQL:
        conn.execute(statement)


def _row_value(row: Any, key: str, index: int = 0) -> Any:
    if isinstance(row, dict):
        return row[key]
    return row[index]


def _create_demo_circuits(conn: Connection[DatabaseRow], ids: tuple[UUID, ...]) -> None:
    with conn.transaction():
        _set_timeouts(conn)
        for index, user_id in enumerate(ids):
            marker = f"dbms-demo-{user_id}"
            conn.execute(
                "INSERT INTO circuits (id, name, country, length_km) VALUES (%s, %s, 'DEMO', %s)",
                (user_id, marker, 1.000 if index == 0 else 1.500),
            )


def _delete_demo_circuits(conn: Connection[DatabaseRow], ids: tuple[UUID, ...]) -> None:
    with conn.transaction():
        _set_timeouts(conn)
        conn.execute("DELETE FROM circuits WHERE id = ANY(%s)", (list(ids),))


def run_isolation_demo(
    connection: Callable[[], AbstractContextManager[Connection[DatabaseRow]]], level: str
) -> dict[str, Any]:
    isolation_sql = _ISOLATION_SQL[level]
    user_id = uuid4()
    reads: list[int] = []
    timeline: list[dict[str, Any]] = []
    with connection() as first:
        _create_demo_circuits(first, (user_id,))
        try:
            with first.transaction():
                first.execute(f"SET TRANSACTION ISOLATION LEVEL {isolation_sql}")
                _set_timeouts(first)
                initial = first.execute(
                    "SELECT (length_km * 1000)::integer AS balance FROM circuits WHERE id = %s",
                    (user_id,),
                ).fetchone()
                reads.append(int(_row_value(initial, "balance")))
                timeline.append(
                    {"time": 1, "tx": "T1", "action": f"BEGIN ISOLATION LEVEL {isolation_sql}"}
                )
                timeline.append({"time": 2, "tx": "T1", "action": f"SELECT balance -> {reads[0]}"})

                with connection() as second, second.transaction():
                    second.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")
                    _set_timeouts(second)
                    second.execute(
                        "UPDATE circuits SET length_km = 1.500 WHERE id = %s", (user_id,)
                    )
                timeline.append({"time": 3, "tx": "T2", "action": "UPDATE demo row and COMMIT"})

                reread = first.execute(
                    "SELECT (length_km * 1000)::integer AS balance FROM circuits WHERE id = %s",
                    (user_id,),
                ).fetchone()
                reads.append(int(_row_value(reread, "balance")))
                timeline.append({"time": 4, "tx": "T1", "action": f"SELECT balance -> {reads[1]}"})
            anomaly = reads[0] != reads[1]
            anomaly_type = "Non-repeatable Read (Fuzzy Read)" if anomaly else None
            result = {
                "level": level,
                "observed_reads": [
                    {"step": "T1: Initial read", "balance": reads[0]},
                    {"step": "T1: Read after T2 commit", "balance": reads[1]},
                ],
                "anomaly_detected": anomaly,
                "anomaly_type": anomaly_type,
                "timeline": timeline,
            }
        finally:
            _delete_demo_circuits(first, (user_id,))
    return result


def run_deadlock_demo(
    connection: Callable[[], AbstractContextManager[Connection[DatabaseRow]]],
) -> dict[str, Any]:
    ids = (uuid4(), uuid4())
    barrier = threading.Barrier(2)

    def lock_then_cross(
        conn: Connection[DatabaseRow], label: str, own: UUID, other: UUID
    ) -> dict[str, Any]:
        try:
            with conn.transaction():
                conn.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")
                _set_timeouts(conn)
                conn.execute("SELECT id FROM circuits WHERE id = %s FOR UPDATE", (own,))
                barrier.wait(timeout=5)
                conn.execute("UPDATE circuits SET length_km = 0.999 WHERE id = %s", (other,))
            return {"transaction": label, "sqlstate": None}
        except Exception as exc:
            return {"transaction": label, "sqlstate": getattr(exc, "sqlstate", None)}

    with connection() as first, connection() as second:
        _create_demo_circuits(first, ids)
        try:
            with ThreadPoolExecutor(max_workers=2) as executor:
                first_future = executor.submit(lock_then_cross, first, "T1", ids[0], ids[1])
                second_future = executor.submit(lock_then_cross, second, "T2", ids[1], ids[0])
                outcomes = [first_future.result(timeout=12), second_future.result(timeout=12)]
            deadlock = next((item for item in outcomes if item["sqlstate"] == "40P01"), None)
            if deadlock is None:
                raise RuntimeError("PostgreSQL did not report a deadlock")
            return {
                "aborted_transaction": deadlock["transaction"],
                "sqlstate": deadlock["sqlstate"],
                "error_message": (
                    "PostgreSQL detected a deadlock in the controlled demo transactions"
                ),
                "details": {
                    "transaction_1": {
                        "query": "UPDATE circuits SET length_km=0.999 for the second demo row",
                        "holding": "row lock on first demo row",
                        "waiting_for": "row lock on second demo row",
                    },
                    "transaction_2": {
                        "query": "UPDATE circuits SET length_km=0.999 for the first demo row",
                        "holding": "row lock on second demo row",
                        "waiting_for": "row lock on first demo row",
                    },
                    "resolution": (
                        f"PostgreSQL aborted {deadlock['transaction']} "
                        f"with SQLSTATE {deadlock['sqlstate']}"
                    ),
                    "observed_sqlstates": [item["sqlstate"] for item in outcomes],
                },
            }
        finally:
            barrier.abort()
            _delete_demo_circuits(first, ids)
