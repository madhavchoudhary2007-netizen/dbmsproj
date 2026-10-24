import os
from datetime import UTC, datetime, timedelta
from urllib.parse import urlparse
from uuid import UUID

import pytest

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:
    psycopg = None
    dict_row = None

from app import analytics_repository

DATABASE_URL = os.getenv("DATABASE_URL")
parsed_url = urlparse(DATABASE_URL or "")
pytestmark = pytest.mark.skipif(not DATABASE_URL or psycopg is None, reason="DB required")


@pytest.fixture
def disposable_db():
    if parsed_url.hostname not in {"localhost", "127.0.0.1", "::1"} or parsed_url.port != 15432:
        pytest.skip("disposable checks require loopback PostgreSQL on port 15432")
    conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
    with conn.cursor() as cur:
        cur.execute(
            "CREATE TEMP TABLE circuits (id uuid PRIMARY KEY, name text NOT NULL);"
            "CREATE TEMP TABLE race_events (id uuid PRIMARY KEY, name text NOT NULL, "
            "circuit_id uuid NOT NULL);"
            "CREATE TEMP TABLE race_sessions (id uuid PRIMARY KEY, event_id uuid NOT NULL, "
            "session_type text NOT NULL, state text NOT NULL, scheduled_at timestamptz NOT NULL);"
        )
    try:
        yield conn
    finally:
        conn.rollback()
        conn.close()


def _add(conn, n, name, kind, state, when):
    ids = [UUID(f"{i:08d}-0000-0000-0000-{n:012d}") for i in (1, 2, 3)]
    conn.execute("INSERT INTO circuits VALUES (%s, %s)", (ids[2], "Harbor Ring"))
    conn.execute("INSERT INTO race_events VALUES (%s, %s, %s)", (ids[1], name, ids[2]))
    conn.execute(
        "INSERT INTO race_sessions VALUES (%s, %s, %s, %s, %s)", (ids[0], ids[1], kind, state, when)
    )
    return ids[0]


def _patch_fetch(monkeypatch, conn):
    old = iter([{"count": 2}, {"count": 3}, {"count": 1}, {"count": 24}, None])
    calls = []

    def fetch_one(sql, params=()):
        calls.append(sql)
        if len(calls) <= 5:
            return next(old)
        row = conn.execute(sql, params).fetchone()
        return dict(row) if row else None

    monkeypatch.setattr(analytics_repository, "fetch_one", fetch_one)
    return calls


def test_next_event_orders_future_ties_by_session_id(monkeypatch, disposable_db):
    now = datetime.now(UTC) + timedelta(minutes=5)
    _add(disposable_db, 3, "later", "RACE", "SCHEDULED", now + timedelta(minutes=1))
    _add(disposable_db, 2, "higher", "RACE", "SCHEDULED", now)
    expected = _add(disposable_db, 1, "lower", "RACE", "SCHEDULED", now)
    calls = _patch_fetch(monkeypatch, disposable_db)

    dashboard = analytics_repository.get_dashboard_data()

    assert dashboard["next_event"]["session_id"] == expected
    assert dashboard["next_event"]["name"] == "lower"
    assert set(dashboard["next_event"]) == set(
        ("id", "name", "session_id", "scheduled_at", "circuit_name")
    )
    assert dashboard["next_event"]["id"] == UUID("20000000-0000-0000-0000-000000000001")
    assert dashboard["next_event"]["scheduled_at"] == now
    assert dashboard["next_event"]["circuit_name"] == "Harbor Ring"
    assert len(calls) == 6


def test_next_event_excludes_past_non_race_and_terminal_sessions(monkeypatch, disposable_db):
    now = datetime.now(UTC)
    for n, name, kind, state, delta in (
        (1, "past", "RACE", "SCHEDULED", -1),
        (2, "practice", "PRACTICE", "SCHEDULED", 1),
        (3, "completed", "RACE", "COMPLETED", 2),
        (4, "cancelled", "RACE", "CANCELLED", 3),
        (5, "active", "RACE", "ACTIVE", 4),
        (6, "paused", "RACE", "PAUSED", 5),
        (7, "qualifying", "QUALIFYING", "SCHEDULED", 6),
    ):
        _add(disposable_db, n, name, kind, state, now + timedelta(minutes=delta))
    calls = _patch_fetch(monkeypatch, disposable_db)

    dashboard = analytics_repository.get_dashboard_data()

    assert dashboard["next_event"] is None
    assert len(calls) == 6
