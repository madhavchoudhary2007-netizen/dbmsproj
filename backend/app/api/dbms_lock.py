from __future__ import annotations

import random
import threading
import time
from _thread import LockType
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from contextlib import AbstractContextManager
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any, cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from psycopg import Connection

from ..core.request_database import DatabaseRow, DatabaseSession
from .laps import admin, get_race_db

router = APIRouter()
dbms_lock_router = router

admin_dependency = Depends(admin)
_default_lock_demo_guard = threading.Lock()


def _resolve_db(database: DatabaseSession | None = None) -> DatabaseSession:
    if database is not None:
        return database
    import sys

    from .. import database as db_module

    main_module = sys.modules.get("backend.app.main")
    cur_fetch_one = (
        getattr(main_module, "fetch_one", db_module.fetch_one)
        if main_module is not None
        else db_module.fetch_one
    )
    cur_fetch_all = (
        getattr(main_module, "fetch_all", db_module.fetch_all)
        if main_module is not None
        else db_module.fetch_all
    )
    from .laps import _MonkeypatchedDatabaseSession

    return _MonkeypatchedDatabaseSession(cur_fetch_one, cur_fetch_all)


def _get_connection(
    database: DatabaseSession | None = None,
) -> AbstractContextManager[Connection[DatabaseRow]]:
    if database is not None and getattr(database, "pool", None) is not None:
        pool = database.pool
        if not pool.closed:
            return cast(AbstractContextManager[Connection[DatabaseRow]], pool.connection())
    import sys

    from .. import database as db_module

    main_module = sys.modules.get("backend.app.main")
    conn_fn = (
        getattr(main_module, "connection", db_module.connection)
        if main_module is not None
        else db_module.connection
    )
    return cast(AbstractContextManager[Connection[DatabaseRow]], conn_fn())


def _resolve_lock_demo_guard() -> LockType:
    import sys

    main_module = sys.modules.get("backend.app.main")
    if main_module is not None and hasattr(main_module, "lock_demo_guard"):
        return cast(LockType, main_module.lock_demo_guard)
    return _default_lock_demo_guard


def _resolve_lock_demo_helpers(
    database: DatabaseSession | None = None,
) -> tuple[Callable[..., dict[str, Any]], Callable[..., None]]:
    import sys

    main_module = sys.modules.get("backend.app.main")
    competing = (
        getattr(main_module, "_competing_lock_demo_reservation", None)
        if main_module is not None
        else None
    )
    cleanup = getattr(main_module, "_cleanup_lock_demo", None) if main_module is not None else None
    if competing is not None and cleanup is not None:
        return competing, cleanup

    from ..core.lock_demo import create_lock_demo_helpers

    return create_lock_demo_helpers(lambda: _get_connection(database))


def _resolve_recalculate() -> Callable[..., Any]:
    import sys

    main_module = sys.modules.get("backend.app.main")
    if main_module is not None and hasattr(main_module, "recalculate"):
        return cast(Callable[..., Any], main_module.recalculate)
    from .race_operation_routes import recalculate

    return recalculate


