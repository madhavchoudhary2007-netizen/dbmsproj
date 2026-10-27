"""Create, run, and safely remove an isolated acceptance database pair."""

from __future__ import annotations

import json
import os
import re
import secrets
import signal
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit, urlunsplit
from uuid import uuid4


PROJECT = "apexgrid-test"
POSTGRES_ENDPOINT = ("127.0.0.1", 15432)
MONGO_ENDPOINT = ("127.0.0.1", 27018)
PREFIX = "apexgrid_acceptance_"
ROOT = Path(__file__).resolve().parents[2]


def _resource_name(run_id: str) -> str:
    return PREFIX + run_id


def _replace_database(url: str, name: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, "/" + name, parts.query, parts.fragment))


def _safe_error(exc: BaseException, owner_token: str) -> str:
    message = str(exc)
    if owner_token:
        message = message.replace(owner_token, "[redacted]")
    message = re.sub(r"(?i)\b(?:postgres(?:ql)?|mongodb(?:\+srv)?)://[^\s'\"<>]+", "[redacted connection URL]", message)
    return f"{type(exc).__name__}: {message[:240]}"


def _require_connection(name: str, host: str, port: int) -> str:
    value = os.environ.get(name, "")
    parts = urlsplit(value)
    expected_scheme = {"DATABASE_URL": {"postgres", "postgresql"},
                       "MONGODB_URL": {"mongodb"}}.get(name, set())
    if (not value or parts.scheme not in expected_scheme or not parts.hostname
            or parts.query or parts.fragment):
        raise RuntimeError(f"Root must provide explicit {name} connection value")
    try:
        valid_host = parts.hostname.lower() == "localhost" or parts.hostname == host
        valid_port = parts.port == port
        authority = parts.netloc.rsplit("@", 1)[-1]
    except ValueError as exc:
        raise RuntimeError(f"Invalid {name} connection value") from exc
    if not valid_host or not valid_port or "," in authority or "\\" in authority:
        raise RuntimeError(f"{name} must target loopback port {port}")
    return value


