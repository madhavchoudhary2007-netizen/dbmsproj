from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from urllib.parse import urlparse
from uuid import UUID, uuid4

import psycopg
import pytest

DEFAULT_POINTS_SYSTEM = UUID("00000000-0000-0000-0000-000000000001")
SEASON = 2098

Standing = tuple[int, str, int, int, int]


def _guarded_fixture_url() -> str:
    url = os.environ.get("SHOWCASE_TEST_DATABASE_URL")
    if not url:
        pytest.fail(
            "SHOWCASE_TEST_DATABASE_URL must explicitly name the disposable apexgrid database"
        )

    try:
        parsed = urlparse(url)
        safe_target = (
            parsed.scheme in {"postgres", "postgresql"}
            and parsed.hostname in {"127.0.0.1", "localhost"}
            and parsed.port == 15432
            and parsed.path == "/apexgrid"
        )
    except ValueError:
        safe_target = False
    if not safe_target:
        pytest.fail(
            "SHOWCASE_TEST_DATABASE_URL must target apexgrid on 127.0.0.1 or localhost:15432"
        )
    return url


@contextmanager
def _rolled_back_connection() -> Iterator[psycopg.Connection[object]]:
    url = _guarded_fixture_url()
    conn = psycopg.connect(url, connect_timeout=3)
    try:
        yield conn
    finally:
        conn.rollback()
        conn.close()


@dataclass(frozen=True)
class Result:
    driver: str
    position: int
    classified: bool = True
    pole: bool = False
    fastest_lap: bool = False


def _driver_ids(cur: psycopg.Cursor[object], count: int) -> list[str]:
    cur.execute("SELECT id::text FROM drivers ORDER BY id LIMIT %s", (count,))
    ids = [str(row[0]) for row in cur.fetchall()]
    if len(ids) < count:
        pytest.fail(f"disposable apexgrid seed must provide at least {count} drivers")
    return ids


def _circuit_id(cur: psycopg.Cursor[object]) -> UUID:
    cur.execute("SELECT id FROM circuits ORDER BY id LIMIT 1")
    row = cur.fetchone()
    if row is None:
        pytest.fail("disposable apexgrid seed must provide a circuit")
    return row[0]


def _insert_points_system(cur: psycopg.Cursor[object], positions: dict[int, int]) -> UUID:
    cur.execute(
        "INSERT INTO points_systems(name,is_default) VALUES (%s,false) RETURNING id",
        (f"standings-tiebreak-{uuid4().hex}",),
    )
    system_id = cur.fetchone()[0]
    cur.executemany(
        "INSERT INTO points_system_positions(system_id,position,points) VALUES (%s,%s,%s)",
        [(system_id, position, points) for position, points in sorted(positions.items())],
    )
    return system_id


def _seed_championship(
    cur: psycopg.Cursor[object],
    circuit_id: UUID,
    sessions: tuple[tuple[Result, ...], ...],
    points_system_id: UUID = DEFAULT_POINTS_SYSTEM,
) -> UUID:
    cur.execute(
        "INSERT INTO championships(name,season,points_system_id) VALUES (%s,%s,%s) RETURNING id",
        (f"standings-tiebreak-{uuid4().hex}", SEASON, points_system_id),
    )
    championship_id = cur.fetchone()[0]
    for round_number, results in enumerate(sessions, start=1):
        cur.execute(
            "INSERT INTO race_events(championship_id,circuit_id,round_number,name,start_date) "
            "VALUES (%s,%s,%s,%s,now()) RETURNING id",
            (championship_id, circuit_id, round_number, f"tiebreak round {round_number}"),
        )
        event_id = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO race_sessions(event_id,session_type,state,scheduled_at,started_at,"
            "ended_at) "
            "VALUES (%s,'RACE','COMPLETED',now(),now(),now()) RETURNING id",
            (event_id,),
        )
        session_id = cur.fetchone()[0]
        cur.executemany(
            "INSERT INTO session_results(session_id,driver_id,position,classified,pole,"
            "fastest_lap) VALUES (%s,%s,%s,%s,%s,%s)",
            [
                (
                    session_id,
                    UUID(result.driver),
                    result.position,
                    result.classified,
                    result.pole,
                    result.fastest_lap,
                )
                for result in results
            ],
        )
    return championship_id


def _recalculate_and_read(cur: psycopg.Cursor[object], championship_id: UUID) -> list[Standing]:
    cur.execute("SELECT recalculate_standings(%s)", (championship_id,))
    return _read_standings(cur, championship_id)


def _read_standings(cur: psycopg.Cursor[object], championship_id: UUID) -> list[Standing]:
    cur.execute(
        "SELECT rank, driver_id::text, points, wins, podiums FROM driver_standings "
        "WHERE championship_id=%s ORDER BY rank",
        (championship_id,),
    )
    return [(int(r[0]), str(r[1]), int(r[2]), int(r[3]), int(r[4])) for r in cur.fetchall()]


def test_equal_points_are_broken_by_wins() -> None:
    with _rolled_back_connection() as conn, conn.cursor() as cur:
        low, high = sorted(_driver_ids(cur, 2))
        circuit_id = _circuit_id(cur)
        championship_id = _seed_championship(
            cur,
            circuit_id,
            (
                (Result(high, 1), Result(low, 2)),
                (Result(high, 10), Result(low, 6)),
            ),
        )
        actual = _recalculate_and_read(cur, championship_id)

    # high: 25 + 1 = 26 points, 1 win, 1 podium
    # low:  18 + 8 = 26 points, 0 wins, 1 podium
    assert actual == [
        (1, high, 26, 1, 1),
        (2, low, 26, 0, 1),
    ]


