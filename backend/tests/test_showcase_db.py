from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path
import os
import threading
from urllib.parse import urlparse
from uuid import uuid4

import psycopg
from psycopg import sql
import pytest
from fastapi.testclient import TestClient


def _fixture_url() -> str:
    url = os.environ.get("SHOWCASE_TEST_DATABASE_URL")
    if not url:
        pytest.fail("SHOWCASE_TEST_DATABASE_URL must explicitly name the disposable apexgrid database")
    parsed = urlparse(url)
    if (
        parsed.scheme not in {"postgres", "postgresql"}
        or parsed.hostname not in {"127.0.0.1", "localhost"}
        or parsed.port != 15432
        or parsed.path.lstrip("/") != "apexgrid"
    ):
        pytest.fail(
            "SHOWCASE_TEST_DATABASE_URL must target apexgrid on 127.0.0.1 or localhost:15432"
        )
    return url


@pytest.fixture
def showcase_client(monkeypatch: pytest.MonkeyPatch) -> tuple[TestClient, list[int]]:
    url = _fixture_url()
    monkeypatch.setenv("DATABASE_URL", url)
    from backend.app.api import dbms_showcase
    from backend.app.api.laps import current_user
    from backend.app.main import app

    backend_pids: list[int] = []

    @contextmanager
    def explicit_fixture_connection():
        with psycopg.connect(url, connect_timeout=3) as conn:
            backend_pids.append(conn.info.backend_pid)
            yield conn

    app.dependency_overrides.clear()
    app.dependency_overrides[current_user] = lambda: {
        "id": "synthetic-showcase-db-admin",
        "email": "showcase-db-admin@example.invalid",
        "role": "ADMIN",
    }
    monkeypatch.setattr(dbms_showcase, "connection", explicit_fixture_connection)
    client = TestClient(app)
    try:
        yield client, backend_pids
    finally:
        client.close()
        app.dependency_overrides.clear()


@pytest.fixture
def owned_table() -> str:
    url = _fixture_url()
    table = f"showcase_concurrency_{uuid4().hex}"
    ident = sql.Identifier(table)
    with psycopg.connect(url, connect_timeout=3) as conn:
        conn.execute(sql.SQL("CREATE TABLE {} (id integer PRIMARY KEY, balance integer NOT NULL)").format(ident))
        conn.execute(sql.SQL("INSERT INTO {} (id, balance) VALUES (1, 314), (2, 271)").format(ident))
    try:
        yield table
    finally:
        with psycopg.connect(url, connect_timeout=3) as conn:
            conn.execute(sql.SQL("DROP TABLE IF EXISTS {} ").format(ident))


@pytest.mark.parametrize(
    ("level", "expected_second_read"),
    [("read committed", 271), ("repeatable read", 314), ("serializable", 314)],
)
def test_real_sessions_observe_requested_isolation(
    owned_table: str, level: str, expected_second_read: int
) -> None:
    url = _fixture_url()
    table = sql.Identifier(owned_table)
    first = psycopg.connect(url, connect_timeout=3)
    second = psycopg.connect(url, connect_timeout=3)
    try:
        assert first.info.backend_pid != second.info.backend_pid
        first.execute(sql.SQL("SET TRANSACTION ISOLATION LEVEL " + level.upper()))
        first.execute("SET LOCAL statement_timeout = '8s'")
        initial = first.execute(sql.SQL("SELECT balance FROM {} WHERE id = 1").format(table)).fetchone()
        assert initial == (314,)

        second.execute("SET LOCAL statement_timeout = '8s'")
        second.execute(sql.SQL("UPDATE {} SET balance = 271 WHERE id = 1").format(table))
        second.commit()

        observed = first.execute(sql.SQL("SELECT balance FROM {} WHERE id = 1").format(table)).fetchone()
        assert observed == (expected_second_read,)
        first.rollback()
    finally:
        first.close()
        second.close()


def test_real_postgres_deadlock_reports_40p01_and_cleans_up(owned_table: str) -> None:
    url = _fixture_url()
    table = sql.Identifier(owned_table)
    rendezvous = threading.Barrier(2)

    def cross_update(own_id: int, other_id: int) -> str:
        with psycopg.connect(url, connect_timeout=3) as conn:
            conn.execute("SET LOCAL lock_timeout = '7s'")
            conn.execute("SET LOCAL statement_timeout = '9s'")
            conn.execute(sql.SQL("UPDATE {} SET balance = balance + 1 WHERE id = %s").format(table), (own_id,))
            rendezvous.wait(timeout=3)
            conn.execute(sql.SQL("UPDATE {} SET balance = balance + 1 WHERE id = %s").format(table), (other_id,))
        return "committed"

    outcomes: list[str] = []
    with ThreadPoolExecutor(max_workers=2) as workers:
        futures = [workers.submit(cross_update, 1, 2), workers.submit(cross_update, 2, 1)]
        for future in futures:
            try:
                outcomes.append(future.result(timeout=12))
            except psycopg.Error as error:
                outcomes.append(error.sqlstate or "unknown")

    assert outcomes.count("40P01") == 1, outcomes
    assert outcomes.count("committed") == 1, outcomes
    with psycopg.connect(url, connect_timeout=3) as verify:
        rows = verify.execute(sql.SQL("SELECT id, balance FROM {} ORDER BY id").format(table)).fetchall()
    assert len(rows) == 2


@pytest.mark.parametrize(
    ("level", "must_repeat"),
    [("read_committed", False), ("repeatable_read", True), ("serializable", True)],
)
def test_showcase_isolation_endpoint_reports_real_observations(
    showcase_client: tuple[TestClient, list[int]], level: str, must_repeat: bool
) -> None:
    client, backend_pids = showcase_client
    response = client.get(f"/api/dbms/isolation-demo?level={level}")

    assert response.status_code == 200, response.text
    assert len(set(backend_pids)) >= 2, backend_pids
    result = response.json()
    assert result["level"] == level
    observed = result["observed_reads"]
    assert len(observed) >= 2
    first_balance = observed[0]["balance"]
    second_balance = observed[1]["balance"]
    assert (first_balance == second_balance) is must_repeat
    assert result["anomaly_detected"] is (not must_repeat)


def test_showcase_deadlock_endpoint_reports_postgres_victim(
    showcase_client: tuple[TestClient, list[int]],
) -> None:
    client, backend_pids = showcase_client
    response = client.post("/api/dbms/deadlock-demo")

    assert response.status_code == 200, response.text
    assert len(set(backend_pids)) >= 2, backend_pids
    result = response.json()
    assert result["sqlstate"] == "40P01"
    assert result["aborted_transaction"] in {"T1", "T2", 1, 2}
