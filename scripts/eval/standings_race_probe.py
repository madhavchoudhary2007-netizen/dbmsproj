"""Deterministic concurrency probe for standings recalculation on owned data only."""

from __future__ import annotations

import importlib
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

import psycopg
from psycopg import sql

ROOT = Path(__file__).resolve().parents[2]
PREFIX = "apexgrid_acceptance_"
RUN_ID_PATTERN = re.compile(r"[0-9a-f]{32}\Z")
OWNERSHIP_ENV_KEYS = (
    "DATABASE_URL",
    "MONGODB_URL",
    "MONGODB_DATABASE",
    "ACCEPTANCE_RUN_ID",
    "ACCEPTANCE_OWNERSHIP_TOKEN",
)

sys.path.insert(0, str(ROOT))
acceptance = importlib.import_module("scripts.acceptance")
owned_acceptance = importlib.import_module("scripts.eval.run_owned_acceptance")


class ProbeFailure(RuntimeError):
    """A safe, non-secret-bearing probe failure message."""


@dataclass(frozen=True)
class OwnedContext:
    database_url: str = field(repr=False)
    database_name: str
    run_id: str
    ownership_token: str = field(repr=False)


def validate_owned_environment(env: dict[str, str]) -> OwnedContext:
    database_url = env.get("DATABASE_URL", "")
    mongo_url = env.get("MONGODB_URL", "")
    database_name = env.get("MONGODB_DATABASE", "")
    run_id = env.get("ACCEPTANCE_RUN_ID", "")
    owner_token = env.get("ACCEPTANCE_OWNERSHIP_TOKEN", "")
    if not all((database_url, mongo_url, database_name, run_id, owner_token)):
        raise ProbeFailure("Probe requires owned database URLs, name, run id, and ownership token")
    if not RUN_ID_PATTERN.fullmatch(run_id) or database_name != f"{PREFIX}{run_id}":
        raise ProbeFailure("Probe database name does not match the valid owned run id")
    if owner_token == run_id:
        raise ProbeFailure("Probe ownership token must be distinct from the run id")
    try:
        guarded_name = acceptance.ensure_disposable_target(database_url, database_name)
        acceptance.ensure_mongo_target(mongo_url, guarded_name)
    except Exception as exc:
        raise ProbeFailure(f"Disposable target validation failed ({type(exc).__name__})") from None
    if guarded_name != database_name:
        raise ProbeFailure("Probe database name failed its disposable target guard")
    try:
        acceptance.verify_run_ownership(
            database_url, mongo_url, database_name, run_id, owner_token
        )
    except Exception as exc:
        raise ProbeFailure(
            f"Owned database marker verification failed ({type(exc).__name__})"
        ) from None
    return OwnedContext(database_url, database_name, run_id, owner_token)


class RecalculationAdapter(Protocol):
    def find_seeded_championship(self) -> str: ...

    def snapshot(self, championship_id: str) -> list[tuple[Any, ...]]: ...

    def clear_standings(self, championship_id: str) -> None: ...

    def prepare_gate(self, championship_id: str) -> None: ...

    def hold_gate(self) -> None: ...

    def wait_for_concurrent_overlap(self, timeout: float) -> bool: ...

    def release_gate(self) -> None: ...

    def recalculate(self, championship_id: str) -> str: ...

    def remove_gate(self) -> None: ...


def run_recalculation_probe(adapter: RecalculationAdapter) -> dict[str, Any]:
    championship_id = adapter.find_seeded_championship()
    if not championship_id:
        raise ProbeFailure("Owned seed has no completed multi-driver championship results")
    adapter.recalculate(championship_id)
    baseline = adapter.snapshot(championship_id)
    if len(baseline) < 2:
        raise ProbeFailure("Owned seed championship must have standings for at least two drivers")
    outcomes: list[str] = []
    gate_prepared = False
    try:
        adapter.clear_standings(championship_id)
        gate_prepared = True
        adapter.prepare_gate(championship_id)
        outcomes = _run_overlapped_recalculations(adapter, championship_id)
    except ProbeFailure:
        raise
    except Exception as exc:
        sqlstate = getattr(exc, "sqlstate", None)
        suffix = f"SQLSTATE {sqlstate}" if sqlstate else type(exc).__name__
        raise ProbeFailure(f"A concurrent recalculation failed ({suffix})") from None
    finally:
        adapter.release_gate()
        if gate_prepared:
            adapter.remove_gate()
    final = adapter.snapshot(championship_id)
    if len(outcomes) != 2 or any(outcome != "ok" for outcome in outcomes):
        raise ProbeFailure("Both concurrent recalculations must succeed")
    if final != baseline:
        raise ProbeFailure("Concurrent standings differ from the serial baseline")
    ranks = [row[0] for row in final]
    if ranks != list(range(1, len(final) + 1)):
        raise ProbeFailure("Final standings ranks are not unique and contiguous")
    return {"championship_id": championship_id, "rows": len(final), "concurrent_requests": 2}


def _run_overlapped_recalculations(
    adapter: RecalculationAdapter, championship_id: str
) -> list[str]:
    adapter.hold_gate()
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(adapter.recalculate, championship_id) for _ in range(2)]
        try:
            overlap_reached = adapter.wait_for_concurrent_overlap(15.0)
        finally:
            adapter.release_gate()
        if not overlap_reached:
            raise ProbeFailure(
                "Concurrent recalculation lock overlap was not observed"
            )
        return [future.result() for future in futures]


