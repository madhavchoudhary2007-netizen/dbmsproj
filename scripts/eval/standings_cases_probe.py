"""Run real standings cases against a freshly owned disposable database."""

from __future__ import annotations

import importlib
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID

import psycopg

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
owned_acceptance = importlib.import_module("scripts.eval.run_owned_acceptance")
race_probe = importlib.import_module("scripts.eval.standings_race_probe")

OWNERSHIP_ENV_KEYS = race_probe.OWNERSHIP_ENV_KEYS
DEFAULT_POINTS_SYSTEM = UUID("00000000-0000-0000-0000-000000000001")


class ProbeFailure(RuntimeError):
    """A safe probe error that does not expose connection details."""


@dataclass(frozen=True)
class RaceResult:
    driver: str
    position: int
    classified: bool = True
    pole: bool = False
    fastest_lap: bool = False


@dataclass(frozen=True)
class StandingsCase:
    name: str
    sessions: tuple[tuple[RaceResult, ...], ...]
    expected: tuple[tuple[str, int, int, int], ...]
    configured_points: tuple[tuple[int, int], ...] = ()


def standings_cases(driver_ids: list[str]) -> tuple[StandingsCase, ...]:
    """Explicit behavioral cases and expected (driver, points, wins, podiums)."""
    if len(driver_ids) < 3:
        raise ProbeFailure("Standings cases require at least three seeded drivers")
    a, b, c = driver_ids[:3]
    low, high = sorted((a, b))
    return (
        StandingsCase(
            "points_primary",
            ((RaceResult(a, 1), RaceResult(b, 2)),),
            ((a, 25, 1, 1), (b, 18, 0, 1)),
        ),
        StandingsCase(
            "wins_tiebreak",
            (
                (RaceResult(a, 1), RaceResult(b, 2)),
                (RaceResult(a, 10), RaceResult(b, 6)),
            ),
            ((a, 26, 1, 1), (b, 26, 0, 1)),
        ),
        StandingsCase(
            "podiums_tiebreak",
            (
                (RaceResult(a, 1), RaceResult(b, 4)),
                (RaceResult(a, 2), RaceResult(b, 1)),
                (RaceResult(a, 9), RaceResult(b, 6)),
            ),
            ((a, 45, 1, 2), (b, 45, 1, 1)),
        ),
        StandingsCase(
            "driver_id_tiebreak",
            (
                (RaceResult(a, 1), RaceResult(b, 4)),
                (RaceResult(a, 5), RaceResult(b, 1)),
            ),
            ((low, 10, 1, 1), (high, 10, 1, 1)),
            configured_points=((1, 10), (4, 0), (5, 0)),
        ),
        StandingsCase(
            "unclassified_bonus_ignored",
            (
                (
                    RaceResult(a, 1, classified=False, pole=True, fastest_lap=True),
                    RaceResult(b, 2),
                ),
            ),
            ((b, 18, 0, 1), (a, 0, 0, 0)),
        ),
        StandingsCase(
            "configured_points_and_bonuses",
            (
                (
                    RaceResult(a, 1, pole=True, fastest_lap=True),
                    RaceResult(b, 2, fastest_lap=True),
                    RaceResult(c, 3),
                ),
            ),
            ((a, 9, 1, 1), (b, 6, 0, 1), (c, 0, 0, 1)),
            configured_points=((1, 7), (2, 5), (3, 0)),
        ),
    )


def assert_expected_standings(
    case: StandingsCase, actual: list[tuple[int, str, int, int, int]]
) -> None:
    expected_rows = sorted(case.expected, key=lambda row: row[0])
    expected_order = sorted(
        expected_rows,
        key=lambda row: (-row[1], -row[2], -row[3], row[0]),
    )
    expected = [
        (rank, driver, points, wins, podiums)
        for rank, (driver, points, wins, podiums) in enumerate(expected_order, start=1)
    ]
    if actual != expected:
        raise ProbeFailure(f"Standings case {case.name} returned unexpected ranks or totals")


class _RollbackProbe(Exception):
    pass


