from __future__ import annotations

import random
import secrets
from datetime import datetime
from typing import Any, cast
from uuid import UUID, uuid4

import bcrypt
from psycopg import Cursor
from psycopg.rows import dict_row

from .database import connection, fetch_all, fetch_one
from .simulation_core import MAX_SESSION_LAPS


class DemoRaceSetupError(Exception):
    pass


class DemoRaceDeleteConflict(Exception):
    pass


def validate_demo_race_delete(
    cur: Cursor[dict[str, Any]], session_id: UUID, marker: dict[str, Any]
) -> None:
    cur.execute(
        "SELECT 1 FROM incident_reports i JOIN penalties p "
        "ON p.incident_id=i.id WHERE i.session_id=%s LIMIT 1",
        (session_id,),
    )
    if cur.fetchone():
        raise DemoRaceDeleteConflict("Demo race has official penalties and cannot be deleted")
    cur.execute(
        "SELECT 1 FROM driver_standings st JOIN demo_race_entries de "
        "ON de.driver_id=st.driver_id\n"
        "        WHERE de.session_id=%s AND st.championship_id<>%s LIMIT 1",
        (session_id, marker["championship_id"]),
    )
    if cur.fetchone():
        raise DemoRaceDeleteConflict(
            "Demo race drivers are referenced by another championship's standings"
        )
    cur.execute(
        "SELECT 1 FROM race_sessions WHERE event_id=%s AND id<>%s LIMIT 1",
        (marker["event_id"], session_id),
    )
    if cur.fetchone():
        raise DemoRaceDeleteConflict("Demo race event is referenced by another session")
    cur.execute(
        "SELECT 1 FROM pit_reservations p JOIN pit_boxes b ON b.id=p.pit_box_id "
        "WHERE b.event_id=%s AND p.session_id<>%s LIMIT 1",
        (marker["event_id"], session_id),
    )
    if cur.fetchone():
        raise DemoRaceDeleteConflict("Demo race event has reservations for another session")
    cur.execute(
        "SELECT 1 FROM demo_race_entries de WHERE de.session_id=%s AND (\n"
        "        EXISTS (SELECT 1 FROM session_results sr WHERE sr.driver_id=de.driver_id "
        "AND sr.session_id<>%s) OR\n"
        "        EXISTS (SELECT 1 FROM incident_reports ir WHERE ir.driver_id=de.driver_id "
        "AND ir.session_id<>%s) OR\n"
        "        EXISTS (SELECT 1 FROM demo_race_entries other WHERE "
        "other.driver_id=de.driver_id AND other.session_id<>%s)) LIMIT 1",
        (session_id, session_id, session_id, session_id),
    )
    if cur.fetchone():
        raise DemoRaceDeleteConflict("Demo race drivers are referenced by another session")
    cur.execute(
        "SELECT 1 FROM demo_race_entries de JOIN drivers d ON d.id=de.driver_id\n"
        "        LEFT JOIN team_memberships tm ON tm.driver_id=d.id\n"
        "        LEFT JOIN teams t ON t.principal_user_id=d.user_id\n"
        "        WHERE de.session_id=%s GROUP BY de.driver_id\n"
        "        HAVING count(DISTINCT tm.id)<>1 OR count(DISTINCT t.id)>0 LIMIT 1",
        (session_id,),
    )
    # Keep generated drivers that gained additional team or principal references.
    if cur.fetchone():
        raise DemoRaceDeleteConflict("Demo race drivers have additional team references")


def delete_demo_race_records(
    cur: Cursor[dict[str, Any]], session_id: UUID, marker: dict[str, Any]
) -> None:
    cur.execute("SELECT driver_id FROM demo_race_entries WHERE session_id=%s", (session_id,))
    driver_ids = [row["driver_id"] for row in cur.fetchall()]
    cur.execute(
        "SELECT d.user_id FROM demo_race_entries de JOIN drivers d ON d.id=de.driver_id "
        "WHERE de.session_id=%s AND d.user_id IS NOT NULL",
        (session_id,),
    )
    user_ids = [row["user_id"] for row in cur.fetchall()]
    cur.execute("DELETE FROM pit_reservations WHERE session_id=%s", (session_id,))
    cur.execute("DELETE FROM pit_boxes WHERE event_id=%s", (marker["event_id"],))
    cur.execute("DELETE FROM incident_reports WHERE session_id=%s", (session_id,))
    cur.execute("DELETE FROM session_results WHERE session_id=%s", (session_id,))
    # Generated drivers are unique to this race. Rebuild this championship's
    # derived standings after removing the race results so stale rows for those
    # drivers disappear and the remaining ranks stay correct.
    cur.execute("SELECT recalculate_standings(%s)", (marker["championship_id"],))
    cur.execute("DELETE FROM demo_race_entries WHERE session_id=%s", (session_id,))
    cur.execute("DELETE FROM demo_races WHERE session_id=%s", (session_id,))
    cur.execute("DELETE FROM race_sessions WHERE id=%s", (session_id,))
    cur.execute("DELETE FROM race_events WHERE id=%s", (marker["event_id"],))
    if driver_ids:
        cur.execute("DELETE FROM team_memberships WHERE driver_id=ANY(%s)", (driver_ids,))
        cur.execute("DELETE FROM drivers WHERE id=ANY(%s)", (driver_ids,))
    if user_ids:
        cur.execute("DELETE FROM users WHERE id=ANY(%s)", (user_ids,))


