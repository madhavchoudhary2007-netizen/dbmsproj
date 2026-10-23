"""Integration checks for the PostgreSQL contract.

Run with DATABASE_URL=postgresql://... pytest backend/tests/test_database.py
Requires psycopg (v3) or psycopg2 and a PostgreSQL role allowed to create extensions
pgcrypto and btree_gist plus temporary schemas.
"""

import os
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest

try:
    import psycopg

    _connect = psycopg.connect
    _database_error = psycopg.DatabaseError
except ImportError:
    try:
        import psycopg2

        _connect = psycopg2.connect
        _database_error = psycopg2.DatabaseError
    except ImportError:
        _connect = None
        _database_error = None

URL = os.getenv("DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not URL or not _connect, reason="DATABASE_URL and psycopg are required"
)
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))


def _sqlstate(exc):
    return getattr(exc, "sqlstate", None) or getattr(exc, "pgcode", None)


def _auto_pit_fixture(cur):
    now = datetime.now(UTC)
    cur.execute("SELECT id FROM championships WHERE name='ApexGrid World Series' AND season=2026")
    championship_id = cur.fetchone()[0]
    cur.execute("SELECT id FROM circuits WHERE name='Harbor Ring'")
    circuit_id = cur.fetchone()[0]
    cur.execute(
        "SELECT COALESCE(max(round_number),0)+1 FROM race_events WHERE championship_id=%s",
        (championship_id,),
    )
    round_number = cur.fetchone()[0]
    cur.execute(
        """INSERT INTO race_events(championship_id,circuit_id,round_number,name,start_date)
        VALUES (%s,%s,%s,'Auto pit fixture',%s) RETURNING id""",
        (championship_id, circuit_id, round_number, now),
    )
    event_id = cur.fetchone()[0]
    cur.execute(
        """INSERT INTO race_sessions(event_id,session_type,state,scheduled_at,started_at,total_laps)
        VALUES (%s,'RACE','ACTIVE',%s,%s,20) RETURNING id""",
        (event_id, now, now),
    )
    session_id = cur.fetchone()[0]
    cur.execute(
        "INSERT INTO pit_boxes(event_id,number) SELECT %s,n FROM generate_series(1,4) AS n",
        (event_id,),
    )
    cur.execute("SELECT id FROM teams WHERE name='Apex Racing'")
    team_id = cur.fetchone()[0]
    cur.execute(
        """SELECT d.id FROM drivers d JOIN team_memberships m ON m.driver_id=d.id
        WHERE m.team_id=%s AND m.start_date<=%s::date
          AND (m.end_date IS NULL OR m.end_date>=%s::date)
        ORDER BY d.number LIMIT 2""",
        (team_id, now, now),
    )
    drivers = [row[0] for row in cur.fetchall()]
    return now, event_id, session_id, team_id, drivers


@pytest.fixture
def db():
    conn = _connect(URL)
    schema = "apexgrid_test_" + uuid.uuid4().hex[:12]
    try:
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(f'CREATE SCHEMA "{schema}"')
        cur.execute(f'SET search_path TO "{schema}", public')
        for migration in sorted((ROOT / "migrations").glob("[0-9]*.sql")):
            cur.execute(migration.read_text())
        cur.execute((ROOT / "db/seed.sql").read_text())
        yield conn, cur
    finally:
        try:
            cur.close()
            conn.autocommit = True
            conn.cursor().execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
        finally:
            conn.close()


def test_seed_contract_and_indexes(db):
    _, cur = db
    cur.execute("SELECT count(*) FROM drivers")
    assert cur.fetchone()[0] == 10
    cur.execute("SELECT count(*) FROM users WHERE role IN ('ADMIN','STEWARD','PRINCIPAL')")
    assert cur.fetchone()[0] == 3
    cur.execute("SELECT count(*) FROM race_events")
    assert cur.fetchone()[0] >= 2
    cur.execute(
        "SELECT indexdef FROM pg_indexes WHERE schemaname=current_schema() "
        "AND indexname='idx_session_results_session_lap_time'"
    )
    assert "(session_id, lap_time_ms)" in cur.fetchone()[0]
    cur.execute(
        "SELECT indexdef FROM pg_indexes WHERE schemaname=current_schema() "
        "AND indexname='idx_drivers_licence_hash'"
    )
    assert "USING hash" in cur.fetchone()[0]


