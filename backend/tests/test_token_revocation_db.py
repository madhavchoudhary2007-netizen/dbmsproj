import os
import sys
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

import psycopg
import pytest
from psycopg.rows import dict_row

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app import token_revocation


def _require_disposable_test_stack() -> str:
    database_url = os.environ.get("DATABASE_URL", "")
    parsed = urlparse(database_url)
    database = parsed.path.removeprefix("/")
    port = parsed.port
    safe_url = parsed.scheme in {"postgres", "postgresql"} and parsed.hostname in {
        "localhost",
        "127.0.0.1",
    }
    local_test_stack = (
        safe_url
        and os.environ.get("APEXGRID_TEST_STACK") == "1"
        and port == 15432
        and database == "apexgrid"
    )
    isolated_ci_service = (
        safe_url
        and os.environ.get("GITHUB_ACTIONS") == "true"
        and os.environ.get("CI") == "true"
        and port == 5432
        and database == "apexgrid_test"
    )
    if not (local_test_stack or isolated_ci_service):
        pytest.fail("refusing database access outside the disposable apexgrid-test stack")
    return database_url


@pytest.fixture
def db_conn():
    database_url = _require_disposable_test_stack()
    conn = psycopg.connect(database_url, row_factory=dict_row)
    conn.autocommit = False
    try:
        yield conn
    finally:
        conn.rollback()
        conn.close()


@pytest.fixture
def repository(db_conn, monkeypatch):
    @contextmanager
    def connection():
        yield db_conn

    def fetch_one(query, params=()):
        row = db_conn.execute(query, params).fetchone()
        return dict(row) if row else None

    monkeypatch.setattr(token_revocation, "connection", connection)
    monkeypatch.setattr(token_revocation, "fetch_one", fetch_one)
    return db_conn


def _insert(conn, jti: str, expires_at: datetime) -> None:
    conn.execute(
        "INSERT INTO revoked_tokens (jti, expires_at) VALUES (%s, %s)",
        (token_revocation.revocation_key(jti), expires_at),
    )


def _count(conn, jti: str) -> int:
    return conn.execute(
        "SELECT count(*) FROM revoked_tokens WHERE jti = %s",
        (token_revocation.revocation_key(jti),),
    ).fetchone()["count"]


def test_revoke_is_idempotent_and_lookup_reports_present_and_absent(repository):
    jti = str(uuid4())
    expiry = datetime.now(UTC) + timedelta(minutes=10)

    token_revocation.revoke_token(jti, expiry)
    token_revocation.revoke_token(jti, expiry)

    assert token_revocation.is_revoked(jti) is True
    assert token_revocation.is_revoked(str(uuid4())) is False
    assert _count(repository, jti) == 1


def test_lookup_ignores_expired_revocation(repository):
    jti = str(uuid4())
    _insert(repository, jti, datetime.now(UTC) - timedelta(seconds=1))

    assert token_revocation.is_revoked(jti) is False


def test_purge_removes_expired_rows_and_preserves_live_rows(repository):
    expired_jti = str(uuid4())
    live_jti = str(uuid4())
    _insert(repository, expired_jti, datetime.now(UTC) - timedelta(seconds=1))
    _insert(repository, live_jti, datetime.now(UTC) + timedelta(minutes=10))

    token_revocation.purge_expired_revocations()

    assert token_revocation.is_revoked(expired_jti) is False
    assert token_revocation.is_revoked(live_jti) is True
    assert _count(repository, expired_jti) == 0
    assert _count(repository, live_jti) == 1


def test_migration_columns_constraints_and_expiry_index(repository):
    columns = repository.execute(
        "SELECT column_name, data_type, is_nullable FROM information_schema.columns "
        "WHERE table_schema = current_schema() AND table_name = 'revoked_tokens'"
    ).fetchall()
    assert {row["column_name"]: (row["data_type"], row["is_nullable"]) for row in columns} == {
        "jti": ("uuid", "NO"),
        "expires_at": ("timestamp with time zone", "NO"),
    }
    primary_key = repository.execute(
        "SELECT column_name FROM information_schema.key_column_usage "
        "WHERE table_schema = current_schema() AND table_name = 'revoked_tokens' "
        "AND constraint_name IN (SELECT constraint_name FROM information_schema.table_constraints "
        "WHERE table_schema = current_schema() AND table_name = 'revoked_tokens' "
        "AND constraint_type = 'PRIMARY KEY')"
    ).fetchall()
    assert [row["column_name"] for row in primary_key] == ["jti"]
    indexes = repository.execute(
        "SELECT indexdef FROM pg_indexes "
        "WHERE schemaname = current_schema() AND tablename = 'revoked_tokens'"
    ).fetchall()
    definitions = [row["indexdef"].lower() for row in indexes]
    assert any("revoked_tokens_expires_at_idx" in definition for definition in definitions)
    assert any("(expires_at)" in definition for definition in definitions)
