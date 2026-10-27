"""Offline regression tests for root-owned disposable acceptance databases."""

from __future__ import annotations

import importlib.util
import math
from pathlib import Path
from typing import Any
from urllib.parse import quote

import pytest


_LIFECYCLE_PATH = Path(__file__).resolve().parent / "run_owned_acceptance.py"
_ACCEPTANCE_PATH = Path(__file__).resolve().parents[1] / "acceptance.py"


def _lifecycle() -> Any:
    spec = importlib.util.spec_from_file_location("owned_acceptance_under_test", _LIFECYCLE_PATH)
    assert spec is not None and spec.loader is not None, "owned acceptance lifecycle module is missing"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _acceptance() -> Any:
    spec = importlib.util.spec_from_file_location("acceptance_url_guards_under_test", _ACCEPTANCE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _Child:
    def __init__(self, calls: list[tuple[Any, ...]], exit_code: int = 0, interrupt_wait: bool = False) -> None:
        self.calls = calls
        self.exit_code = exit_code
        self.interrupt_wait = interrupt_wait
        self.terminated = False

    def wait(self, timeout: float | None = None) -> int:
        self.calls.append(("child_wait", timeout))
        if self.interrupt_wait and not self.terminated:
            raise KeyboardInterrupt()
        return self.exit_code

    def terminate(self) -> None:
        self.calls.append(("child_terminate",))
        self.terminated = True


class _Adapter:
    """Fake all external effects so these tests cannot reach a real stack."""

    def __init__(self, *, existing: set[tuple[str, str]] | None = None) -> None:
        self.calls: list[tuple[Any, ...]] = []
        self.existing = existing or set()
        self.created: set[tuple[str, str]] = set()
        self.created_history: list[tuple[str, str]] = []
        self.fail_at: str | None = None
        self.exit_code = 0
        self.sessions = 0
        self.mismatched_ownership = False
        self.sessions_by_engine: dict[str, int] = {}
        self.mismatched_by_engine: set[str] = set()
        self.interrupt_child_wait = False
        self.child: _Child | None = None

    def validate_stack(self, project: str, postgres: tuple[str, int], mongo: tuple[str, int]) -> None:
        self.calls.append(("validate", project, postgres, mongo))
        if self.fail_at == "validate":
            raise RuntimeError("unsafe stack")

    def generate_run_id(self) -> str:
        self.calls.append(("generate_id",))
        return "f3b02c0e5d934ff494f176513dd0"

    def generate_owner_token(self) -> str:
        self.calls.append(("generate_owner_token",))
        return "owner-token-c9b1f4e7"

    def database_exists(self, engine: str, name: str) -> bool:
        self.calls.append(("exists", engine, name))
        return (engine, name) in self.existing

    def create_database(self, engine: str, name: str, run_id: str, owner_token: str) -> None:
        self.calls.append(("create", engine, name, run_id, owner_token))
        if self.fail_at == f"create_{engine}":
            raise RuntimeError("create failed")
        self.created.add((engine, name))
        self.created_history.append((engine, name))

    def seed_database(self, engine: str, name: str, run_id: str, owner_token: str) -> None:
        self.calls.append(("seed", engine, name, run_id, owner_token))
        if self.fail_at == f"seed_{engine}":
            raise RuntimeError("seed failed")

    def run_acceptance(self, env: dict[str, str]) -> _Child:
        self.calls.append(("run_acceptance", dict(env)))
        if self.fail_at == "run":
            raise RuntimeError("launch failed")
        self.child = _Child(self.calls, self.exit_code, self.interrupt_child_wait)
        return self.child

    def active_sessions(self, engine: str, name: str) -> int:
        self.calls.append(("sessions", engine, name))
        return self.sessions_by_engine.get(engine, self.sessions)

    def ownership_matches(self, engine: str, name: str, run_id: str, owner_token: str) -> bool:
        self.calls.append(("ownership", engine, name, run_id, owner_token))
        return not self.mismatched_ownership and engine not in self.mismatched_by_engine

    def drop_database(self, engine: str, name: str, run_id: str, owner_token: str) -> None:
        self.calls.append(("drop", engine, name, run_id, owner_token))
        self.created.remove((engine, name))


def _run(adapter: _Adapter) -> Any:
    return _lifecycle().run_owned_acceptance(adapter=adapter)


def _db_name(engine: str, calls: list[tuple[Any, ...]]) -> str:
    return next(call[2] for call in calls if call[0] == "create" and call[1] == engine)


def test_validates_stack_before_database_actions_and_uses_one_run_owned_name() -> None:
    adapter = _Adapter()

    _run(adapter)

    actions = [call[0] for call in adapter.calls]
    assert actions.index("validate") < actions.index("exists") < actions.index("create")
    validation = adapter.calls[0]
    assert validation == ("validate", "apexgrid-test", ("127.0.0.1", 15432), ("127.0.0.1", 27018))
    pg_name = _db_name("postgres", adapter.calls)
    mongo_name = _db_name("mongo", adapter.calls)
    assert pg_name == mongo_name
    assert pg_name.startswith("apexgrid_acceptance_")
    assert pg_name.removeprefix("apexgrid_acceptance_") == "f3b02c0e5d934ff494f176513dd0"
    assert all(call[2] == pg_name for call in adapter.calls if call[0] in {"create", "seed", "drop"})


def test_refuses_existing_matching_database_without_reuse_or_cleanup() -> None:
    name = "apexgrid_acceptance_f3b02c0e5d934ff494f176513dd0"
    adapter = _Adapter(existing={("mongo", name)})

    with pytest.raises((RuntimeError, ValueError)):
        _run(adapter)

    assert not any(call[0] in {"create", "seed", "run_acceptance", "drop"} for call in adapter.calls)


@pytest.mark.parametrize("failure", ["create_mongo", "seed_postgres", "seed_mongo", "run"])
def test_partial_setup_and_test_failures_drop_only_created_databases(failure: str) -> None:
    adapter = _Adapter()
    adapter.fail_at = failure

    with pytest.raises(RuntimeError):
        _run(adapter)

    drops = [call for call in adapter.calls if call[0] == "drop"]
    assert {(call[1], call[2]) for call in drops} == set(adapter.created_history)
    assert all((call[1], call[2]) in {( "postgres", _db_name("postgres", adapter.calls)), ("mongo", _db_name("mongo", adapter.calls))} for call in drops)


def test_child_gets_isolated_database_environment_and_exits_before_cleanup() -> None:
    adapter = _Adapter()

    _run(adapter)

    run_call = next(call for call in adapter.calls if call[0] == "run_acceptance")
    env = run_call[1]
    name = _db_name("postgres", adapter.calls)
    run_id = "f3b02c0e5d934ff494f176513dd0"
    owner_token = "owner-token-c9b1f4e7"
    assert env["DATABASE_URL"].endswith("/" + name)
    assert env["MONGODB_URL"].endswith("/" + name)
    assert env["MONGODB_DATABASE"] == name
    assert env["ACCEPTANCE_RUN_ID"] == run_id
    assert env["ACCEPTANCE_OWNERSHIP_TOKEN"] == owner_token
    assert env["ACCEPTANCE_OWNERSHIP_TOKEN"] != env["ACCEPTANCE_RUN_ID"]
    marker_calls = [call for call in adapter.calls if call[0] in {"create", "seed", "ownership", "drop"}]
    assert marker_calls
    assert all(call[3] == run_id and call[4] == owner_token for call in marker_calls)
    assert next(i for i, call in enumerate(adapter.calls) if call[0] == "child_wait") < next(
        i for i, call in enumerate(adapter.calls) if call[0] == "drop"
    )


def test_nonzero_child_exit_still_cleans_up_after_wait() -> None:
    adapter = _Adapter()
    adapter.exit_code = 3

    with pytest.raises((RuntimeError, SystemExit)):
        _run(adapter)

    assert any(call[0] == "child_wait" for call in adapter.calls)
    assert any(call[0] == "drop" for call in adapter.calls)


def test_active_session_or_mismatched_ownership_refuses_drop() -> None:
    adapter = _Adapter()
    adapter.sessions = 1

    with pytest.raises((RuntimeError, ValueError)):
        _run(adapter)

    assert not any(call[0] == "drop" for call in adapter.calls)


def test_mismatched_ownership_refuses_drop() -> None:
    adapter = _Adapter()
    adapter.mismatched_ownership = True

    with pytest.raises((RuntimeError, ValueError)):
        _run(adapter)

    assert adapter.created_history
    assert not any(call[0] == "drop" for call in adapter.calls)


def test_interruption_runs_cleanup_after_child_exit() -> None:
    adapter = _Adapter()
    adapter.interrupt_child_wait = True
    with pytest.raises(KeyboardInterrupt):
        _run(adapter)

    waits = [(i, call[1]) for i, call in enumerate(adapter.calls) if call[0] == "child_wait"]
    terminate_index = next(i for i, call in enumerate(adapter.calls) if call[0] == "child_terminate")
    first_drop = next(i for i, call in enumerate(adapter.calls) if call[0] == "drop")
    assert len(waits) >= 2
    assert all(timeout is not None and math.isfinite(timeout) and 0 < timeout <= 30 for _, timeout in waits)
    assert waits[0][0] < terminate_index < waits[1][0] < first_drop
    assert {(call[1], call[2]) for call in adapter.calls if call[0] == "drop"} == set(adapter.created_history)


@pytest.mark.parametrize("engine", ["postgres", "mongo"])
@pytest.mark.parametrize("hazard", ["active_session", "mismatched_marker"])
def test_cleanup_preflights_both_databases_before_dropping_either(engine: str, hazard: str) -> None:
    adapter = _Adapter()
    if hazard == "active_session":
        adapter.sessions_by_engine[engine] = 1
    else:
        adapter.mismatched_by_engine.add(engine)

    with pytest.raises((RuntimeError, ValueError)):
        _run(adapter)

    drop_indices = [i for i, call in enumerate(adapter.calls) if call[0] == "drop"]
    safety_indices = [i for i, call in enumerate(adapter.calls) if call[0] in {"sessions", "ownership"}]
    assert not drop_indices
    assert len([call for call in adapter.calls if call[0] == "sessions"]) == 2
    assert len([call for call in adapter.calls if call[0] == "ownership"]) == 2
    assert safety_indices and min(safety_indices) < min(drop_indices, default=len(adapter.calls))


@pytest.mark.parametrize(
    ("engine", "url"),
    [
        ("postgres", "postgresql://unit:unit@127.0.0.1:15432/apexgrid_acceptance_run?host=evil.invalid"),
        ("postgres", "postgresql://unit:unit@127.0.0.1:15432/apexgrid_acceptance_run#host=evil.invalid"),
        ("postgres", "postgresql://unit:unit@127.0.0.1,evil.invalid:15432/apexgrid_acceptance_run"),
        ("mongo", "mongodb://127.0.0.1:27018,evil.invalid:27018/apexgrid_acceptance_run"),
        ("mongo", "mongodb://127.0.0.1:27018/apexgrid_acceptance_run?host=evil.invalid"),
        ("mongo", "mongodb://127.0.0.1:27018/apexgrid_acceptance_run#host=evil.invalid"),
    ],
)
def test_database_url_guards_reject_query_fragment_and_extra_host_overrides(engine: str, url: str) -> None:
    acceptance = _acceptance()
    name = "apexgrid_acceptance_run"

    with pytest.raises((RuntimeError, ValueError)):
        if engine == "postgres":
            acceptance.ensure_disposable_target(url, name)
        else:
            acceptance.ensure_mongo_target(url, name)


@pytest.mark.parametrize("hazard", ["active_session", "mismatched_marker"])
def test_original_failure_reports_cleanup_refusal_and_retained_resources(hazard: str) -> None:
    adapter = _Adapter()
    adapter.fail_at = "run"
    if hazard == "active_session":
        adapter.sessions_by_engine["postgres"] = 1
    else:
        adapter.mismatched_by_engine.add("postgres")

    with pytest.raises(RuntimeError) as error:
        _run(adapter)

    message = str(error.value).lower()
    assert "launch failed" in message
    assert "cleanup" in message
    assert "retained" in message or "refus" in message
    assert "apexgrid_acceptance_f3b02c0e5d934ff494f176513dd0" in message