class _CliAdapter:
    """Real local-stack adapter. Connection strings are held only in memory."""

    def __init__(self) -> None:
        self.pg_root = _require_connection("DATABASE_URL", *POSTGRES_ENDPOINT)
        self.mongo_root = _require_connection("MONGODB_URL", *MONGO_ENDPOINT)
        self.pg_admin = _replace_database(self.pg_root, "postgres")
        self.mongo_admin = self.mongo_root

    def validate_stack(self, project: str, postgres: tuple[str, int], mongo: tuple[str, int]) -> None:
        if project != PROJECT or postgres != POSTGRES_ENDPOINT or mongo != MONGO_ENDPOINT:
            raise RuntimeError("Unexpected acceptance stack identity")
        result = subprocess.run(
            ["docker", "ps", "-q", "--filter", f"label=com.docker.compose.project={project}"],
            check=True, capture_output=True, text=True,
        )
        ids = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if len(ids) != 2:
            raise RuntimeError("Acceptance stack must contain exactly its two expected services")
        inspect = subprocess.run(
            ["docker", "inspect", "--format",
             "{{index .Config.Labels \"com.docker.compose.project\"}}\t{{index .Config.Labels \"com.docker.compose.service\"}}\t{{json .NetworkSettings.Ports}}",
             *ids],
            check=True, capture_output=True, text=True,
        )
        containers = []
        for line in inspect.stdout.splitlines():
            project_label, separator, remainder = line.partition("\t")
            service_label, separator, ports_raw = remainder.partition("\t")
            if not separator:
                raise RuntimeError("Docker inspect returned incomplete stack metadata")
            containers.append({"project": project_label, "service": service_label, "ports": json.loads(ports_raw)})
        seen: dict[str, tuple[str, int]] = {}
        for container in containers:
            if container.get("project") != project:
                raise RuntimeError("Docker container project label mismatch")
            service = container.get("service")
            bindings = container.get("ports", {}) or {}
            wanted = "5432/tcp" if service == "postgres" else "27017/tcp" if service == "mongo" else None
            port = 15432 if service == "postgres" else 27018 if service == "mongo" else None
            if not wanted or not port:
                raise RuntimeError("Unexpected container in acceptance project")
            rows = bindings.get(wanted) or []
            if len(rows) != 1 or rows[0].get("HostIp") not in {"127.0.0.1", "::1"} or rows[0].get("HostPort") != str(port):
                raise RuntimeError("Acceptance stack port binding mismatch")
            if service in seen:
                raise RuntimeError("Duplicate acceptance service")
            seen[service] = (rows[0]["HostIp"], port)
        if set(seen) != {"postgres", "mongo"}:
            raise RuntimeError("Acceptance stack services are incomplete")

    def generate_run_id(self) -> str:
        return uuid4().hex

    def generate_owner_token(self) -> str:
        return secrets.token_urlsafe(32)

    def _pg(self, url: str):
        import psycopg
        return psycopg.connect(url, autocommit=True)

    def _mongo(self, url: str):
        from pymongo import MongoClient
        return MongoClient(url, serverSelectionTimeoutMS=5000)

    def database_exists(self, engine: str, name: str) -> bool:
        if engine == "postgres":
            with self._pg(self.pg_admin) as conn:
                return conn.execute("SELECT 1 FROM pg_database WHERE datname=%s", (name,)).fetchone() is not None
        client = self._mongo(self.mongo_admin)
        try:
            return name in client.list_database_names()
        finally:
            client.close()

    def create_database(self, engine: str, name: str, run_id: str, owner_token: str) -> None:
        marker = f"apexgrid-acceptance:{run_id}:{owner_token}"
        if engine == "postgres":
            from psycopg import sql
            with self._pg(self.pg_admin) as conn:
                conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
                try:
                    conn.execute(sql.SQL("COMMENT ON DATABASE {} IS {}").format(sql.Identifier(name), sql.Literal(marker)))
                except BaseException as marker_error:
                    try:
                        if self.active_sessions(engine, name) != 0:
                            raise RuntimeError("New PostgreSQL database has active sessions")
                        conn.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(name)))
                    except BaseException as cleanup_error:
                        raise RuntimeError("Ownership marker failed; newly created PostgreSQL database could not be safely removed") from cleanup_error
                    raise RuntimeError("Could not stamp ownership marker; newly created PostgreSQL database was removed") from marker_error
        else:
            client = self._mongo(self.mongo_root)
            try:
                try:
                    client[name]["acceptance_metadata"].insert_one(
                        {"_id": "run_owner", "run_id": run_id, "owner_token": owner_token}
                    )
                except BaseException as marker_error:
                    client.close()
                    try:
                        if not self.ownership_matches(engine, name, run_id, owner_token):
                            raise RuntimeError("MongoDB owner marker could not be verified")
                        if self.active_sessions(engine, name) != 0:
                            raise RuntimeError("New MongoDB database has active operations")
                        cleanup = self._mongo(self.mongo_admin)
                        try:
                            cleanup.drop_database(name)
                        finally:
                            cleanup.close()
                    except BaseException as cleanup_error:
                        raise RuntimeError("Ownership marker failed; newly created MongoDB database could not be safely removed") from cleanup_error
                    raise RuntimeError("Could not confirm MongoDB ownership marker; newly created database was removed") from marker_error
            finally:
                try:
                    client.close()
                except Exception:
                    pass

    def seed_database(self, engine: str, name: str, run_id: str, owner_token: str) -> None:
        if engine != "postgres":
            return
        env = os.environ.copy()
        env.update({"DATABASE_URL": _replace_database(self.pg_root, name),
                    "MONGODB_URL": _replace_database(self.mongo_root, name),
                    "MONGODB_DATABASE": name, "APP_ENV": "local", "SEED_DEMO_DATA": "1",
                    "PYTHONPATH": str(ROOT / "backend")})
        subprocess.run([sys.executable, "-m", "app.bootstrap"], cwd=ROOT / "backend", env=env, check=True)

    def run_acceptance(self, env: dict[str, str]):
        return subprocess.Popen(
            [sys.executable, str(ROOT / "scripts" / "acceptance.py")], cwd=ROOT, env=env,
            start_new_session=True,
        )

    def stop_child(self, child) -> None:
        if child.poll() is not None:
            child.wait(timeout=5)
            return
        try:
            os.killpg(child.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            child.wait(timeout=5)
            return
        except subprocess.TimeoutExpired:
            pass
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("Owned acceptance process group did not stop after bounded termination") from exc

    def active_sessions(self, engine: str, name: str) -> int:
        if engine == "postgres":
            with self._pg(self.pg_admin) as conn:
                return int(conn.execute("SELECT count(*) FROM pg_stat_activity WHERE datname=%s", (name,)).fetchone()[0])
        client = self._mongo(self.mongo_admin)
        try:
            operations = client.admin.command("currentOp", {"$all": True}).get("inprog", [])
            namespace_prefix = name + "."
            return sum(1 for operation in operations if str(operation.get("ns", "")).startswith(namespace_prefix))
        finally:
            client.close()

    def ownership_matches(self, engine: str, name: str, run_id: str, owner_token: str) -> bool:
        if engine == "postgres":
            with self._pg(self.pg_admin) as conn:
                row = conn.execute("SELECT shobj_description(oid, 'pg_database') FROM pg_database WHERE datname=%s", (name,)).fetchone()
            return bool(row and row[0] == f"apexgrid-acceptance:{run_id}:{owner_token}")
        client = self._mongo(self.mongo_root)
        try:
            row = client[name]["acceptance_metadata"].find_one({"_id": "run_owner"})
            return bool(row and row.get("run_id") == run_id and row.get("owner_token") == owner_token)
        finally:
            client.close()

    def drop_database(self, engine: str, name: str, run_id: str, owner_token: str) -> None:
        if not self.ownership_matches(engine, name, run_id, owner_token):
            raise RuntimeError(f"Refusing to drop {engine} database with mismatched ownership")
        if self.active_sessions(engine, name) != 0:
            raise RuntimeError(f"Refusing to drop {engine} database with active sessions")
        if engine == "postgres":
            from psycopg import sql
            with self._pg(self.pg_admin) as conn:
                conn.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(name)))
        else:
            client = self._mongo(self.mongo_admin)
            try:
                client.drop_database(name)
            finally:
                client.close()