def run_sql_cases(database_url: str) -> dict[str, Any]:
    """Exercise recalculation and roll back all synthetic rows before returning."""
    try:
        with psycopg.connect(database_url) as conn:
            try:
                with conn.transaction():
                    with conn.cursor() as cur:
                        cur.execute("SELECT id::text FROM drivers ORDER BY id LIMIT 3")
                        driver_ids = [str(row[0]) for row in cur.fetchall()]
                        cases = standings_cases(driver_ids)
                        cur.execute("SELECT id FROM circuits ORDER BY id LIMIT 1")
                        circuit_row = cur.fetchone()
                        if circuit_row is None:
                            raise ProbeFailure("Owned seed has no circuit for standings cases")
                        circuit_id = circuit_row[0]
                        for case in cases:
                            _run_case(cur, circuit_id, case)
                    raise _RollbackProbe
            except _RollbackProbe:
                pass
    except ProbeFailure:
        raise
    except Exception as exc:
        sqlstate = getattr(exc, "sqlstate", None)
        suffix = f"SQLSTATE {sqlstate}" if sqlstate else type(exc).__name__
        raise ProbeFailure(f"Standings SQL probe failed ({suffix})") from None
    return {"cases": len(cases), "rolled_back": True}


def _run_case(cur: Any, circuit_id: UUID, case: StandingsCase) -> None:
    points_system_id = None
    if case.configured_points:
        cur.execute(
            "INSERT INTO points_systems(name,is_default) VALUES (%s,false) RETURNING id",
            (f"probe-{case.name}",),
        )
        points_system_id = cur.fetchone()[0]
        cur.executemany(
            "INSERT INTO points_system_positions(system_id,position,points) VALUES (%s,%s,%s)",
            [(points_system_id, position, points) for position, points in case.configured_points],
        )
    cur.execute(
        "INSERT INTO championships(name,season,points_system_id) VALUES (%s,2098,%s) RETURNING id",
        (f"Standings probe {case.name}", points_system_id or DEFAULT_POINTS_SYSTEM),
    )
    championship_id = cur.fetchone()[0]
    for round_number, results in enumerate(case.sessions, start=1):
        cur.execute(
            "INSERT INTO race_events(championship_id,circuit_id,round_number,name,start_date) "
            "VALUES (%s,%s,%s,%s,now()) RETURNING id",
            (championship_id, circuit_id, round_number, f"{case.name} round {round_number}"),
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
            "fastest_lap) "
            "VALUES (%s,%s,%s,%s,%s,%s)",
            [
                (
                    session_id,
                    UUID(item.driver),
                    item.position,
                    item.classified,
                    item.pole,
                    item.fastest_lap,
                )
                for item in results
            ],
        )
    cur.execute("SELECT recalculate_standings(%s)", (championship_id,))
    cur.execute(
        "SELECT rank,driver_id::text,points,wins,podiums FROM driver_standings "
        "WHERE championship_id=%s ORDER BY rank",
        (championship_id,),
    )
    assert_expected_standings(case, [tuple(row) for row in cur.fetchall()])


def run_owned_probe(env: dict[str, str]) -> dict[str, Any]:
    context = race_probe.validate_owned_environment(env)
    return run_sql_cases(context.database_url)


class _ProbeOwnedAdapter(owned_acceptance._CliAdapter):
    def run_acceptance(self, env: dict[str, str]) -> Any:
        return __import__("subprocess").Popen(
            [sys.executable, str(Path(__file__).resolve()), "--probe-child"],
            cwd=ROOT,
            env=env,
            start_new_session=True,
        )


def main() -> int:
    if sys.argv[1:] == ["--probe-child"]:
        try:
            result = run_owned_probe({key: os.environ.get(key, "") for key in OWNERSHIP_ENV_KEYS})
        except ProbeFailure as exc:
            print(f"FAIL: {exc}")
            return 1
        except Exception as exc:
            print(f"FAIL: standings cases probe error ({type(exc).__name__})")
            return 1
        print(f"PASS: {result['cases']} standings SQL cases; fixture rolled back")
        return 0
    try:
        owned_acceptance.run_owned_acceptance(_ProbeOwnedAdapter())
    except Exception as exc:
        print(f"FAIL: owned standings cases lifecycle ({type(exc).__name__})")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