def test_penalty_insert_accumulates_once_and_bans_at_threshold(db):
    _, cur = db
    cur.execute("SELECT id FROM drivers WHERE number=9")
    driver_id = cur.fetchone()[0]
    cur.execute("SELECT id FROM race_sessions WHERE session_type='RACE' LIMIT 1")
    session_id = cur.fetchone()[0]
    cur.execute(
        """INSERT INTO incident_reports(session_id,driver_id,lap,description,state)
                    VALUES (%s,%s,3,'threshold test','APPROVED') RETURNING id""",
        (session_id, driver_id),
    )
    incident_id = cur.fetchone()[0]
    cur.execute(
        "INSERT INTO penalties(incident_id,driver_id,points) VALUES (%s,%s,9)",
        (incident_id, driver_id),
    )
    cur.execute("SELECT eligibility FROM drivers WHERE id=%s", (driver_id,))
    assert cur.fetchone()[0] == "ACTIVE"
    cur.execute(
        """INSERT INTO incident_reports(session_id,driver_id,lap,description,state)
                    VALUES (%s,%s,4,'threshold test two','APPROVED') RETURNING id""",
        (session_id, driver_id),
    )
    incident2 = cur.fetchone()[0]
    cur.execute(
        "INSERT INTO penalties(incident_id,driver_id,points) VALUES (%s,%s,3)",
        (incident2, driver_id),
    )
    cur.execute("SELECT eligibility FROM drivers WHERE id=%s", (driver_id,))
    assert cur.fetchone()[0] == "RACE_BANNED"
    cur.execute(
        "SELECT points FROM penalty_points WHERE driver_id=%s AND season=2026", (driver_id,)
    )
    assert cur.fetchone()[0] == 12
    with pytest.raises(_database_error):
        cur.execute(
            "INSERT INTO penalties(incident_id,driver_id,points) VALUES (%s,%s,3)",
            (incident2, driver_id),
        )


def test_penalties_are_immutable_after_points_are_awarded(db):
    _, cur = db
    cur.execute("SELECT id FROM drivers WHERE number=9")
    driver_id = cur.fetchone()[0]
    cur.execute("SELECT id FROM race_sessions WHERE session_type='RACE' LIMIT 1")
    session_id = cur.fetchone()[0]
    cur.execute(
        """INSERT INTO incident_reports(session_id,driver_id,lap,description,state)
                    VALUES (%s,%s,7,'immutable penalty fixture','APPROVED') RETURNING id""",
        (session_id, driver_id),
    )
    incident_id = cur.fetchone()[0]
    cur.execute(
        "INSERT INTO penalties(incident_id,driver_id,points) VALUES (%s,%s,4) RETURNING id",
        (incident_id, driver_id),
    )
    penalty_id = cur.fetchone()[0]

    with pytest.raises(Exception) as exc:
        cur.execute("UPDATE penalties SET points=1 WHERE id=%s", (penalty_id,))
    assert _sqlstate(exc.value) == "23514"
    with pytest.raises(Exception) as exc:
        cur.execute("DELETE FROM penalties WHERE id=%s", (penalty_id,))
    assert _sqlstate(exc.value) == "23514"

    cur.execute(
        "SELECT points FROM penalty_points WHERE driver_id=%s AND season=2026", (driver_id,)
    )
    assert cur.fetchone()[0] == 4
    cur.execute("SELECT points FROM penalties WHERE id=%s", (penalty_id,))
    assert cur.fetchone()[0] == 4


def test_standings_and_overlapping_pit_reservation(db):
    _, cur = db
    cur.execute("SELECT id FROM championships WHERE season=2026")
    championship_id = cur.fetchone()[0]
    cur.execute("SELECT recalculate_standings(%s)", (championship_id,))
    cur.execute("SELECT count(*), min(rank), max(rank) FROM driver_standings WHERE championship_id=%s", (championship_id,))
    assert cur.fetchone() == (10, 1, 10)
    cur.execute("""SELECT b.id,s.id,t.id FROM pit_boxes b JOIN race_events e ON e.id=b.event_id
                    JOIN race_sessions s ON s.event_id=e.id JOIN teams t ON true
                    WHERE s.session_type='RACE' LIMIT 1""")
    box, session, team = cur.fetchone()
    cur.execute("SELECT reserve_pit_box(%s,%s,%s,'2026-03-15 08:00+00','2026-03-15 09:00+00')", (box, session, team))
    with pytest.raises(_database_error):
        cur.execute("SELECT reserve_pit_box(%s,%s,%s,'2026-03-15 08:30+00','2026-03-15 09:30+00')", (box, session, team))


