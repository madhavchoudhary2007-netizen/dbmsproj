from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row


def compute_checksum(path: Path) -> str:
    """Calculate the SHA-256 hex digest of a migration file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _table_exists(conn: psycopg.Connection[Any], table_name: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            """SELECT 1 FROM information_schema.tables
            WHERE table_schema='public' AND table_name=%s""",
            (table_name,),
        )
        return cur.fetchone() is not None


def _column_exists(conn: psycopg.Connection[Any], table_name: str, column_name: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            """SELECT 1 FROM information_schema.columns
            WHERE table_schema='public' AND table_name=%s AND column_name=%s""",
            (table_name, column_name),
        )
        return cur.fetchone() is not None


def _proc_exists(conn: psycopg.Connection[Any], proc_name: str) -> bool:
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_proc WHERE proname=%s", (proc_name,))
        return cur.fetchone() is not None


def _sentinel_verified(conn: psycopg.Connection[Any], version: str) -> bool:
    if version.startswith("001"):
        return _table_exists(conn, "championships")
    if version.startswith("002"):
        return _proc_exists(conn, "recalculate_standings") or _table_exists(conn, "championships")
    if version.startswith("003"):
        return _column_exists(conn, "demo_races", "simulation_seed") or _table_exists(
            conn, "demo_races"
        )
    return False


def _ensure_ledger_table(conn: psycopg.Connection[Any]) -> None:
    with conn.transaction():
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(64) PRIMARY KEY,
                checksum VARCHAR(64) NOT NULL,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            """
        )


def _load_ledger(conn: psycopg.Connection[Any]) -> dict[str, str]:
    ledger: dict[str, str] = {}
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT version, checksum FROM schema_migrations")
        for row in cur.fetchall():
            ledger[str(row["version"])] = str(row["checksum"])
    return ledger


def _backfill_existing_migrations(
    conn: psycopg.Connection[Any],
    migrations: list[Path],
    applied_ledger: dict[str, str],
) -> None:
    if not _table_exists(conn, "championships"):
        return
    with conn.transaction():
        for migration in migrations:
            version = migration.name
            if version in applied_ledger or migration.stem in applied_ledger:
                continue
            if not (
                version.startswith("001") or version.startswith("002") or version.startswith("003")
            ):
                continue
            if _sentinel_verified(conn, version):
                checksum = compute_checksum(migration)
                conn.execute(
                    """
                    INSERT INTO schema_migrations (version, checksum, applied_at)
                    VALUES (%s, %s, NOW())
                    ON CONFLICT (version) DO NOTHING
                    """,
                    (version, checksum),
                )
                applied_ledger[version] = checksum


def apply_migrations(
    conn: psycopg.Connection[Any],
    migrations_dir: Path,
    *,
    seed_path: Path | None = None,
    seed_demo: bool = False,
) -> list[str]:
    """Execute unapplied migrations in version order and track in schema_migrations."""
    _ensure_ledger_table(conn)
    applied_ledger = _load_ledger(conn)

    migrations = sorted(p for p in migrations_dir.glob("[0-9]*.sql") if p.is_file())
    if not migrations:
        return []

    if not applied_ledger:
        _backfill_existing_migrations(conn, migrations, applied_ledger)

    applied_versions: list[str] = []
    for migration in migrations:
        version = migration.name
        current_checksum = compute_checksum(migration)
        if version in applied_ledger or migration.stem in applied_ledger:
            recorded = applied_ledger.get(version) or applied_ledger[migration.stem]
            if recorded != current_checksum:
                raise RuntimeError(
                    f"Checksum mismatch for migration {version}: "
                    f"expected {recorded}, got {current_checksum}"
                )
            continue

        with conn.transaction():
            conn.execute(migration.read_text(encoding="utf-8"))
            conn.execute(
                """
                INSERT INTO schema_migrations (version, checksum, applied_at)
                VALUES (%s, %s, NOW())
                """,
                (version, current_checksum),
            )
        applied_versions.append(version)
        applied_ledger[version] = current_checksum

    if seed_demo and seed_path is not None and seed_path.exists():
        with conn.transaction():
            conn.execute(seed_path.read_text(encoding="utf-8"))

    return applied_versions
