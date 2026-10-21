"""Apply relational schema and seed once before the API starts."""
from pathlib import Path
import psycopg
from .config import DATABASE_URL, APP_ENV, MONGODB_URL, MONGODB_DATABASE, SEED_DEMO_DATA
from psycopg.rows import dict_row
from pymongo import MongoClient
from .race_archive import seed_historical_laps


def main():
    root = Path(__file__).resolve().parents[1]
    migration = root / "migrations" / "001_initial.sql"
    seed = root / "db" / "seed.sql"
    if not migration.exists():
        raise SystemExit(f"Required migration missing: {migration}")
    with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
        conn.execute(migration.read_text())
        if SEED_DEMO_DATA and seed.exists():
            conn.execute(seed.read_text())
    if SEED_DEMO_DATA and APP_ENV == "local":
        with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn, MongoClient(MONGODB_URL, serverSelectionTimeoutMS=5000) as mongo:
            seed_historical_laps(conn, mongo[MONGODB_DATABASE]["telemetry"])
    print("Database migration complete" + (" and seed complete" if SEED_DEMO_DATA else "; demo seeding skipped"))


if __name__ == "__main__":
    main()