def test_historical_penalty_provisional(db, monkeypatch):
    _, cur = db
    cur.execute("SELECT id FROM championships WHERE name='ApexGrid World Series' AND season=2026")
    championship_id = cur.fetchone()[0]
    cur.execute("""SELECT e.round_number,s.id FROM race_events e JOIN race_sessions s ON s.event_id=e.id
        WHERE e.championship_id=%s AND e.round_number IN (1,2) AND s.session_type='RACE'
        ORDER BY e.round_number""", (championship_id,))
    sessions = dict(cur.fetchall())
    round1, round2 = sessions[1], sessions[2]
    cur.execute("""SELECT count(*), min(p.time_seconds) FROM penalties p
        JOIN incident_reports i ON i.id=p.incident_id WHERE i.session_id=%s""", (round1,))
    assert cur.fetchone() == (1, 5)
    cur.execute("""SELECT count(*) FROM penalties p JOIN incident_reports i ON i.id=p.incident_id
        WHERE i.session_id=%s""", (round2,))
    assert cur.fetchone()[0] == 0

    from backend.app import main

    def schema_fetch_all(query, params=()):
        cur.execute(query, params)
        columns = [column.name for column in cur.description]
        return [dict(zip(columns, row, strict=True)) for row in cur.fetchall()]

    monkeypatch.setattr(main, "fetch_all", schema_fetch_all)
    cur.execute("SELECT recalculate_standings(%s)", (championship_id,))
    affected_results = main.results(round1)
    unaffected_results = main.results(round2)
    championship_standings = main.standings(championship_id)
    assert affected_results and all(row["provisional"] is True for row in affected_results)
    assert unaffected_results and all(row["provisional"] is False for row in unaffected_results)
    assert championship_standings and all(row["provisional"] is True for row in championship_standings)


def test_unclassified_bonus_points_do_not_count(db):
    _, cur = db
    now = datetime.now(UTC)
    cur.execute("INSERT INTO championships(name,season) VALUES ('Unclassified bonus regression',2099) RETURNING id")
    championship_id = cur.fetchone()[0]
    cur.execute("SELECT id FROM circuits WHERE name='Harbor Ring'")
    circuit_id = cur.fetchone()[0]
    cur.execute("SELECT id FROM drivers WHERE number=1 ORDER BY licence_number LIMIT 1")
    driver_id = cur.fetchone()[0]
    cur.execute("""INSERT INTO race_events(championship_id,circuit_id,round_number,name,start_date)
        VALUES (%s,%s,1,'Unclassified bonus regression',%s) RETURNING id""", (championship_id,circuit_id,now))
    event_id = cur.fetchone()[0]
    cur.execute("""INSERT INTO race_sessions(event_id,session_type,state,scheduled_at,started_at,ended_at,total_laps)
        VALUES (%s,'RACE','COMPLETED',%s,%s,%s,1) RETURNING id""", (event_id,now,now,now))
    session_id = cur.fetchone()[0]
    cur.execute("""INSERT INTO session_results(session_id,driver_id,position,lap_time_ms,pole,fastest_lap,classified)
        VALUES (%s,%s,1,90000,true,true,false)""", (session_id,driver_id))
    cur.execute("SELECT recalculate_standings(%s)", (championship_id,))
    cur.execute("SELECT points FROM driver_standings WHERE championship_id=%s AND driver_id=%s", (championship_id,driver_id))
    assert cur.fetchone()[0] == 0


def test_penalty_requires_approved_incident_and_matching_driver(db):
    _, cur = db
    cur.execute("SELECT id FROM drivers WHERE number=9")
    incident_driver = cur.fetchone()[0]
    cur.execute("SELECT id FROM drivers WHERE number=8")
    other_driver = cur.fetchone()[0]
    cur.execute("SELECT id FROM race_sessions WHERE session_type='RACE' LIMIT 1")
    session_id = cur.fetchone()[0]

    cur.execute("""INSERT INTO incident_reports(session_id,driver_id,lap,description,state)
                    VALUES (%s,%s,5,'pending penalty guard','OPEN') RETURNING id""",
                (session_id, incident_driver))
    open_incident = cur.fetchone()[0]
    with pytest.raises(_database_error):
        cur.execute("INSERT INTO penalties(incident_id,driver_id,points) VALUES (%s,%s,2)",
                    (open_incident, incident_driver))

    cur.execute("""INSERT INTO incident_reports(session_id,driver_id,lap,description,state)
                    VALUES (%s,%s,6,'driver penalty guard','APPROVED') RETURNING id""",
                (session_id, incident_driver))
    approved_incident = cur.fetchone()[0]
    with pytest.raises(_database_error):
        cur.execute("INSERT INTO penalties(incident_id,driver_id,points) VALUES (%s,%s,2)",
                    (approved_incident, other_driver))


