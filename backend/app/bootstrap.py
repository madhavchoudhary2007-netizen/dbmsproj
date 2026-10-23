"""Apply relational schema and seed once before the API starts."""

from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from pymongo import MongoClient

from .config import APP_ENV, DATABASE_URL, MONGODB_DATABASE, MONGODB_URL, SEED_DEMO_DATA
from .race_archive import seed_historical_laps


def main():
    root = Path(__file__).resolve().parents[1]
    migrations_dir = root / "migrations"
    if not migrations_dir.is_dir():
        raise SystemExit(f"Required migrations directory missing: {migrations_dir}")
    migrations = sorted(migrations_dir.glob("[0-9]*.sql"))
    if not migrations:
        raise SystemExit(f"No numbered SQL migrations found in: {migrations_dir}")
    seed = root / "db" / "seed.sql"
    with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
        for migration in migrations:
            conn.execute(migration.read_text())
        if SEED_DEMO_DATA and seed.exists():
            conn.execute(seed.read_text())
    if SEED_DEMO_DATA and APP_ENV == "local":
        with (
            psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn,
            MongoClient(MONGODB_URL, serverSelectionTimeoutMS=5000) as mongo,
        ):
            seed_historical_laps(conn, mongo[MONGODB_DATABASE]["telemetry"])
    seed_status = " and seed complete" if SEED_DEMO_DATA else "; demo seeding skipped"
    print("Database migration complete" + seed_status)


if __name__ == "__main__":
    main()