class PostgresAdapter:
    def __init__(self, context: OwnedContext) -> None:
        self._database_url = context.database_url
        self._application_name = f"standings-probe-{context.run_id}"
        self._connection: Any = None
        self._lock_keys = (
            int(context.run_id[:8], 16) % 2**31,
            int(context.run_id[8:16], 16) % 2**31,
        )
        self._function_name = f"standings_gate_{context.run_id}"
        self._trigger_name = f"standings_gate_{context.run_id}"

    def find_seeded_championship(self) -> str:
        query = """SELECT c.id::text FROM championships c
            JOIN race_events e ON e.championship_id=c.id
            JOIN race_sessions s ON s.event_id=e.id
            JOIN session_results r ON r.session_id=s.id
            WHERE s.session_type='RACE' AND s.state='COMPLETED'
            GROUP BY c.id HAVING count(DISTINCT r.driver_id)>=2
            ORDER BY c.id LIMIT 1"""
        with psycopg.connect(self._database_url) as conn, conn.cursor() as cur:
            cur.execute(query)
            row = cur.fetchone()
        if not row:
            return ""
        return str(row[0])

    def recalculate(self, championship_id: str) -> str:
        with psycopg.connect(
            self._database_url, application_name=self._application_name
        ) as conn, conn.cursor() as cur:
            cur.execute("SELECT recalculate_standings(%s)", (championship_id,))
        return "ok"

    def snapshot(self, championship_id: str) -> list[tuple[Any, ...]]:
        with psycopg.connect(self._database_url) as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT rank,driver_id::text,points,wins,podiums FROM driver_standings "
                "WHERE championship_id=%s ORDER BY rank",
                (championship_id,),
            )
            return [tuple(row) for row in cur.fetchall()]

    def clear_standings(self, championship_id: str) -> None:
        with psycopg.connect(self._database_url) as conn, conn.cursor() as cur:
            cur.execute(
                "DELETE FROM driver_standings WHERE championship_id=%s",
                (championship_id,),
            )

    def prepare_gate(self, championship_id: str) -> None:
        key_one, key_two = self._lock_keys
        body = (
            "BEGIN IF NEW.championship_id = "
            f"{sql.Literal(championship_id).as_string()}::uuid THEN "
            f"PERFORM pg_advisory_xact_lock({key_one}, {key_two}); "
            "END IF; RETURN NEW; END"
        )
        with psycopg.connect(self._database_url, autocommit=True) as conn:
            conn.execute(
                sql.SQL("CREATE FUNCTION {}() RETURNS trigger LANGUAGE plpgsql AS {}")
                .format(sql.Identifier(self._function_name), sql.Literal(body))
            )
            conn.execute(
                sql.SQL(
                    "CREATE TRIGGER {} BEFORE INSERT ON driver_standings "
                    "FOR EACH ROW EXECUTE FUNCTION {}()"
                )
                .format(sql.Identifier(self._trigger_name), sql.Identifier(self._function_name))
            )

    def hold_gate(self) -> None:
        self._connection = psycopg.connect(self._database_url, autocommit=True)
        self._connection.execute("SELECT pg_advisory_lock(%s, %s)", self._lock_keys)

    def wait_for_concurrent_overlap(self, timeout: float) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with psycopg.connect(self._database_url) as conn, conn.cursor() as cur:
                cur.execute(
                    "SELECT count(*) FILTER (WHERE wait_event_type='Lock'), "
                    "count(*) FILTER (WHERE wait_event_type='Lock' AND wait_event='advisory') "
                    "FROM pg_stat_activity WHERE datname=current_database() "
                    "AND application_name=%s AND state='active'",
                    (self._application_name,),
                )
                row = cur.fetchone()
            if row and row[0] >= 2 and row[1] >= 1:
                return True
            time.sleep(0.025)
        return False

    def release_gate(self) -> None:
        if self._connection is not None:
            try:
                self._connection.execute("SELECT pg_advisory_unlock(%s, %s)", self._lock_keys)
            finally:
                self._connection.close()
                self._connection = None

    def remove_gate(self) -> None:
        with psycopg.connect(self._database_url, autocommit=True) as conn:
            conn.execute(
                sql.SQL("DROP TRIGGER IF EXISTS {} ON driver_standings").format(
                    sql.Identifier(self._trigger_name)
                )
            )
            conn.execute(
                sql.SQL("DROP FUNCTION IF EXISTS {}()").format(
                    sql.Identifier(self._function_name)
                )
            )


def run_owned_probe(env: dict[str, str], adapter_factory: Any = PostgresAdapter) -> dict[str, Any]:
    context = validate_owned_environment(env)
    return run_recalculation_probe(adapter_factory(context))


class _ProbeOwnedAdapter(owned_acceptance._CliAdapter):
    """Delegate resource lifecycle to the existing owned-acceptance manager."""

    def run_acceptance(self, env: dict[str, str]) -> Any:
        return subprocess.Popen(  # noqa: S603 -- executable and script path are fixed by this probe
            [sys.executable, str(Path(__file__).resolve()), "--probe-child"],
            cwd=ROOT,
            env=env,
            start_new_session=True,
        )


def main() -> int:
    if sys.argv[1:] == ["--probe-child"]:
        try:
            result = run_owned_probe(
                {key: os.environ.get(key, "") for key in OWNERSHIP_ENV_KEYS}
            )
        except ProbeFailure as exc:
            print(f"FAIL: {exc}")
            return 1
        except Exception as exc:
            print(f"FAIL: standings probe error ({type(exc).__name__})")
            return 1
        print(f"PASS: concurrent standings recalculation ({result['rows']} seeded rows)")
        return 0
    try:
        owned_acceptance.run_owned_acceptance(_ProbeOwnedAdapter())
    except Exception as exc:
        print(f"FAIL: owned standings probe lifecycle ({type(exc).__name__})")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
