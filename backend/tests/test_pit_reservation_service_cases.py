from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from datetime import timedelta
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
from fastapi import HTTPException
from psycopg.errors import ExclusionViolation, ForeignKeyViolation

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ.setdefault("APP_ENV", "local")

from backend.app.api.pit_write import _check_principal_own_team
from backend.app.pit_reservation_service import run_reserve_pit_auto, run_update_pit_reservation
from backend.app.schemas_operations import AutoReservationIn, ReservationStatus

SESSION_ID = UUID("a2100000-0000-4000-8000-000000000001")
TEAM_ID = UUID("a2100000-0000-4000-8000-000000000002")
DRIVER_ID = UUID("a2100000-0000-4000-8000-000000000003")
RESERVATION_ID = UUID("a2100000-0000-4000-8000-000000000004")


class _Database:
    def __init__(self, row: dict[str, Any] | None = None) -> None:
        self.row = row
        self.calls: list[tuple[str, tuple[Any, ...]]] = []

    def fetch_one(self, query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        self.calls.append((query, params))
        return self.row


class _DatabaseError(Exception):
    def __init__(self, sqlstate: str) -> None:
        super().__init__(f"synthetic database error {sqlstate}")
        self.sqlstate = sqlstate


def _body() -> AutoReservationIn:
    return AutoReservationIn(session_id=SESSION_ID, team_id=TEAM_ID, driver_id=DRIVER_ID)


def _principal_check(team_id: UUID, user: dict[str, Any]) -> None:
    if user["role"] == "PRINCIPAL" and team_id != TEAM_ID:
        raise HTTPException(403, "Principals may reserve pit boxes only for their own team")


def test_auto_reservation_uses_simulation_duration_returns_allocation_and_publishes() -> None:
    database = _Database({"state": "ACTIVE"})
    reservation = {
        "id": str(RESERVATION_ID),
        "session_id": str(SESSION_ID),
        "team_id": str(TEAM_ID),
        "driver_id": str(DRIVER_ID),
        "box_number": 7,
        "status": "RESERVED",
        "allocation_source": "AUTO",
    }
    calls: list[tuple[Any, ...]] = []
    events: list[tuple[Any, ...]] = []

    result = run_reserve_pit_auto(
        _body(),
        {"id": "principal-1", "role": "PRINCIPAL"},
        _principal_check,
        database.fetch_one,
        {str(SESSION_ID): type("Simulation", (), {"rate_hz": 6.0})()},
        lambda *args: calls.append(args) or reservation,
        lambda value: value,
        lambda *args: events.append(args),
    )

    assert result == reservation
    assert database.calls == [
        ("SELECT state FROM race_sessions WHERE id=%s", (SESSION_ID,))
    ]
    assert calls == [(SESSION_ID, TEAM_ID, DRIVER_ID, timedelta(seconds=0.6))]
    assert events == [(SESSION_ID, "pit.update", reservation)]


def test_auto_reservation_requires_own_team_before_session_lookup() -> None:
    other_team = UUID("a2100000-0000-4000-8000-000000000099")
    database = _Database({"state": "ACTIVE"})
    allocations: list[tuple[Any, ...]] = []
    user = {"id": "principal-1", "role": "PRINCIPAL"}

    with pytest.raises(HTTPException) as error:
        run_reserve_pit_auto(
            AutoReservationIn(session_id=SESSION_ID, team_id=other_team),
            user,
            lambda team_id, principal: _check_principal_own_team(
                team_id, principal, _Database(None)
            ),
            database.fetch_one,
            {},
            lambda *args: allocations.append(args),
            lambda value: value,
            lambda *_args: None,
        )

    assert error.value.status_code == 403
    assert error.value.detail == "Principals may reserve pit boxes only for their own team"
    assert database.calls == []
    assert allocations == []


@pytest.mark.parametrize(
    ("session", "status", "expected_status", "expected_detail"),
    [
        (None, None, 404, "Session not found"),
        ({"state": "SCHEDULED"}, None, 409, "Pit reservations require an active or paused session"),
        ({"state": "COMPLETED"}, None, 409, "Pit reservations require an active or paused session"),
    ],
)
def test_auto_reservation_requires_existing_active_or_paused_session(
    session: dict[str, Any] | None,
    status: None,
    expected_status: int,
    expected_detail: str,
) -> None:
    database = _Database(session)
    allocations: list[tuple[Any, ...]] = []

    with pytest.raises(HTTPException) as error:
        run_reserve_pit_auto(
            _body(),
            {"role": "ADMIN"},
            lambda *_args: None,
            database.fetch_one,
            {},
            lambda *args: allocations.append(args),
            lambda value: value,
            lambda *_args: None,
        )

    assert error.value.status_code == expected_status
    assert error.value.detail == expected_detail
    assert allocations == []
    assert len(database.calls) == 1


@pytest.mark.parametrize(
    ("sqlstate", "expected_status", "expected_detail"),
    [
        ("P0002", 409, "The event has no pit boxes"),
        ("23514", 422, "Driver must be an eligible member of the team for this session"),
        ("23505", 409, "Driver already has an open pit reservation for this session"),
        ("23P01", 409, "Driver or pit box already has a conflicting reservation"),
        ("23503", 404, "Session, team, driver, or pit box not found"),
    ],
)
def test_auto_reservation_maps_allocation_conflicts_and_constraints(
    sqlstate: str, expected_status: int, expected_detail: str
) -> None:
    database = _Database({"state": "PAUSED"})
    events: list[tuple[Any, ...]] = []

    def unavailable(*_args: Any) -> None:
        if sqlstate == "23P01":
            raise ExclusionViolation("synthetic exclusion conflict")
        if sqlstate == "23503":
            raise ForeignKeyViolation("synthetic missing reference")
        raise _DatabaseError(sqlstate)

    with pytest.raises(HTTPException) as error:
        run_reserve_pit_auto(
            _body(),
            {"role": "ADMIN"},
            lambda *_args: None,
            database.fetch_one,
            {},
            unavailable,
            lambda value: value,
            lambda *args: events.append(args),
        )

    assert error.value.status_code == expected_status
    assert error.value.detail == expected_detail
    assert events == []


class _Cursor:
    def __init__(self, reservation: dict[str, Any] | None) -> None:
        self.reservation = reservation
        self.queries: list[tuple[str, tuple[Any, ...]]] = []

    def __enter__(self) -> _Cursor:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def execute(self, query: str, params: tuple[Any, ...] = ()) -> None:
        self.queries.append((query, params))
        if query.startswith("UPDATE pit_reservations"):
            self.reservation = {**self.reservation, "status": params[0]}

    def fetchone(self) -> dict[str, Any] | None:
        return self.reservation


class _Connection:
    def __init__(self, cursor: _Cursor) -> None:
        self._cursor = cursor

    def __enter__(self) -> _Connection:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def cursor(self, **_kwargs: Any) -> _Cursor:
        return self._cursor


def _connection_factory(cursor: _Cursor) -> Any:
    @contextmanager
    def connection() -> Any:
        yield _Connection(cursor)

    return connection


def test_update_changes_reserved_status_and_publishes_updated_reservation() -> None:
    row = {
        "id": str(RESERVATION_ID),
        "status": "RESERVED",
        "principal_user_id": "principal-1",
        "session_id": SESSION_ID,
    }
    cursor = _Cursor(row)
    events: list[tuple[Any, ...]] = []

    result = run_update_pit_reservation(
        RESERVATION_ID,
        ReservationStatus(status="COMPLETED"),
        {"id": "admin-1", "role": "ADMIN"},
        _connection_factory(cursor),
        lambda value: value,
        lambda *args: events.append(args),
    )

    assert result["status"] == "COMPLETED"
    assert cursor.queries[1] == (
        "UPDATE pit_reservations SET status=%s WHERE id=%s",
        ("COMPLETED", RESERVATION_ID),
    )
    assert events == [(SESSION_ID, "pit.update", result)]


@pytest.mark.parametrize(
    ("reservation", "user", "expected_status", "expected_detail"),
    [
        (None, {"id": "admin", "role": "ADMIN"}, 404, "Pit reservation not found"),
        (
            {"status": "RESERVED", "principal_user_id": "different", "session_id": SESSION_ID},
            {"id": "principal-1", "role": "PRINCIPAL"},
            403,
            "Principals may update reservations only for their own team",
        ),
        (
            {"status": "CANCELLED", "principal_user_id": "principal-1", "session_id": SESSION_ID},
            {"id": "principal-1", "role": "PRINCIPAL"},
            409,
            "Pit reservation is already closed",
        ),
    ],
)
def test_update_rejects_missing_unauthorized_or_closed_reservations(
    reservation: dict[str, Any] | None,
    user: dict[str, Any],
    expected_status: int,
    expected_detail: str,
) -> None:
    cursor = _Cursor(reservation)
    events: list[tuple[Any, ...]] = []

    with pytest.raises(HTTPException) as error:
        run_update_pit_reservation(
            RESERVATION_ID,
            ReservationStatus(status="CANCELLED"),
            user,
            _connection_factory(cursor),
            lambda value: value,
            lambda *args: events.append(args),
        )

    assert error.value.status_code == expected_status
    assert error.value.detail == expected_detail
    assert all(not query.startswith("UPDATE pit_reservations") for query, _ in cursor.queries)
    assert events == []