def create_demo_race_records(
    session_id: UUID,
    event_id: UUID,
    now: datetime,
    names: list[str],
    auto_repeat: bool,
    seed: int | None = None,
) -> tuple[list[dict[str, Any]], int]:
    generated: list[dict[str, Any]] = []
    rng = random.Random(seed) if seed is not None else random  # noqa: S311 -- deterministic simulation, not security
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT id FROM championships WHERE name='ApexGrid Live Demo' "
            "AND season=extract(year from current_date)::int"
        )
        championship = cur.fetchone()
        if not championship:
            cur.execute(
                "INSERT INTO championships(name,season) VALUES ('ApexGrid Live Demo',"
                "extract(year from current_date)::int) RETURNING id"
            )
            championship = cur.fetchone()
        cur.execute("SELECT id,name FROM circuits ORDER BY name")
        circuits = cur.fetchall()
        cur.execute("SELECT id,name FROM teams ORDER BY name")
        teams = cur.fetchall()
        if not circuits or not teams:
            raise DemoRaceSetupError("Demo race requires at least one circuit and one team")
        cur.execute("SELECT pg_advisory_xact_lock(hashtext('apexgrid-demo-race-create'))")
        cur.execute(
            "SELECT COALESCE(max(round_number),0)+1 AS round "
            "FROM race_events WHERE championship_id=%s",
            (championship["id"],),
        )
        round_number = cur.fetchone()["round"]
        numbers = rng.sample(range(11, 100), len(names))
        circuit = rng.choice(circuits)
        event_name = (
            f"{circuit['name']} Grand Prix — "
            f"{rng.choice(['Sprint Weekend', 'Night Race', 'Coastal Classic', 'Autumn Round'])}"
        )
        total_laps = rng.randint(45, MAX_SESSION_LAPS)
        cur.execute(
            "INSERT INTO race_events(id,championship_id,circuit_id,round_number,"
            "name,start_date) VALUES (%s,%s,%s,%s,%s,%s)",
            (event_id, championship["id"], circuit["id"], round_number, event_name, now),
        )
        cur.execute(
            "INSERT INTO race_sessions(id,event_id,session_type,state,scheduled_at,"
            "started_at,total_laps) "
            "VALUES (%s,%s,'RACE','ACTIVE',%s,%s,%s)",
            (session_id, event_id, now, now, total_laps),
        )
        cur.execute(
            "INSERT INTO demo_races(session_id,event_id,auto_repeat,simulation_seed) "
            "VALUES (%s,%s,%s,%s)",
            (session_id, event_id, auto_repeat, seed),
        )
        cur.execute(
            "INSERT INTO pit_boxes(event_id,number) SELECT %s,n FROM generate_series(1,4) AS n "
            "ON CONFLICT(event_id,number) DO NOTHING",
            (event_id,),
        )
        for idx, full_name in enumerate(names):
            number = numbers[idx]
            user_id, driver_id = uuid4(), uuid4()
            email = f"demo-{user_id.hex}@apexgrid.invalid"
            secret = secrets.token_urlsafe(40)
            password_hash = bcrypt.hashpw(secret.encode(), bcrypt.gensalt(rounds=10)).decode()
            cur.execute(
                "INSERT INTO users(id,email,password_hash,full_name,role) "
                "VALUES (%s,%s,%s,%s,'DRIVER')",
                (user_id, email, password_hash, full_name),
            )
            cur.execute(
                "INSERT INTO drivers(id,user_id,licence_number,number) VALUES (%s,%s,%s,%s)",
                (driver_id, user_id, f"AGD-{driver_id.hex[:12].upper()}", number),
            )
            team = teams[idx % len(teams)]
            cur.execute(
                "INSERT INTO team_memberships(driver_id,team_id,start_date) VALUES (%s,%s,%s)",
                (driver_id, team["id"], now.date()),
            )
            offset = rng.randint(-1200, 1600)
            cur.execute(
                "INSERT INTO demo_race_entries(session_id,driver_id,pace_offset_ms) "
                "VALUES (%s,%s,%s)",
                (session_id, driver_id, offset),
            )
            generated.append(
                {
                    "id": driver_id,
                    "number": number,
                    "pace_offset_ms": offset,
                    "team_id": team["id"],
                    "team_name": team["name"],
                }
            )
    return generated, total_laps


def get_demo_race_row(session_id: UUID | str) -> dict[str, Any] | None:
    return cast(
        dict[str, Any] | None,
        fetch_one(
            "SELECT s.id AS session_id,e.id AS event_id,e.name AS event_name,"
            "c.name AS circuit_name,\n"
            "            s.state,s.total_laps,(SELECT count(*) FROM "
            "demo_race_entries de WHERE de.session_id=s.id)::int AS car_count,\n"
            "            d.created_at FROM demo_races d JOIN race_sessions s "
            "ON s.id=d.session_id\n"
            "            JOIN race_events e ON e.id=d.event_id JOIN circuits c "
            "ON c.id=e.circuit_id WHERE s.id=%s",
            (session_id,),
        ),
    )


def list_demo_race_ids(limit: int, offset: int) -> list[dict[str, Any]]:
    return fetch_all(
        "SELECT session_id FROM demo_races ORDER BY created_at DESC LIMIT %s OFFSET %s",
        (limit, offset),
    )
