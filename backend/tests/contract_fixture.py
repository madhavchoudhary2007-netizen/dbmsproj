from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import UTC, date, datetime, timedelta
from secrets import token_urlsafe
from urllib.parse import urlparse
from uuid import NAMESPACE_URL, uuid5

import jwt
import psycopg
from fastapi.testclient import TestClient
from psycopg.rows import dict_row
from pymongo import MongoClient
from pytest import MonkeyPatch


def _fixture_id(resource: str):
    return uuid5(NAMESPACE_URL, "apexgrid.contract." + resource)


class _RealConnectionPool:
    closed = False

    def __init__(self, conn):
        self.conn = conn

    @contextmanager
    def connection(self):
        yield self.conn


def _mongo_uri() -> str:
    uri = os.environ.get("MONGODB_URL", "")
    parsed = urlparse(uri)
    safe_scheme = parsed.scheme in {"mongodb", "mongodb+srv"}
    local = parsed.hostname in {"localhost", "127.0.0.1"}
    safe_port = parsed.port == 27018 or (
        parsed.port == 27017
        and os.environ.get("GITHUB_ACTIONS") == "true"
        and os.environ.get("CI") == "true"
    )
    if not (safe_scheme and local and safe_port):
        raise RuntimeError("refusing MongoDB access outside the disposable local test stack")
    return uri


def capture_contracts() -> dict[str, object]:
    from backend.app import database, main
    from backend.tests.test_token_revocation_db import _require_disposable_test_stack

    database_url = _require_disposable_test_stack()
    mongo_uri = _mongo_uri()
    conn = psycopg.connect(database_url, row_factory=dict_row)
    conn.autocommit = False
    mongo = MongoClient(mongo_uri)
    names = ("admin", "driver_user", "team", "driver") + (
        "championship",
        "circuit",
        "event",
        "session",
    )
    ids = {name: _fixture_id(name) for name in names}
    admin, driver_user, team, driver, championship, circuit, event, session = (
        ids[name] for name in names
    )
    fixed = datetime(2026, 1, 1, tzinfo=UTC)
    try:
        for user_id, email, name, role in (
            (ids["admin"], "contract-admin@example.invalid", "Contract Admin", "ADMIN"),
            (ids["driver_user"], "contract-driver@example.invalid", "Contract Driver", "DRIVER"),
        ):
            conn.execute(
                "INSERT INTO users(id,email,password_hash,full_name,role,created_at) "
                "VALUES (%s,%s,%s,%s,%s,%s)",
                (user_id, email, "fixture-placeholder", name, role, fixed),
            )
        queries = [
            "INSERT INTO teams(id,name,principal_user_id) VALUES (%s,%s,NULL)",
            "INSERT INTO drivers(id,user_id,licence_number,number) VALUES (%s,%s,%s,%s)",
            "INSERT INTO team_memberships(driver_id,team_id,start_date) VALUES (%s,%s,%s)",
            "INSERT INTO championships(id,name,season) VALUES (%s,%s,%s)",
            "INSERT INTO circuits(id,name,country,length_km) VALUES (%s,%s,%s,%s)",
            "INSERT INTO race_events(id,championship_id,circuit_id,round_number,name,start_date) "
            "VALUES (%s,%s,%s,%s,%s,%s)",
            "INSERT INTO race_sessions(id,event_id,session_type,state,scheduled_at,total_laps) "
            "VALUES (%s,%s,%s,%s,%s,%s)",
        ]
        rows = [
            (team, "Contract Team"),
            (driver, driver_user, "CONTRACT-001", 91),
            (driver, team, date(2025, 1, 1)),
            (championship, "Contract Championship", 2026),
            (circuit, "Contract Circuit", "Fixtureland", 5.2),
            (event, championship, circuit, 1, "Contract Event", fixed),
            (session, event, "RACE", "SCHEDULED", fixed, 5),
        ]
        for sql, params in zip(queries, rows, strict=True):
            conn.execute(sql, params)
        mongo_collection = mongo["apexgrid"]["telemetry"]
        secret = token_urlsafe(32)
        claims = {
            "sub": str(ids["admin"]),
            "role": "ADMIN",
            "exp": datetime.now(UTC) + timedelta(minutes=10),
        }
        token = jwt.encode(claims, secret, algorithm="HS256")
        with MonkeyPatch.context() as patch:
            patch.setattr(database, "pool", _RealConnectionPool(conn))
            patch.setattr(main, "JWT_SECRET", secret)
            patch.setattr(main.app.state, "runtime_lease", None, raising=False)
            patch.setattr(main, "telemetry_collection", mongo_collection)
            client = TestClient(main.app)
            try:
                headers = {"Authorization": f"Bearer {token}"}
                resources = [
                    ("championships", "championship"),
                    ("circuits", "circuit"),
                    ("teams", "team"),
                    ("drivers", "driver"),
                    ("events", "event"),
                    ("sessions", "session"),
                    ("users", "admin"),
                ]
                paths = ["/api/auth/me"] + [
                    f"/api/{resource}/{ids[key]}" for resource, key in resources
                ]
                paths += [f"/api/sessions/{ids['session']}/{suffix}" for suffix in ("live", "laps")]
                responses = {}
                for path in paths:
                    response = client.get(path, headers=headers)
                    if response.status_code != 200:
                        raise AssertionError(f"{path} returned HTTP {response.status_code}")
                    responses[path] = response.json()
                return responses
            finally:
                client.close()
    finally:
        conn.rollback()
        conn.close()
        mongo.close()