def run_owned_acceptance(adapter=None):
    adapter = adapter if adapter is not None else _CliAdapter()
    adapter.validate_stack(PROJECT, POSTGRES_ENDPOINT, MONGO_ENDPOINT)
    raw_id = adapter.generate_run_id()
    run_id = str(raw_id).replace("-", "").lower()
    if not run_id or len(run_id) > 32 or any(char not in "0123456789abcdef" for char in run_id):
        raise RuntimeError("Adapter returned an invalid run id")
    owner_token = adapter.generate_owner_token()
    if not owner_token or str(owner_token) == run_id:
        raise RuntimeError("Adapter returned an invalid ownership token")
    name = _resource_name(run_id)
    engines = ("postgres", "mongo")
    created: list[tuple[str, str]] = []
    child = None
    child_reaped = True
    failure: BaseException | None = None
    cleanup_failures: list[str] = []
    try:
        for engine in engines:
            if adapter.database_exists(engine, name):
                raise RuntimeError(f"Refusing to reuse existing {engine} acceptance database")
        for engine in engines:
            adapter.create_database(engine, name, run_id, owner_token)
            created.append((engine, name))
        for engine in engines:
            adapter.seed_database(engine, name, run_id, owner_token)
        env = os.environ.copy()
        if isinstance(adapter, _CliAdapter):
            env["DATABASE_URL"] = _replace_database(adapter.pg_root, name)
            env["MONGODB_URL"] = _replace_database(adapter.mongo_root, name)
        else:
            env["DATABASE_URL"] = f"postgresql://127.0.0.1:15432/{name}"
            env["MONGODB_URL"] = f"mongodb://127.0.0.1:27018/{name}"
        env.update({"MONGODB_DATABASE": name, "ACCEPTANCE_RUN_ID": run_id,
                    "ACCEPTANCE_OWNERSHIP_TOKEN": owner_token})
        child = adapter.run_acceptance(env)
        child_reaped = False
        while True:
            try:
                exit_code = child.wait(timeout=30)
                break
            except subprocess.TimeoutExpired:
                continue
        child_reaped = True
        if exit_code != 0:
            raise RuntimeError(f"Acceptance child exited with status {exit_code}")
    except BaseException as exc:
        failure = exc
    finally:
        if child is not None and not child_reaped:
            try:
                stop_child = getattr(adapter, "stop_child", None)
                if stop_child is not None:
                    stop_child(child)
                else:
                    terminate = getattr(child, "terminate", None)
                    if terminate is None:
                        raise RuntimeError("Cannot safely terminate acceptance child after interruption")
                    terminate()
                    child.wait(timeout=5)
                child_reaped = True
            except BaseException as exc:
                cleanup_failures.append(f"Could not stop acceptance child: {_safe_error(exc, owner_token)}")
        safe_to_drop = child_reaped
        if not safe_to_drop:
            cleanup_failures.extend(
                f"Refused cleanup of {engine}/{database}: child shutdown was not confirmed"
                for engine, database in created
            )
        else:
            for engine, database in created:
                try:
                    ownership_matches = adapter.ownership_matches(engine, database, run_id, owner_token)
                    if not ownership_matches:
                        cleanup_failures.append(f"Refused cleanup of {engine}/{database}: ownership marker mismatch")
                except BaseException as exc:
                    cleanup_failures.append(
                        f"Could not verify ownership for {engine}/{database}: {_safe_error(exc, owner_token)}"
                    )
                try:
                    if adapter.active_sessions(engine, database) != 0:
                        cleanup_failures.append(f"Refused cleanup of {engine}/{database}: active sessions remain")
                except BaseException as exc:
                    cleanup_failures.append(
                        f"Could not verify sessions for {engine}/{database}: {_safe_error(exc, owner_token)}"
                    )
        safe_to_drop = safe_to_drop and not cleanup_failures
        for engine, database in reversed(created) if safe_to_drop else ():
            try:
                adapter.drop_database(engine, database, run_id, owner_token)
            except BaseException as exc:
                cleanup_failures.append(
                    f"Could not remove {engine}/{database}: {_safe_error(exc, owner_token)}"
                )
    if failure is not None or cleanup_failures:
        if isinstance(failure, KeyboardInterrupt) and not cleanup_failures:
            raise failure
        report = []
        if failure is not None:
            report.append(f"Acceptance lifecycle failed: {_safe_error(failure, owner_token)}")
        report.extend(cleanup_failures)
        raise RuntimeError("; ".join(report)) from failure
    return {"run_id": run_id, "database": name}


if __name__ == "__main__":
    run_owned_acceptance()