def test_incident_laps_stay_within_session_distance(db):
    _, cur = db
    cur.execute("SELECT id,total_laps FROM race_sessions WHERE total_laps>0 ORDER BY total_laps LIMIT 1")
    session_id, total_laps = cur.fetchone()
    cur.execute("SELECT id FROM drivers ORDER BY number LIMIT 1")
    driver_id = cur.fetchone()[0]

    cur.execute("INSERT INTO incident_reports(session_id,driver_id,lap,description) VALUES (%s,%s,%s,'valid boundary')",
                (session_id, driver_id, total_laps))
    with pytest.raises(Exception) as exc:
        cur.execute("INSERT INTO incident_reports(session_id,driver_id,lap,description) VALUES (%s,%s,%s,'past distance')",
                    (session_id, driver_id, total_laps + 1))
    assert _sqlstate(exc.value) == "23514"
    with pytest.raises(Exception) as exc:
        cur.execute("INSERT INTO incident_reports(session_id,driver_id,lap,description) VALUES (%s,%s,73,'hard cap')",
                    (session_id, driver_id))
    assert _sqlstate(exc.value) == "23514"
    with pytest.raises(Exception) as exc:
        cur.execute("UPDATE race_sessions SET total_laps=%s WHERE id=%s", (total_laps - 1, session_id))
    assert _sqlstate(exc.value) == "23514"


def test_seed_has_scheduled_third_round_race(db):
    _, cur = db
    cur.execute("""SELECT s.state,s.total_laps,s.scheduled_at=e.start_date
                    FROM race_sessions s JOIN race_events e ON e.id=s.event_id
                    WHERE e.round_number=3 AND s.session_type='RACE'""")
    assert cur.fetchone() == ("SCHEDULED", 25, True)


def test_seed_does_not_write_historical_data_to_user_created_race(db):
    _, cur = db
    cur.execute("SELECT e.id,e.start_date,d.id FROM race_events e CROSS JOIN drivers d WHERE e.round_number=1 AND d.number=1")
    event_id, start_date, driver_id = cur.fetchone()
    cur.execute("""INSERT INTO race_sessions(event_id,session_type,state,scheduled_at,started_at,total_laps)
                    VALUES (%s,'RACE','ACTIVE',%s,%s,25) RETURNING id""",
                (event_id, start_date, start_date))
    session_id = cur.fetchone()[0]
    cur.execute("""INSERT INTO session_results(session_id,driver_id,position,lap_time_ms)
                    VALUES (%s,%s,1,90000)""", (session_id, driver_id))

    cur.execute((ROOT / "db/seed.sql").read_text())

    cur.execute("SELECT count(*) FROM session_results WHERE session_id=%s", (session_id,))
    assert cur.fetchone()[0] == 1
    cur.execute("""SELECT count(*) FROM incident_reports
                    WHERE session_id=%s AND description='Unsafe rejoin after leaving the circuit'""", (session_id,))
    assert cur.fetchone()[0] == 0


def test_seed_skips_generated_demo_championship_events(db):
    _, cur = db
    cur.execute("INSERT INTO championships(name,season) VALUES ('ApexGrid Live Demo',2026) RETURNING id")
    championship_id = cur.fetchone()[0]
    cur.execute("SELECT id FROM circuits WHERE name='Harbor Ring'")
    circuit_id = cur.fetchone()[0]
    cur.execute("""INSERT INTO race_events(championship_id,circuit_id,round_number,name,start_date)
                    VALUES (%s,%s,1,'ApexGrid Live Demo','2026-10-05 12:00+00') RETURNING id""",
                (championship_id, circuit_id))
    event_id = cur.fetchone()[0]

    cur.execute((ROOT / "db/seed.sql").read_text())

    cur.execute("SELECT count(*) FROM race_sessions WHERE event_id=%s", (event_id,))
    assert cur.fetchone()[0] == 0
    cur.execute("SELECT count(*) FROM pit_boxes WHERE event_id=%s", (event_id,))
    assert cur.fetchone()[0] == 0
    cur.execute("""SELECT count(*) FROM session_results r JOIN race_sessions s ON s.id=r.session_id
                    WHERE s.event_id=%s""", (event_id,))
    assert cur.fetchone()[0] == 0
    cur.execute("""SELECT count(*) FROM incident_reports i JOIN race_sessions s ON s.id=i.session_id
                    WHERE s.event_id=%s""", (event_id,))
    assert cur.fetchone()[0] == 0


def test_seed_does_not_assign_fixture_team_to_new_driver(db):
    _, cur = db
    cur.execute("""INSERT INTO drivers(number,licence_number)
                    VALUES (946,'TEST-NEW-946') RETURNING id""")
    driver_id = cur.fetchone()[0]

    cur.execute((ROOT / "db/seed.sql").read_text())

    cur.execute("SELECT count(*) FROM team_memberships WHERE driver_id=%s", (driver_id,))
    assert cur.fetchone()[0] == 0