def test_equal_points_and_wins_are_broken_by_podiums() -> None:
    with _rolled_back_connection() as conn, conn.cursor() as cur:
        low, high = sorted(_driver_ids(cur, 2))
        circuit_id = _circuit_id(cur)
        championship_id = _seed_championship(
            cur,
            circuit_id,
            (
                (Result(high, 1), Result(low, 4)),
                (Result(high, 2), Result(low, 1)),
                (Result(high, 9), Result(low, 6)),
            ),
        )
        actual = _recalculate_and_read(cur, championship_id)

    # high: 25 + 18 + 2 = 45 points, 1 win, 2 podiums
    # low:  12 + 25 + 8 = 45 points, 1 win, 1 podium
    assert actual == [
        (1, high, 45, 1, 2),
        (2, low, 45, 1, 1),
    ]


def test_full_tie_is_broken_by_driver_id_ascending() -> None:
    with _rolled_back_connection() as conn, conn.cursor() as cur:
        d0, d1, d2 = sorted(_driver_ids(cur, 3))
        circuit_id = _circuit_id(cur)
        championship_id = _seed_championship(
            cur,
            circuit_id,
            (
                (Result(d2, 3), Result(d1, 2), Result(d0, 1)),
                (Result(d0, 3), Result(d2, 2), Result(d1, 1)),
                (Result(d1, 3), Result(d0, 2), Result(d2, 1)),
            ),
        )
        actual = _recalculate_and_read(cur, championship_id)

    # Every driver: 15 + 18 + 25 = 58 points, 1 win, 3 podiums.
    assert actual == [
        (1, d0, 58, 1, 3),
        (2, d1, 58, 1, 3),
        (3, d2, 58, 1, 3),
    ]


def test_unclassified_result_earns_no_points_win_or_podium() -> None:
    with _rolled_back_connection() as conn, conn.cursor() as cur:
        low, high = sorted(_driver_ids(cur, 2))
        circuit_id = _circuit_id(cur)
        championship_id = _seed_championship(
            cur,
            circuit_id,
            (
                (
                    Result(high, 1, classified=False, pole=True, fastest_lap=True),
                    Result(low, 2),
                ),
                (
                    Result(high, 4),
                    Result(low, 1, classified=False, pole=True, fastest_lap=True),
                ),
            ),
        )
        actual = _recalculate_and_read(cur, championship_id)

    # high: unclassified P1 scores nothing; classified P4 = 12 points, no podium.
    # low:  classified P2 = 18 points, 1 podium; unclassified P1 scores nothing.
    assert actual == [
        (1, low, 18, 0, 1),
        (2, high, 12, 0, 0),
    ]


def test_configured_points_system_changes_totals() -> None:
    with _rolled_back_connection() as conn, conn.cursor() as cur:
        d0, d1, d2 = sorted(_driver_ids(cur, 3))
        circuit_id = _circuit_id(cur)
        configured_system = _insert_points_system(cur, {1: 10, 2: 8, 3: 6})
        championship_id = _seed_championship(
            cur,
            circuit_id,
            (
                (
                    Result(d0, 1, pole=True, fastest_lap=True),
                    Result(d1, 2, fastest_lap=True),
                    Result(d2, 3),
                ),
                (Result(d0, 4),),
            ),
            points_system_id=configured_system,
        )
        actual = _recalculate_and_read(cur, championship_id)

    # Configured system: P1=10, P2=8, P3=6, P4 not configured (0).
    # d0: 10 + pole 1 + fastest lap 1 = 12 points, 1 win, 1 podium; P4 adds nothing.
    # d1: 8 + fastest lap 1 = 9 points, 0 wins, 1 podium.
    # d2: 6 points, 0 wins, 1 podium.
    assert actual == [
        (1, d0, 12, 1, 1),
        (2, d1, 9, 0, 1),
        (3, d2, 6, 0, 1),
    ]


def test_recalculate_standings_is_idempotent() -> None:
    with _rolled_back_connection() as conn, conn.cursor() as cur:
        d0, d1, d2 = sorted(_driver_ids(cur, 3))
        circuit_id = _circuit_id(cur)
        championship_id = _seed_championship(
            cur,
            circuit_id,
            (
                (Result(d2, 1, pole=True), Result(d0, 2, fastest_lap=True), Result(d1, 3)),
                (Result(d0, 1), Result(d1, 2), Result(d2, 4, classified=False)),
                (
                    Result(d1, 1, fastest_lap=True),
                    Result(d2, 2),
                    Result(d0, 3, classified=False),
                ),
            ),
        )
        first = _recalculate_and_read(cur, championship_id)
        second = _recalculate_and_read(cur, championship_id)

    # d0: 19 + 25 + 0 = 44 points, 1 win, 2 podiums.
    # d1: 15 + 18 + 26 = 59 points, 1 win, 3 podiums.
    # d2: 26 + 0 + 18 = 44 points, 1 win, 2 podiums.
    expected = [
        (1, d1, 59, 1, 3),
        (2, d0, 44, 1, 2),
        (3, d2, 44, 1, 2),
    ]
    assert first == expected
    assert second == first
