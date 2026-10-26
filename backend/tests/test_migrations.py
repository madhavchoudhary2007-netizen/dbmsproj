from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, cast

import psycopg
import pytest

from backend.app.migrations import (
    _backfill_existing_migrations,
    _ensure_ledger_table,
    _load_ledger,
    apply_migrations,
    compute_checksum,
)


class MockCursor:
    def __init__(
        self,
        fetchone_result: Any = None,
        fetchall_results: list[dict[str, Any]] | None = None,
    ) -> None:
        self.executed: list[tuple[str, tuple[Any, ...]]] = []
        self._fetchone_result = fetchone_result
        self._fetchall_results = fetchall_results or []

    def __enter__(self) -> MockCursor:
        return self

    def __exit__(self, *args: Any) -> None:
        pass

    def execute(self, query: str, params: tuple[Any, ...] | None = None) -> None:
        self.executed.append((query, params or ()))

    def fetchone(self) -> Any:
        return self._fetchone_result

    def fetchall(self) -> list[dict[str, Any]]:
        return self._fetchall_results


class MockTransaction:
    def __enter__(self) -> MockTransaction:
        return self

    def __exit__(self, *args: Any) -> None:
        pass


class MockConnection:
    def __init__(
        self,
        *,
        table_exists: bool = False,
        ledger_rows: list[dict[str, str]] | None = None,
    ) -> None:
        self.executed: list[tuple[str, tuple[Any, ...]]] = []
        self.table_exists = table_exists
        self.ledger_rows: list[dict[str, Any]] = (
            [dict(row) for row in ledger_rows] if ledger_rows else []
        )

    def transaction(self) -> MockTransaction:
        return MockTransaction()

    def execute(self, query: str, params: tuple[Any, ...] | None = None) -> None:
        self.executed.append((query, params or ()))

    def cursor(self, row_factory: Any = None) -> MockCursor:
        if row_factory is not None:
            return MockCursor(fetchall_results=self.ledger_rows)
        fetchone_val: Any = (1,) if self.table_exists else None
        return MockCursor(fetchone_result=fetchone_val)


# ---------------------------------------------------------------------------
# compute_checksum Tests
# ---------------------------------------------------------------------------


def test_compute_checksum_known_digest(tmp_path: Path) -> None:
    sample_content = b"CREATE TABLE test_table (id serial PRIMARY KEY);\n"
    expected_hash = hashlib.sha256(sample_content).hexdigest()

    test_file = tmp_path / "001_test.sql"
    test_file.write_bytes(sample_content)

    digest = compute_checksum(test_file)
    assert digest == expected_hash
    assert len(digest) == 64


def test_compute_checksum_distinct_files(tmp_path: Path) -> None:
    file_a = tmp_path / "a.sql"
    file_b = tmp_path / "b.sql"
    file_a.write_text("SELECT 1;", encoding="utf-8")
    file_b.write_text("SELECT 2;", encoding="utf-8")

    digest_a = compute_checksum(file_a)
    digest_b = compute_checksum(file_b)

    assert digest_a != digest_b
    assert digest_a == hashlib.sha256(b"SELECT 1;").hexdigest()
    assert digest_b == hashlib.sha256(b"SELECT 2;").hexdigest()


# ---------------------------------------------------------------------------
# Migration Sorting / Version Ordering Tests
# ---------------------------------------------------------------------------


def test_apply_migrations_sorts_in_version_order(tmp_path: Path) -> None:
    (tmp_path / "003_third.sql").write_text("SELECT 3;", encoding="utf-8")
    (tmp_path / "001_first.sql").write_text("SELECT 1;", encoding="utf-8")
    (tmp_path / "002_second.sql").write_text("SELECT 2;", encoding="utf-8")
    (tmp_path / "010_tenth.sql").write_text("SELECT 10;", encoding="utf-8")
    (tmp_path / "not_a_migration.txt").write_text("IGNORED", encoding="utf-8")

    mock_conn = MockConnection()
    conn = cast(psycopg.Connection[Any], mock_conn)

    applied = apply_migrations(conn, tmp_path)

    expected_order = [
        "001_first.sql",
        "002_second.sql",
        "003_third.sql",
        "010_tenth.sql",
    ]
    assert applied == expected_order

    executed_sqls = [call[0] for call in mock_conn.executed if "SELECT" in call[0]]
    assert executed_sqls == ["SELECT 1;", "SELECT 2;", "SELECT 3;", "SELECT 10;"]


def test_apply_migrations_empty_directory(tmp_path: Path) -> None:
    mock_conn = MockConnection()
    conn = cast(psycopg.Connection[Any], mock_conn)

    applied = apply_migrations(conn, tmp_path)
    assert applied == []


# ---------------------------------------------------------------------------
# Checksum Mismatch Detection Tests
# ---------------------------------------------------------------------------