def test_migration_backfills_four_pit_boxes_for_generated_event(db):
    _, cur = db
    cur.execute("INSERT INTO championships(name,season) VALUES ('ApexGrid Live Demo',2026) RETURNING id")
    championship_id = cur.fetchone()[0]
    cur.execute("SELECT id FROM circuits WHERE name='Harbor Ring'")
    circuit_id = cur.fetchone()[0]
    cur.execute("""INSERT INTO race_events(championship_id,circuit_id,round_number,name,start_date)
                    VALUES (%s,%s,1,'Generated pit fixture','2026-10-05 12:00+00') RETURNING id""",
                (championship_id, circuit_id))
    event_id = cur.fetchone()[0]
    cur.execute("""INSERT INTO race_sessions(event_id,session_type,state,scheduled_at,started_at,total_laps)
                    VALUES (%s,'RACE','ACTIVE','2026-10-05 12:00+00','2026-10-05 12:00+00',20) RETURNING id""",
                (event_id,))
    session_id = cur.fetchone()[0]
    cur.execute("INSERT INTO demo_races(session_id,event_id) VALUES (%s,%s)", (session_id,event_id))

    cur.execute((ROOT / "migrations/001_initial.sql").read_text())

    cur.execute("SELECT number FROM pit_boxes WHERE event_id=%s ORDER BY number", (event_id,))
    assert [row[0] for row in cur.fetchall()] == [1, 2, 3, 4]


def test_concurrent_overlapping_pit_reservations_allow_only_one(db):
    """The second connection waits on the box row, then sees the committed overlap."""
    import threading
    import time

    _, cur = db
    cur.execute("""SELECT b.id,s.id,t.id FROM pit_boxes b
                    JOIN race_events e ON e.id=b.event_id
                    JOIN race_sessions s ON s.event_id=e.id AND s.session_type='RACE'
                    JOIN teams t ON t.id=(SELECT id FROM teams ORDER BY name LIMIT 1)
                    WHERE e.round_number=1 LIMIT 1""")
    box_id, session_id, team_id = cur.fetchone()
    cur.execute("SELECT current_schema()")
    schema = cur.fetchone()[0]

    conn_a = _connect(URL)
    conn_b = _connect(URL)
    errors = []
    b_started = threading.Event()
    try:
        for conn in (conn_a, conn_b):
            conn.autocommit = False
            setup = conn.cursor()
            setup.execute(f'SET search_path TO "{schema}", public')
            setup.execute("SET lock_timeout='8s'")
            setup.execute("SET statement_timeout='10s'")
            setup.close()

        cur_a = conn_a.cursor()
        cur_a.execute("SELECT reserve_pit_box(%s,%s,%s,%s,%s)",
                      (box_id, session_id, team_id, "2026-06-01 08:00+00", "2026-06-01 09:00+00"))

        def reserve_from_b():
            cursor = conn_b.cursor()
            b_started.set()
            try:
                cursor.execute("SELECT reserve_pit_box(%s,%s,%s,%s,%s)",
                               (box_id, session_id, team_id, "2026-06-01 08:30+00", "2026-06-01 09:30+00"))
                conn_b.commit()
                errors.append(("unexpected-success", None))
            except Exception as exc:
                sqlstate = getattr(exc, "sqlstate", None) or getattr(exc, "pgcode", None)
                conn_b.rollback()
                errors.append(("error", sqlstate))
            finally:
                cursor.close()

        worker = threading.Thread(target=reserve_from_b, daemon=True)
        worker.start()
        assert b_started.wait(timeout=3), "second connection did not start"
        time.sleep(0.25)  # let B reach the row lock while A still owns it
        conn_a.commit()
        worker.join(timeout=12)
        assert not worker.is_alive(), "second reservation hung past its statement timeout"
        assert errors == [("error", "23P01")]

        cur.execute("SELECT count(*) FROM pit_reservations WHERE pit_box_id=%s AND status='RESERVED'", (box_id,))
        assert cur.fetchone()[0] == 1
    finally:
        conn_a.rollback()
        conn_b.rollback()
        conn_a.close()
        conn_b.close()


