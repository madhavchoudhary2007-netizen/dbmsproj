from __future__ import annotations

import random
import secrets
from datetime import datetime
from typing import Any, cast
from uuid import UUID, uuid4

import bcrypt
from psycopg.rows import dict_row

from .database import connection, fetch_all, fetch_one
from .simulation_core import MAX_SESSION_LAPS


class DemoRaceSetupError(Exception):
    pass


def create_demo_race_records(
    session_id: UUID,
    event_id: UUID,
    now: datetime,
    names: list[str],
    auto_repeat: bool,
) -> tuple[list[dict[str, Any]], int]:
    generated: list[dict[str, Any]] = []
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT id FROM championships WHERE name='ApexGrid Live Demo' "
            "AND season=extract(year from current_date)::int"
        )
        championship = cur.fetchone()
        if not championship:
            cur.execute("INSERT INTO championships(name,season) VALUES ('ApexGrid Live Demo',extract(year from current_date)::int) RETURNING id")
            championship = cur.fetchone()
        cur.execute("SELECT id,name FROM circuits ORDER BY name")
        circuits = cur.fetchall()
        cur.execute("SELECT id,name FROM teams ORDER BY name")
        teams = cur.fetchall()
        if not circuits or not teams:
            raise DemoRaceSetupError("Demo race requires at least one circuit and one team")
        cur.execute("SELECT pg_advisory_xact_lock(hashtext('apexgrid-demo-race-create'))")
        cur.execute("SELECT COALESCE(max(round_number),0)+1 AS round FROM race_events WHERE championship_id=%s", (championship["id"],))
        round_number = cur.fetchone()["round"]
        numbers = random.sample(range(11, 100), len(names))
        circuit = random.choice(circuits)
        event_name = f"{circuit['name']} Grand Prix — {random.choice(['Sprint Weekend', 'Night Race', 'Coastal Classic', 'Autumn Round'])}"
        total_laps = random.randint(45, MAX_SESSION_LAPS)
        cur.execute("INSERT INTO race_events(id,championship_id,circuit_id,round_number,name,start_date) VALUES (%s,%s,%s,%s,%s,%s)", (event_id, championship["id"], circuit["id"], round_number, event_name, now))
        cur.execute("INSERT INTO race_sessions(id,event_id,session_type,state,scheduled_at,started_at,total_laps) VALUES (%s,%s,'RACE','ACTIVE',%s,%s,%s)", (session_id,event_id,now,now,total_laps))
        cur.execute("INSERT INTO demo_races(session_id,event_id,auto_repeat) VALUES (%s,%s,%s)", (session_id,event_id,auto_repeat))
        cur.execute("INSERT INTO pit_boxes(event_id,number) SELECT %s,n FROM generate_series(1,4) AS n ON CONFLICT(event_id,number) DO NOTHING", (event_id,))
        for idx, full_name in enumerate(names):
            number = numbers[idx]
            user_id, driver_id = uuid4(), uuid4()
            email = f"demo-{user_id.hex}@apexgrid.invalid"
            secret = secrets.token_urlsafe(40)
            password_hash = bcrypt.hashpw(secret.encode(), bcrypt.gensalt(rounds=10)).decode()
            cur.execute("INSERT INTO users(id,email,password_hash,full_name,role) VALUES (%s,%s,%s,%s,'DRIVER')", (user_id,email,password_hash,full_name))
            cur.execute("INSERT INTO drivers(id,user_id,licence_number,number) VALUES (%s,%s,%s,%s)", (driver_id,user_id,f"AGD-{driver_id.hex[:12].upper()}",number))
            team = teams[idx % len(teams)]
            cur.execute("INSERT INTO team_memberships(driver_id,team_id,start_date) VALUES (%s,%s,%s)", (driver_id,team["id"],now.date()))
            offset = random.randint(-1200, 1600)
            cur.execute("INSERT INTO demo_race_entries(session_id,driver_id,pace_offset_ms) VALUES (%s,%s,%s)", (session_id,driver_id,offset))
            generated.append({"id":driver_id,"number":number,"pace_offset_ms":offset,
                              "team_id":team["id"],"team_name":team["name"]})
    return generated, total_laps


def get_demo_race_row(session_id: UUID | str) -> dict[str, Any] | None:
    return cast(
        dict[str, Any] | None,
        fetch_one(
            """SELECT s.id AS session_id,e.id AS event_id,e.name AS event_name,c.name AS circuit_name,
            s.state,s.total_laps,(SELECT count(*) FROM demo_race_entries de WHERE de.session_id=s.id)::int AS car_count,
            d.created_at FROM demo_races d JOIN race_sessions s ON s.id=d.session_id
            JOIN race_events e ON e.id=d.event_id JOIN circuits c ON c.id=e.circuit_id WHERE s.id=%s""",
            (session_id,),
        ),
    )


def list_demo_race_ids(limit: int, offset: int) -> list[dict[str, Any]]:
    return fetch_all(
        "SELECT session_id FROM demo_races ORDER BY created_at DESC LIMIT %s OFFSET %s",
        (limit, offset),
    )
