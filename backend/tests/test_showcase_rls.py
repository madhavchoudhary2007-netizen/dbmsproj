from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

import psycopg
import pytest


def _guarded_fixture_url() -> str:
    url = os.environ.get("SHOWCASE_TEST_DATABASE_URL")
    if not url:
        pytest.fail("SHOWCASE_TEST_DATABASE_URL must explicitly name the disposable apexgrid database")

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


@pytest.mark.parametrize(
    "url",
    [
        None,
        "postgresql://test:test@example.com:15432/apexgrid",
        "postgresql://test:test@localhost:5432/apexgrid",
        "postgresql://test:test@localhost:15432/other",
    ],
)
def test_fixture_guard_rejects_unsafe_database_urls(
    monkeypatch: pytest.MonkeyPatch, url: str | None
) -> None:
    if url is None:
        monkeypatch.delenv("SHOWCASE_TEST_DATABASE_URL", raising=False)
    else:
        monkeypatch.setenv("SHOWCASE_TEST_DATABASE_URL", url)

    with pytest.raises(pytest.fail.Exception):
        _guarded_fixture_url()


@pytest.mark.parametrize(
    "url",
    [
        "postgresql://synthetic:synthetic@localhost:15432/apexgrid",
        "postgres://synthetic:synthetic@127.0.0.1:15432/apexgrid",
    ],
)
def test_fixture_guard_accepts_only_harmless_local_target(
    monkeypatch: pytest.MonkeyPatch, url: str
) -> None:
    monkeypatch.setenv("SHOWCASE_TEST_DATABASE_URL", url)

    assert _guarded_fixture_url() == url


def _set_test_role_context(conn: psycopg.Connection[object], role: str) -> None:
    if role not in {"admin", "steward"}:
        raise ValueError("unsupported synthetic role context")
    conn.execute("SELECT set_config('apexgrid.role', %s, true)", (role,))


def test_restricted_role_rls_exposes_only_owned_penalty_audit_row() -> None:
    url = _guarded_fixture_url()
    tag = f"rls-test-{uuid4().hex}"
    conn = psycopg.connect(url, connect_timeout=3)
    try:
        conn.execute("BEGIN")
        migration_path = Path(__file__).resolve().parents[1] / "migrations" / "009_audit_rls_scope.sql"
        migration_sql = migration_path.read_text(encoding="utf-8")
        for _ in range(2):
            for statement in migration_sql.split(";"):
                if statement.strip():
                    conn.execute(statement)

        for table_name in ("penalties", "championships"):
            conn.execute(
                """
                INSERT INTO audit_log (table_name, op, row_pk, new, actor)
                VALUES (%s, 'INSERT', jsonb_build_object('test_tag', %s::text),
                        jsonb_build_object('test_tag', %s::text), %s)
                """,
                (table_name, tag, tag, "synthetic-rls-test"),
            )

        conn.execute("SET LOCAL ROLE apexgrid_app")
        _set_test_role_context(conn, "steward")
        steward_rows = conn.execute(
            """
            SELECT table_name, row_pk->>'test_tag'
            FROM audit_log
            WHERE row_pk->>'test_tag' = %s
            ORDER BY table_name
            """,
            (tag,),
        ).fetchall()
        assert steward_rows == [("penalties", tag)]

        _set_test_role_context(conn, "admin")
        admin_rows = conn.execute(
            """
            SELECT table_name, row_pk->>'test_tag'
            FROM audit_log
            WHERE row_pk->>'test_tag' = %s
            ORDER BY table_name
            """,
            (tag,),
        ).fetchall()
        assert admin_rows == [("championships", tag), ("penalties", tag)]

        conn.execute("SELECT set_config('apexgrid.role', 'unknown', true)")
        unknown_rows = conn.execute(
            "SELECT table_name FROM audit_log WHERE row_pk->>'test_tag' = %s", (tag,)
        ).fetchall()
        assert unknown_rows == []

        conn.execute("RESET apexgrid.role")
        absent_rows = conn.execute(
            "SELECT table_name FROM audit_log WHERE row_pk->>'test_tag' = %s", (tag,)
        ).fetchall()
        assert absent_rows == []
    finally:
        conn.rollback()
        conn.close()