def test_reserved_pit_driver_is_unique_per_session(db):
    _, cur = db
    now, event_id, session_id, team_id, drivers = _auto_pit_fixture(cur)
    assert drivers
    cur.execute("SELECT id FROM pit_boxes WHERE event_id=%s ORDER BY number LIMIT 1", (event_id,))
    first_box = cur.fetchone()[0]
    cur.execute("SELECT id FROM pit_boxes WHERE event_id=%s ORDER BY number OFFSET 1 LIMIT 1", (event_id,))
    second_box = cur.fetchone()[0]
    cur.execute("""INSERT INTO pit_reservations(
        pit_box_id,session_id,team_id,driver_id,starts_at,ends_at
    ) VALUES (%s,%s,%s,%s,%s,%s)""",
        (first_box, session_id, team_id, drivers[0], now, now + __import__('datetime').timedelta(minutes=5)))

    with pytest.raises(Exception) as exc:
        cur.execute("""INSERT INTO pit_reservations(
            pit_box_id,session_id,team_id,driver_id,starts_at,ends_at
        ) VALUES (%s,%s,%s,%s,%s,%s)""",
            (second_box, session_id, team_id, drivers[0], now, now + __import__('datetime').timedelta(minutes=5)))
    assert _sqlstate(exc.value) == "23505"

    # Releasing a reservation makes its driver available for another stop.
    cur.execute("UPDATE pit_reservations SET status='CANCELLED' WHERE session_id=%s AND driver_id=%s",
                (session_id, drivers[0]))
    cur.execute("""INSERT INTO pit_reservations(
        pit_box_id,session_id,team_id,driver_id,starts_at,ends_at
    ) VALUES (%s,%s,%s,%s,%s,%s)""",
        (second_box, session_id, team_id, drivers[0], now, now + __import__('datetime').timedelta(minutes=5)))


def test_auto_pit_allocator_chooses_earliest_gap_and_next_unreserved_driver(db):
    _, cur = db
    now, event_id, session_id, team_id, drivers = _auto_pit_fixture(cur)
    assert len(drivers) == 2
    cur.execute("SELECT id FROM pit_boxes WHERE event_id=%s AND number=1", (event_id,))
    box_one = cur.fetchone()[0]
    # Leave a later booking on the first box. The allocator should fill the
    # earlier gap, then choose a different driver for the following request.
    cur.execute("""INSERT INTO pit_reservations(pit_box_id,session_id,team_id,starts_at,ends_at)
        VALUES (%s,%s,%s,%s,%s)""",
        (box_one, session_id, team_id, now + __import__('datetime').timedelta(minutes=10),
         now + __import__('datetime').timedelta(minutes=20)))
    cur.execute("SELECT reserve_pit_box_auto(%s,%s,%s,interval '5 minutes')",
                (session_id, team_id, drivers[0]))
    first_id = cur.fetchone()[0]
    cur.execute("SELECT b.number,r.starts_at,r.allocation_source,r.driver_id FROM pit_reservations r "
                "JOIN pit_boxes b ON b.id=r.pit_box_id WHERE r.id=%s", (first_id,))
    number, starts_at, source, assigned_driver = cur.fetchone()
    assert number == 1
    assert starts_at < now + __import__('datetime').timedelta(minutes=10)
    assert source == "AUTOMATIC" and assigned_driver == drivers[0]

    cur.execute("SELECT reserve_pit_box_auto(%s,%s,NULL,interval '5 minutes')", (session_id, team_id))
    second_id = cur.fetchone()[0]
    cur.execute("SELECT r.driver_id,b.number,r.allocation_source FROM pit_reservations r "
                "JOIN pit_boxes b ON b.id=r.pit_box_id WHERE r.id=%s", (second_id,))
    assigned_driver, number, source = cur.fetchone()
    assert assigned_driver == drivers[1]
    assert number == 2
    assert source == "AUTOMATIC"

    with pytest.raises(Exception) as error:
        cur.execute("SELECT reserve_pit_box_auto(%s,%s,%s,interval '5 minutes')",
                    (session_id, team_id, drivers[0]))
    assert _sqlstate(error.value) == "23505"


def test_concurrent_auto_allocations_serialize_on_event(db):
    import threading
    _, cur = db
    now, event_id, session_id, team_id, drivers = _auto_pit_fixture(cur)
    assert len(drivers) == 2
    cur.execute("SELECT current_schema()")
    schema = cur.fetchone()[0]
    conns = [_connect(URL), _connect(URL)]
    barrier = threading.Barrier(2)
    results = []
    errors = []
    try:
        for conn in conns:
            conn.autocommit = False
            setup = conn.cursor()
            setup.execute(f'SET search_path TO "{schema}", public')
            setup.execute("SET lock_timeout='8s'")
            setup.execute("SET statement_timeout='10s'")
            setup.close()

        def allocate(conn, driver_id):
            cursor = conn.cursor()
            try:
                barrier.wait(timeout=3)
                cursor.execute("SELECT reserve_pit_box_auto(%s,%s,%s,interval '5 minutes')",
                               (session_id, team_id, driver_id))
                reservation_id = cursor.fetchone()[0]
                conn.commit()
                results.append(reservation_id)
            except Exception as exc:
                conn.rollback()
                errors.append(exc)
            finally:
                cursor.close()

        workers = [threading.Thread(target=allocate, args=(conn, driver), daemon=True)
                   for conn, driver in zip(conns, drivers, strict=True)]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join(timeout=12)
        assert all(not worker.is_alive() for worker in workers)
        assert not errors
        assert len(results) == 2
        cur.execute("SELECT count(DISTINCT pit_box_id) FROM pit_reservations WHERE id=ANY(%s)",
                    (results,))
        assert cur.fetchone()[0] == 2
    finally:
        for conn in conns:
            conn.rollback()
            conn.close()


