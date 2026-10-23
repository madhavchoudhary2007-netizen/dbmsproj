import asyncio
import random
import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app import demo_race_repository as repository
from app import main
from app.simulation_core import Simulation

ROOT = Path(__file__).resolve().parents[1]


def test_f_dom_05_migration_adds_idempotent_nullable_seed():
    migrations = list((ROOT / "migrations").glob("003*.sql"))
    assert migrations
    sql = migrations[0].read_text().lower()
    assert re.search(
        r"alter\s+table\s+if\s+exists\s+demo_races\s+add\s+column\s+if\s+not\s+exists\s+simulation_seed\s+bigint\s+null",
        sql,
    )


def test_f_dom_05_repository_persists_seed_and_generates_repeatable_grid(monkeypatch):  # noqa: C901
    class Cursor:
        def __init__(self):
            self.query = ""

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def execute(self, query, _params=()):
            self.query = query

        def fetchone(self):
            if "SELECT id FROM championships" in self.query:
                return None
            if "INSERT INTO championships" in self.query:
                return {"id": "championship"}
            if "COALESCE(max(round_number)" in self.query:
                return {"round": 1}
            return None

        def fetchall(self):
            if "FROM circuits" in self.query:
                return [{"id": "circuit", "name": "Test Circuit"}]
            if "FROM teams" in self.query:
                return [{"id": "team", "name": "Test Team"}]
            return []

    class Connection:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def cursor(self, **_kwargs):
            return Cursor()

    monkeypatch.setattr(repository, "connection", Connection)
    calls = []
    monkeypatch.setattr(
        Cursor,
        "execute",
        lambda self, query, params=(): (
            setattr(self, "query", query),
            calls.append((query, params)),
        ),
    )
    args = (datetime(2026, 10, 23, tzinfo=UTC), ["Test Driver"], False)
    generated_a, laps_a = repository.create_demo_race_records(uuid4(), uuid4(), *args, seed=123)
    insert_a = next(params for query, params in calls if "INSERT INTO demo_races" in query)
    calls.clear()
    generated_b, laps_b = repository.create_demo_race_records(uuid4(), uuid4(), *args, seed=123)
    insert_b = next(params for query, params in calls if "INSERT INTO demo_races" in query)
    assert 123 in insert_a and 123 in insert_b
    assert generated_a and generated_b
    actual = (generated_a[0]["number"], generated_a[0]["pace_offset_ms"], laps_a)
    expected = (generated_b[0]["number"], generated_b[0]["pace_offset_ms"], laps_b)
    assert actual == expected


def test_f_dom_05_seeded_packets_ignore_global_random_draws():
    timestamp = datetime(2026, 10, 23, 12, tzinfo=UTC)
    drivers = [{"id": "driver-a", "number": 7}, {"id": "driver-b", "number": 22}]

    def replay():
        sim = Simulation("replay", [dict(driver) for driver in drivers], 2, seed=123)
        outputs = []
        for tick in range(4):
            random.random()  # noqa: S311
            outputs.append(
                main.advance_simulation_tick(
                    sim, timestamp.replace(minute=tick), safety_car=tick == 1
                )
            )
        return outputs

    state = random.getstate()
    try:
        random.seed(10)
        first = replay()
        random.seed(999)
        for _ in range(37):
            random.random()  # noqa: S311
        second = replay()
        assert first == second
    finally:
        random.setstate(state)


def test_f_dom_05_active_generated_race_restores_stored_seed(monkeypatch):
    session_id = uuid4()
    active = [{"id": session_id, "total_laps": 50, "auto_repeat": True, "simulation_seed": 456}]
    entries = [
        {
            "id": "driver-a",
            "number": 7,
            "pace_offset_ms": 12,
            "team_id": "team",
            "team_name": "Team",
        }
    ]

    def fetch_all(query, _params=()):
        return active if "JOIN demo_races" in query else entries

    launched = []
    monkeypatch.setattr(main, "fetch_all", fetch_all)
    monkeypatch.setattr(main, "restore_simulation_from_telemetry", lambda _sim: None)
    monkeypatch.setattr(main, "restore_simulated_incidents", lambda _sim: None)
    monkeypatch.setattr(main, "launch_demo_simulation", lambda value: launched.append(value))
    try:
        asyncio.run(main.resume_or_create_auto_demo_race(create_if_missing=False))
        sim = main.simulations[str(session_id)]
        assert sim.seed == 456
        assert launched == [session_id]
    finally:
        main.simulations.pop(str(session_id), None)