def test_apply_migrations_raises_on_checksum_mismatch(tmp_path: Path) -> None:
    mig_file = tmp_path / "001_initial.sql"
    mig_file.write_text("CREATE TABLE test (id int);", encoding="utf-8")
    current_hash = compute_checksum(mig_file)

    recorded_fake_hash = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"

    mock_conn = MockConnection(
        ledger_rows=[{"version": "001_initial.sql", "checksum": recorded_fake_hash}]
    )
    conn = cast(psycopg.Connection[Any], mock_conn)

    with pytest.raises(RuntimeError) as exc_info:
        apply_migrations(conn, tmp_path)

    err_msg = str(exc_info.value)
    assert "Checksum mismatch for migration 001_initial.sql" in err_msg
    assert f"expected {recorded_fake_hash}" in err_msg
    assert f"got {current_hash}" in err_msg


def test_apply_migrations_skips_matching_checksum(tmp_path: Path) -> None:
    mig_1 = tmp_path / "001_initial.sql"
    mig_1.write_text("SELECT 1;", encoding="utf-8")
    checksum_1 = compute_checksum(mig_1)

    mig_2 = tmp_path / "002_second.sql"
    mig_2.write_text("SELECT 2;", encoding="utf-8")

    mock_conn = MockConnection(ledger_rows=[{"version": "001_initial.sql", "checksum": checksum_1}])
    conn = cast(psycopg.Connection[Any], mock_conn)

    applied = apply_migrations(conn, tmp_path)
    assert applied == ["002_second.sql"]


# ---------------------------------------------------------------------------
# Mock Connection Ledger Operations Tests
# ---------------------------------------------------------------------------


def test_ensure_ledger_table() -> None:
    mock_conn = MockConnection()
    conn = cast(psycopg.Connection[Any], mock_conn)

    _ensure_ledger_table(conn)

    assert any(
        "CREATE TABLE IF NOT EXISTS schema_migrations" in call[0] for call in mock_conn.executed
    )


def test_load_ledger() -> None:
    mock_conn = MockConnection(
        ledger_rows=[
            {"version": "001_initial.sql", "checksum": "hash1"},
            {"version": "002_classified_bonus.sql", "checksum": "hash2"},
        ]
    )
    conn = cast(psycopg.Connection[Any], mock_conn)

    ledger = _load_ledger(conn)
    assert ledger == {
        "001_initial.sql": "hash1",
        "002_classified_bonus.sql": "hash2",
    }


def test_backfill_existing_migrations_no_championships() -> None:
    mock_conn = MockConnection(table_exists=False)
    conn = cast(psycopg.Connection[Any], mock_conn)

    applied_ledger: dict[str, str] = {}
    migrations = [Path("backend/migrations/001_initial.sql")]

    _backfill_existing_migrations(conn, migrations, applied_ledger)
    assert applied_ledger == {}
    assert len(mock_conn.executed) == 0


def test_backfill_existing_migrations_with_championships(tmp_path: Path) -> None:
    mig_1 = tmp_path / "001_initial.sql"
    mig_1.write_text("SELECT 1;", encoding="utf-8")
    mig_2 = tmp_path / "002_bonus.sql"
    mig_2.write_text("SELECT 2;", encoding="utf-8")
    mig_4 = tmp_path / "004_revocation.sql"
    mig_4.write_text("SELECT 4;", encoding="utf-8")

    mock_conn = MockConnection(table_exists=True)
    conn = cast(psycopg.Connection[Any], mock_conn)

    applied_ledger: dict[str, str] = {}
    migrations = [mig_1, mig_2, mig_4]

    _backfill_existing_migrations(conn, migrations, applied_ledger)

    assert "001_initial.sql" in applied_ledger
    assert "002_bonus.sql" in applied_ledger
    assert "004_revocation.sql" not in applied_ledger

    insert_calls = [
        call for call in mock_conn.executed if "INSERT INTO schema_migrations" in call[0]
    ]
    assert len(insert_calls) == 2


# ---------------------------------------------------------------------------
# Migration File Integrity Tests
# ---------------------------------------------------------------------------


def test_migration_files_integrity() -> None:
    migrations_dir = Path("backend/migrations")
    assert migrations_dir.is_dir(), "backend/migrations directory must exist"

    sql_files = sorted(migrations_dir.glob("*.sql"))
    assert len(sql_files) >= 5, f"Expected at least 5 migration files, found {len(sql_files)}"

    expected_prefixes = ("001_", "002_", "003_", "004_", "005_")
    found_prefixes = [f.name[:4] for f in sql_files]
    for prefix in expected_prefixes:
        assert prefix in found_prefixes, f"Missing migration file starting with {prefix}"

    for sql_file in sql_files:
        assert sql_file.is_file(), f"{sql_file} must be a file"
        size = sql_file.stat().st_size
        assert size > 0, f"Migration {sql_file.name} must not be empty"

        content = sql_file.read_text(encoding="utf-8")
        assert len(content.strip()) > 0, f"Migration {sql_file.name} has no text content"

        digest1 = compute_checksum(sql_file)
        digest2 = compute_checksum(sql_file)
        assert digest1 == digest2
        assert len(digest1) == 64