def _run_lock_demo(
    fetch_one: Callable[..., DatabaseRow | None],
    connection: Callable[[], AbstractContextManager[Connection[DatabaseRow]]],
    _competing_lock_demo_reservation: Callable[..., dict[str, Any]],
    _cleanup_lock_demo: Callable[..., None],
    lock_demo_guard: LockType,
) -> dict[str, Any]:
    """Demonstrate two real transactions contending on a pit box row."""
    if not lock_demo_guard.acquire(blocking=False):
        raise HTTPException(409, "A lock demonstration is already running")
    first_reservation_id = None
    second_reservation_id = None
    future = None
    worker = None
    outcome = None
    try:
        target = fetch_one(
            "SELECT b.id AS pit_box_id,s.id AS session_id,t.id AS team_id FROM pit_boxes b JO"
            "IN race_sessions s ON s.event_id=b.event_id CROSS JOIN teams t ORDER BY b.number"
            ",s.scheduled_at LIMIT 1"
        )
        if target is None or not target:
            raise HTTPException(503, "Seeded pit box, session, or team is unavailable")
        starts_at = datetime.now(UTC) + timedelta(
            # Non-security randomized demonstration reservation window.
            days=3650 + random.randrange(10000),  # noqa: S311
            seconds=random.randrange(86400),  # noqa: S311
        )
        ends_at = starts_at + timedelta(minutes=2)
        ready = threading.Event()
        competitor = {"pid": None}
        worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="apexgrid-lock-demo")

        wait_observed = False
        with connection() as owner, owner.transaction():
            owner.execute("SET LOCAL lock_timeout='8s'")
            reservation = owner.execute(
                "SELECT reserve_pit_box(%s,%s,%s,%s,%s) AS id",
                (
                    target["pit_box_id"],
                    target["session_id"],
                    target["team_id"],
                    starts_at,
                    ends_at,
                ),
            ).fetchone()
            if reservation is None:
                raise TypeError("'NoneType' object is not subscriptable")
            first_reservation_id = reservation["id"]
            future = worker.submit(
                _competing_lock_demo_reservation, target, starts_at, ends_at, ready, competitor
            )
            if not ready.wait(timeout=2):
                raise HTTPException(503, "Second database connection did not become ready")
            # The worker publishes its backend PID just before it issues the blocking function.
            # Observe the database wait itself before committing the first reservation.
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                lock_row = owner.execute(
                    "SELECT wait_event_type FROM pg_stat_activity WHERE pid=%s",
                    (competitor["pid"],),
                ).fetchone()
                if lock_row and lock_row.get("wait_event_type") == "Lock":
                    wait_observed = True
                    break
                time.sleep(0.025)
        try:
            outcome = future.result(timeout=9) if future else None
        except FutureTimeout as exc:
            raise HTTPException(504, "Competing reservation did not finish before timeout") from exc
        second_reservation_id = outcome.get("reservation_id") if outcome else None
        if not outcome or outcome["outcome"] != "rejected" or outcome["sqlstate"] != "23P01":
            raise HTTPException(500, "Overlapping reservation was not rejected as expected")
        if not wait_observed:
            raise HTTPException(
                503, "Database did not report the competitor waiting on the pit box lock"
            )
        return {
            "pit_box_id": str(target["pit_box_id"]),
            "lock_wait_observed": True,
            "lock_wait_ms": outcome["wait_ms"],
            "first_reservation": "committed",
            "overlapping_reservation": "rejected",
            "rejection_sqlstate": outcome["sqlstate"],
        }
    finally:
        try:
            _cleanup_lock_demo(worker, future, outcome, first_reservation_id, second_reservation_id)
        finally:
            lock_demo_guard.release()


@router.post("/api/dbms/lock-demo")
def dbms_lock_demo(
    user: Annotated[dict[str, Any] | None, admin_dependency] = None,
    database: Annotated[DatabaseSession | None, Depends(get_race_db)] = None,
) -> dict[str, Any]:
    """Demonstrate two real transactions contending on a pit box row."""
    db = _resolve_db(database)
    competing, cleanup = _resolve_lock_demo_helpers(database)
    guard = _resolve_lock_demo_guard()
    return _run_lock_demo(
        db.fetch_one,
        lambda: _get_connection(database),
        competing,
        cleanup,
        guard,
    )


@router.post("/api/dbms/recalculate")
def dbms_recalculate(
    championship_id: UUID,
    user: Annotated[dict[str, Any] | None, admin_dependency] = None,
) -> Any:
    recalc = _resolve_recalculate()
    return recalc(championship_id, user)


dbms_lock_handlers: dict[str, Callable[..., Any]] = {
    "dbms_lock_demo": dbms_lock_demo,
    "dbms_recalculate": dbms_recalculate,
}


def create_dbms_lock_router(
    fetch_one: Callable[..., DatabaseRow | None],
    connection: Callable[[], AbstractContextManager[Connection[DatabaseRow]]],
    _competing_lock_demo_reservation: Callable[..., dict[str, Any]],
    _cleanup_lock_demo: Callable[..., None],
    lock_demo_guard: LockType,
    recalculate: Callable[..., Any],
    admin_dependency: Any,
) -> tuple[APIRouter, dict[str, Callable[..., Any]]]:
    legacy_router = APIRouter()

    @legacy_router.post("/api/dbms/lock-demo")
    def dbms_lock_demo(user: Any = admin_dependency) -> dict[str, Any]:
        """Demonstrate two real transactions contending on a pit box row."""
        return _run_lock_demo(
            fetch_one,
            connection,
            _competing_lock_demo_reservation,
            _cleanup_lock_demo,
            lock_demo_guard,
        )

    @legacy_router.post("/api/dbms/recalculate")
    def dbms_recalculate(championship_id: UUID, user: Any = admin_dependency) -> Any:
        return recalculate(championship_id, user)

    handlers: dict[str, Callable[..., Any]] = {
        "dbms_lock_demo": dbms_lock_demo,
        "dbms_recalculate": dbms_recalculate,
    }
    return legacy_router, handlers
