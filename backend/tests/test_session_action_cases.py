from __future__ import annotations

import asyncio
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ.setdefault("APP_ENV", "local")

from backend.app.schemas_operations import Action
from backend.app.session_lifecycle import run_session_action
from backend.app.session_measurements import ensure_reset_allowed

SESSION_ID = UUID("a2100000-0000-4000-8000-000000000001")


class _Cursor:
    def __init__(self, state: str, *, updated_at_state: str | None = None) -> None:
        self.state = state
        self.updated_at_state = updated_at_state
        self.queries: list[tuple[str, list[Any]]] = []
        self.row: dict[str, Any] | None = None

    def __enter__(self) -> _Cursor:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def execute(self, query: Any, params: list[Any]) -> None:
        rendered = query.as_string() if hasattr(query, "as_string") else str(query)
        self.queries.append((rendered, params))
        if not rendered.startswith("UPDATE race_sessions"):
            return
        allowed_states = params[-1]
        actual_state = self.updated_at_state if self.updated_at_state is not None else self.state
        if actual_state not in allowed_states:
            self.row = None
            return
        new_state = params[0]
        row: dict[str, Any] = {"id": SESSION_ID, "state": new_state}
        if "started_at=%s" in rendered:
            row["started_at"] = params[1]
            row["ended_at"] = None
        elif "ended_at=%s" in rendered:
            row["started_at"] = "started-before"
            row["ended_at"] = params[1]
        elif "started_at=NULL" in rendered:
            row.update(started_at=None, ended_at=None, safety_car=False)
        else:
            row.update(started_at="started-before", ended_at=None)
        self.row = row

    def fetchone(self) -> dict[str, Any] | None:
        return self.row


class _Connection:
    def __init__(self, cursor: _Cursor) -> None:
        self._cursor = cursor

    def __enter__(self) -> _Connection:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def cursor(self, **_kwargs: Any) -> _Cursor:
        return self._cursor


def _run_action(
    action: str,
    state: str,
    *,
    exists: bool = True,
    allowed_state: str | None = None,
    reset_guard: Any | None = None,
    simulations: dict[str, Any] | None = None,
) -> tuple[Any, _Cursor, list[tuple[Any, ...]], list[tuple[Any, ...]], list[tuple[Any, ...]]]:
    cursor = _Cursor(state, updated_at_state=allowed_state)
    connection_calls: list[tuple[Any, ...]] = []
    clear_calls: list[tuple[Any, ...]] = []
    sync_calls: list[tuple[Any, ...]] = []
    cancel_calls: list[tuple[Any, ...]] = []
    events: list[tuple[Any, ...]] = []
    fetch_calls: list[str] = []

    def fetch_one(query: str, _params: tuple[Any, ...]) -> dict[str, Any] | None:
        fetch_calls.append(query)
        if not exists:
            return None
        if query.startswith("SELECT state"):
            return {"state": state}
        return {"id": SESSION_ID}

    def require_record(row: Any, detail: str) -> Any:
        if row is None:
            raise HTTPException(404, detail)
        return row

    @contextmanager
    def connection() -> Any:
        connection_calls.append(("opened",))
        yield _Connection(cursor)

    def clear_measurements(session_id: UUID) -> None:
        clear_calls.append(("clear", session_id))

    def sync_lifecycle(session_id: UUID, name: str) -> None:
        sync_calls.append(("sync", session_id, name))

    def cancel_reservations(session_id: UUID) -> None:
        cancel_calls.append(("cancel", session_id))

    result = asyncio.run(
        run_session_action(
            SESSION_ID,
            Action(action=action),
            {"id": "admin-1", "role": "ADMIN"},
            require_record,
            fetch_one,
            reset_guard or (lambda _session: None),
            simulations or {},
            connection,
            clear_measurements,
            sync_lifecycle,
            cancel_reservations,
            lambda value: value,
            lambda *args: events.append(args),
        )
    )
    return (
        result,
        cursor,
        connection_calls,
        sync_calls + clear_calls + cancel_calls + fetch_calls,
        events,
    )