def test_session_state_guards_allow_api_lifecycle_and_reset(db):
    _, cur = db
    cur.execute("SELECT s.id FROM race_sessions s JOIN race_events e ON e.id=s.event_id WHERE e.round_number=3 AND s.session_type='RACE'")
    session_id = cur.fetchone()[0]
    with pytest.raises(Exception) as exc:
        cur.execute("UPDATE race_sessions SET state='PAUSED' WHERE id=%s", (session_id,))
    assert _sqlstate(exc.value) == "23514"
    with pytest.raises(Exception) as exc:
        cur.execute("UPDATE race_sessions SET started_at=now() WHERE id=%s", (session_id,))
    assert _sqlstate(exc.value) == "23514"

    cur.execute("UPDATE race_sessions SET state='ACTIVE',started_at='2026-05-10 14:00+00' WHERE id=%s", (session_id,))
    cur.execute("UPDATE race_sessions SET state='PAUSED' WHERE id=%s", (session_id,))
    cur.execute("UPDATE race_sessions SET state='ACTIVE' WHERE id=%s", (session_id,))
    cur.execute("UPDATE race_sessions SET state='COMPLETED',ended_at='2026-05-10 16:00+00' WHERE id=%s", (session_id,))
    cur.execute("UPDATE race_sessions SET state='SCHEDULED',started_at=NULL,ended_at=NULL,safety_car=false WHERE id=%s", (session_id,))
    cur.execute("SELECT state,started_at,ended_at FROM race_sessions WHERE id=%s", (session_id,))
    assert cur.fetchone() == ("SCHEDULED", None, None)


def test_classified_positions_are_unique_per_session(db):
    _, cur = db
    cur.execute("""SELECT s.id,occupied.position,target.id FROM race_sessions s
                    JOIN race_events e ON e.id=s.event_id
                    JOIN session_results occupied ON occupied.session_id=s.id AND occupied.classified
                    JOIN session_results target ON target.session_id=s.id AND target.id<>occupied.id
                    WHERE e.round_number=1 AND s.session_type='RACE'
                    ORDER BY occupied.position LIMIT 1""")
    session_id, occupied_position, target_result_id = cur.fetchone()
    with pytest.raises(Exception) as exc:
        cur.execute("UPDATE session_results SET position=%s WHERE id=%s", (occupied_position, target_result_id))
    assert _sqlstate(exc.value) == "23505"
    # Unclassified results may retain a position also used by a classified result.
    cur.execute("UPDATE session_results SET position=%s,classified=false WHERE id=%s",
                (occupied_position, target_result_id))


def test_driver_team_memberships_cannot_overlap(db):
    _, cur = db
    cur.execute("""SELECT m.id,m.driver_id,m.start_date,t2.id
                    FROM team_memberships m CROSS JOIN teams t2
                    WHERE t2.name<>'Apex Racing' ORDER BY m.start_date LIMIT 1""")
    membership_id, driver_id, _, next_team_id = cur.fetchone()
    with pytest.raises(Exception) as exc:
        cur.execute("""INSERT INTO team_memberships(driver_id,team_id,start_date)
                        VALUES (%s,%s,'2026-02-01')""", (driver_id, next_team_id))
    assert _sqlstate(exc.value) == "23P01"

    cur.execute("UPDATE team_memberships SET end_date='2026-01-31' WHERE id=%s", (membership_id,))
    cur.execute("""INSERT INTO team_memberships(driver_id,team_id,start_date,end_date)
                    VALUES (%s,%s,'2026-02-01','2026-12-31')""", (driver_id, next_team_id))
    with pytest.raises(Exception) as exc:
        cur.execute("""INSERT INTO team_memberships(driver_id,team_id,start_date)
                        VALUES (%s,(SELECT id FROM teams WHERE name='Orion GP'),'2026-01-31')""", (driver_id,))
    assert _sqlstate(exc.value) == "23P01"