@pytest.mark.parametrize(
    ("action", "before", "after"),
    [
        ("start", "SCHEDULED", "ACTIVE"),
        ("pause", "ACTIVE", "PAUSED"),
        ("resume", "PAUSED", "ACTIVE"),
        ("finish", "ACTIVE", "COMPLETED"),
        ("finish", "PAUSED", "COMPLETED"),
        ("reset", "COMPLETED", "SCHEDULED"),
    ],
)
def test_valid_session_actions_update_state_and_emit_state_event(
    action: str, before: str, after: str
) -> None:
    result, cursor, connection_calls, side_effects, events = _run_action(action, before)

    assert result["state"] == after
    assert result["id"] == SESSION_ID
    assert len(connection_calls) == 1
    query, params = cursor.queries[0]
    assert query.startswith("UPDATE race_sessions SET state=%s")
    assert params[0] == after
    if action == "finish":
        assert params[-1] == ["ACTIVE", "PAUSED"]
    elif action == "reset":
        assert params[-1] == ["ACTIVE", "PAUSED", "COMPLETED", "CANCELLED"]
    else:
        assert params[-1] == [before]
    assert events == [(SESSION_ID, "session.state", result)]
    if action == "reset":
        assert result["started_at"] is result["ended_at"] is None
        assert "safety_car=FALSE" in query
    if action == "start":
        assert result["started_at"] is not None
        assert result["ended_at"] is None
    if action == "finish":
        assert result["ended_at"] is not None
    expected_sync = ("sync", SESSION_ID, action)
    if action == "reset":
        assert expected_sync in side_effects
        assert ("clear", SESSION_ID) in side_effects
    elif action == "finish":
        assert expected_sync in side_effects
        assert ("cancel", SESSION_ID) in side_effects
    else:
        assert side_effects == [expected_sync]


@pytest.mark.parametrize(
    ("state", "exists", "expected_status", "expected_detail"),
    [
        ("ACTIVE", False, 404, "Session not found"),
        ("ACTIVE", True, 409, "Invalid session state transition"),
    ],
)
def test_start_rejects_missing_or_invalid_session_state(
    state: str, exists: bool, expected_status: int, expected_detail: str
) -> None:
    with pytest.raises(HTTPException) as error:
        _run_action("start", state, exists=exists)

    assert error.value.status_code == expected_status
    assert error.value.detail == expected_detail


def test_update_race_that_invalidates_transition_returns_conflict_without_event() -> None:
    cursor = _Cursor("ACTIVE", updated_at_state="PAUSED")
    events: list[tuple[Any, ...]] = []

    def fetch_one(query: str, _params: tuple[Any, ...]) -> dict[str, Any]:
        return {"state": "ACTIVE"} if query.startswith("SELECT state") else {"id": SESSION_ID}

    @contextmanager
    def connection() -> Any:
        yield _Connection(cursor)

    def require_record(row: Any, detail: str) -> Any:
        if row is None:
            raise HTTPException(404, detail)
        return row

    with pytest.raises(HTTPException) as error:
        asyncio.run(
            run_session_action(
                SESSION_ID,
                Action(action="pause"),
                {"id": "admin", "role": "ADMIN"},
                require_record,
                fetch_one,
                lambda _session: None,
                {},
                connection,
                lambda _session: None,
                lambda *_args: None,
                lambda _session: None,
                lambda value: value,
                lambda *args: events.append(args),
            )
        )

    assert error.value.status_code == 409
    assert error.value.detail == "Invalid session state transition"
    assert events == []


def test_reset_with_official_penalty_is_rejected_before_mutation() -> None:
    cursor = _Cursor("COMPLETED")
    update_calls: list[str] = []

    class PenaltyDatabase:
        def fetch_one(self, query: str, _params: tuple[Any, ...]) -> dict[str, Any]:
            assert "has_penalties" in query
            return {"has_penalties": True}

    @contextmanager
    def connection() -> Any:
        yield _Connection(cursor)

    def require_record(row: Any, detail: str) -> Any:
        if row is None:
            raise HTTPException(404, detail)
        return row

    def connection_not_expected() -> Any:
        update_calls.append("opened")
        return connection()

    def fetch_one(query: str, _params: tuple[Any, ...]) -> dict[str, Any]:
        return {"state": "COMPLETED"}

    with pytest.raises(HTTPException) as error:
        asyncio.run(
            run_session_action(
                SESSION_ID,
                Action(action="reset"),
                {"id": "admin", "role": "ADMIN"},
                require_record,
                fetch_one,
                lambda session_id: ensure_reset_allowed(session_id, PenaltyDatabase().fetch_one),
                {},
                connection_not_expected,
                lambda _session: None,
                lambda *_args: None,
                lambda _session: None,
                lambda value: value,
                lambda *_args: None,
            )
        )

    assert error.value.status_code == 409
    assert error.value.detail == "A session with official penalties cannot be reset"
    assert update_calls == []


def test_reset_clears_measurements_and_syncs_simulation_after_database_update() -> None:
    result, cursor, _connection_calls, side_effects, events = _run_action("reset", "CANCELLED")

    assert result["state"] == "SCHEDULED"
    assert result["started_at"] is result["ended_at"] is None
    assert ("clear", SESSION_ID) in side_effects
    assert ("sync", SESSION_ID, "reset") in side_effects
    assert events == [(SESSION_ID, "session.state", result)]