def test_generated_race_markers_enforce_ownership_and_cascade(db):
    _, cur = db
    cur.execute("SELECT s.id,s.event_id FROM race_sessions s WHERE s.session_type='RACE' ORDER BY s.scheduled_at LIMIT 1")
    session_id, event_id = cur.fetchone()
    cur.execute("SELECT id FROM race_events WHERE id<>%s LIMIT 1", (event_id,))
    other_event_id = cur.fetchone()[0]
    cur.execute("SELECT id FROM drivers ORDER BY number LIMIT 1")
    driver_id = cur.fetchone()[0]

    with pytest.raises(Exception) as exc:
        cur.execute("INSERT INTO demo_races(session_id,event_id) VALUES (%s,%s)", (session_id, other_event_id))
    assert _sqlstate(exc.value) == "23503"
    cur.execute("INSERT INTO demo_races(session_id,event_id) VALUES (%s,%s)", (session_id, event_id))
    cur.execute("INSERT INTO demo_race_entries(session_id,driver_id,pace_offset_ms) VALUES (%s,%s,0)",
                (session_id, driver_id))

    with pytest.raises(Exception) as exc:
        cur.execute("INSERT INTO demo_race_entries(session_id,driver_id,pace_offset_ms) VALUES (%s,%s,1)",
                    (session_id, driver_id))
    assert _sqlstate(exc.value) == "23505"
    with pytest.raises(Exception) as exc:
        cur.execute("INSERT INTO demo_race_entries(session_id,driver_id,pace_offset_ms) VALUES (%s,%s,3001)",
                    (session_id, driver_id))
    assert _sqlstate(exc.value) == "23514"
    with pytest.raises(Exception) as exc:
        cur.execute("INSERT INTO demo_race_entries(session_id,driver_id,pace_offset_ms) VALUES (%s,%s,0)",
                    (session_id, uuid.uuid4()))
    assert _sqlstate(exc.value) == "23503"  # Missing driver is rejected by its FK.

    cur.execute("DELETE FROM demo_races WHERE session_id=%s", (session_id,))
    cur.execute("SELECT count(*) FROM demo_races WHERE session_id=%s", (session_id,))
    assert cur.fetchone()[0] == 0
    cur.execute("SELECT count(*) FROM demo_race_entries WHERE session_id=%s", (session_id,))
    assert cur.fetchone()[0] == 0
    cur.execute("SELECT count(*) FROM drivers WHERE id=%s", (driver_id,))
    assert cur.fetchone()[0] == 1
    cur.execute("SELECT count(*) FROM race_sessions WHERE id=%s", (session_id,))
    assert cur.fetchone()[0] == 1


def test_migration_reruns_on_populated_schema_and_preserves_generated_race(db):
    _, cur = db
    cur.execute("SELECT id FROM race_events WHERE round_number=1 LIMIT 1")
    event_id = cur.fetchone()[0]
    cur.execute("SELECT id FROM drivers WHERE number=1")
    driver_id = cur.fetchone()[0]
    cur.execute("""INSERT INTO race_sessions(event_id,session_type,state,scheduled_at,started_at,ended_at,total_laps)
        VALUES (%s,'RACE','COMPLETED','2026-06-01 14:00+00','2026-06-01 14:00+00','2026-06-01 16:00+00',24)
        RETURNING id""", (event_id,))
    session_id = cur.fetchone()[0]
    cur.execute("INSERT INTO demo_races(session_id,event_id) VALUES (%s,%s)", (session_id,event_id))
    cur.execute("INSERT INTO demo_race_entries(session_id,driver_id,pace_offset_ms) VALUES (%s,%s,17)",
                (session_id,driver_id))
    cur.execute("INSERT INTO session_results(session_id,driver_id,position,lap_time_ms) VALUES (%s,%s,1,90000)",
                (session_id,driver_id))
    # Simulate an earlier deployment with the lookup-only index.
    cur.execute("CREATE INDEX idx_pit_reservations_driver_active ON pit_reservations(session_id,driver_id) WHERE status='RESERVED' AND driver_id IS NOT NULL")

    cur.execute((ROOT / "migrations/001_initial.sql").read_text())

    cur.execute("SELECT count(*) FROM drivers")
    assert cur.fetchone()[0] == 10
    cur.execute("SELECT count(*) FROM pg_indexes WHERE schemaname=current_schema() AND indexname='idx_pit_reservations_driver_active'")
    assert cur.fetchone()[0] == 0
    cur.execute("SELECT indexdef FROM pg_indexes WHERE schemaname=current_schema() AND indexname='uq_pit_reservations_active_driver'")
    assert "UNIQUE INDEX" in cur.fetchone()[0]
    cur.execute("""SELECT s.state,s.total_laps,d.event_id,e.driver_id,e.pace_offset_ms,r.position
        FROM race_sessions s JOIN demo_races d ON d.session_id=s.id
        JOIN demo_race_entries e ON e.session_id=s.id
        JOIN session_results r ON r.session_id=s.id AND r.driver_id=e.driver_id
        WHERE s.id=%s""", (session_id,))
    assert cur.fetchone() == ("COMPLETED",24,event_id,driver_id,17,1)
