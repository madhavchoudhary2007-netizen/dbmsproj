from __future__ import annotations

# ruff: noqa: S101
import importlib.util
import sys
import threading
from pathlib import Path
from typing import Any

import pytest

_PROBE_PATH = Path(__file__).with_name("standings_race_probe.py")
_PROBE_SPEC = importlib.util.spec_from_file_location("standings_race_probe_under_test", _PROBE_PATH)
assert _PROBE_SPEC is not None and _PROBE_SPEC.loader is not None
probe = importlib.util.module_from_spec(_PROBE_SPEC)
sys.modules[_PROBE_SPEC.name] = probe
_PROBE_SPEC.loader.exec_module(probe)

RUN_ID = "0123456789abcdef0123456789abcdef"
OWNER = "owned-test-token-value"
DATABASE = f"apexgrid_acceptance_{RUN_ID}"


def _environment(**overrides: str) -> dict[str, str]:
    values = {
        "DATABASE_URL": f"postgresql://unit:unit@127.0.0.1:15432/{DATABASE}",
        "MONGODB_URL": f"mongodb://unit:unit@127.0.0.1:27018/{DATABASE}",
        "MONGODB_DATABASE": DATABASE,
        "ACCEPTANCE_RUN_ID": RUN_ID,
        "ACCEPTANCE_OWNERSHIP_TOKEN": OWNER,
    }
    values.update(overrides)
    return values


@pytest.fixture
def verified_marker(monkeypatch: pytest.MonkeyPatch) -> list[tuple[Any, ...]]:
    calls: list[tuple[Any, ...]] = []
    monkeypatch.setattr(
        probe.acceptance,
        "verify_run_ownership",
        lambda *args: calls.append(args),
    )
    return calls


def test_owned_guard_checks_matching_run_name_endpoints_and_marker(
    verified_marker: list[tuple[Any, ...]],
) -> None:
    context = probe.validate_owned_environment(_environment())

    assert context.database_name == DATABASE
    assert context.run_id == RUN_ID
    assert context.ownership_token == OWNER
    assert len(verified_marker) == 1
    assert verified_marker[0][2:] == (DATABASE, RUN_ID, OWNER)


@pytest.mark.parametrize(
    "overrides",
    [
        {"DATABASE_URL": ""},
        {"MONGODB_URL": ""},
        {"MONGODB_DATABASE": ""},
        {"ACCEPTANCE_RUN_ID": ""},
        {"ACCEPTANCE_OWNERSHIP_TOKEN": ""},
        {"ACCEPTANCE_RUN_ID": "wrong-run-id"},
        {"ACCEPTANCE_OWNERSHIP_TOKEN": RUN_ID},
        {"MONGODB_DATABASE": "apexgrid_acceptance_other"},
        {
            "DATABASE_URL": f"postgresql://unit:unit@db.invalid:15432/{DATABASE}",
        },
        {
            "DATABASE_URL": f"postgresql://unit:unit@127.0.0.1:5432/{DATABASE}",
        },
        {
            "MONGODB_URL": f"mongodb://unit:unit@mongo.invalid:27018/{DATABASE}",
        },
        {
            "MONGODB_URL": f"mongodb://unit:unit@127.0.0.1:27017/{DATABASE}",
        },
    ],
)
def test_owned_guard_fails_closed_before_marker_lookup_for_bad_context(
    verified_marker: list[tuple[Any, ...]], overrides: dict[str, str]
) -> None:
    with pytest.raises(probe.ProbeFailure):
        probe.validate_owned_environment(_environment(**overrides))

    assert verified_marker == []


def test_missing_or_mismatched_ownership_marker_fails_before_adapter_use(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        probe.acceptance,
        "verify_run_ownership",
        lambda *_args: (_ for _ in ()).throw(RuntimeError("marker mismatch")),
    )
    factories: list[object] = []

    with pytest.raises(probe.ProbeFailure, match="marker verification failed"):
        probe.run_owned_probe(_environment(), lambda _context: factories.append(object()))

    assert factories == []


class _FakeAdapter:
    def __init__(
        self,
        *,
        failing: bool = False,
        advisory_waiters: int = 2,
        championship_lock_waiters: int = 0,
    ) -> None:
        self.failing = failing
        self.advisory_waiters = advisory_waiters
        self.championship_lock_waiters = championship_lock_waiters
        self.calls: list[str] = []
        self.concurrent = threading.Barrier(2)
        self.recalculations = 0
        self.rows = [(1, "driver-one", 25, 1, 1), (2, "driver-two", 18, 0, 1)]

    def find_seeded_championship(self) -> str:
        self.calls.append("find-seeded")
        return "seeded-championship"

    def snapshot(self, championship_id: str) -> list[tuple[Any, ...]]:
        self.calls.append(f"snapshot:{championship_id}")
        return list(self.rows)

    def clear_standings(self, championship_id: str) -> None:
        self.calls.append(f"clear:{championship_id}")

    def prepare_gate(self, championship_id: str) -> None:
        self.calls.append(f"prepare:{championship_id}")

    def hold_gate(self) -> None:
        self.calls.append("hold")

    def wait_for_concurrent_overlap(self, timeout: float) -> bool:
        self.calls.append(f"wait:{timeout}")
        total_lock_waiters = self.advisory_waiters + self.championship_lock_waiters
        return self.advisory_waiters >= 1 and total_lock_waiters >= 2

    def release_gate(self) -> None:
        self.calls.append("release")

    def recalculate(self, championship_id: str) -> str:
        self.recalculations += 1
        call_number = self.recalculations
        if call_number == 1:
            self.calls.append(f"serial:{championship_id}")
            return "ok"
        self.concurrent.wait(timeout=2)
        self.calls.append(f"concurrent:{championship_id}")
        if self.failing and call_number == 2:
            error = RuntimeError("unique conflict")
            error.sqlstate = "23505"
            raise error
        return "ok"

    def remove_gate(self) -> None:
        self.calls.append("remove")


@pytest.mark.parametrize(
    ("advisory_waiters", "championship_lock_waiters"),
    [(2, 0), (1, 1)],
)
def test_probe_fake_adapter_requires_overlapped_success_and_consistent_rows(
    monkeypatch: pytest.MonkeyPatch,
    advisory_waiters: int,
    championship_lock_waiters: int,
) -> None:
    adapter = _FakeAdapter(
        advisory_waiters=advisory_waiters,
        championship_lock_waiters=championship_lock_waiters,
    )
    marker_checks: list[tuple[Any, ...]] = []
    monkeypatch.setattr(
        probe.acceptance,
        "verify_run_ownership",
        lambda *args: marker_checks.append(args),
    )

    result = probe.run_owned_probe(_environment(), lambda _context: adapter)

    assert result == {
        "championship_id": "seeded-championship",
        "rows": 2,
        "concurrent_requests": 2,
    }
    assert adapter.recalculations == 3
    assert adapter.calls.count("release") == 2
    assert adapter.calls[-1] == "snapshot:seeded-championship"
    assert "remove" in adapter.calls
    assert len(marker_checks) == 1


def test_probe_rejects_single_waiter_even_if_another_request_exists() -> None:
    adapter = _FakeAdapter(advisory_waiters=0, championship_lock_waiters=1)

    with pytest.raises(probe.ProbeFailure, match="lock overlap was not observed"):
        probe.run_recalculation_probe(adapter)

    assert "release" in adapter.calls
    assert adapter.calls[-1] == "remove"


def test_probe_fake_adapter_reports_unique_conflict_and_always_removes_gate() -> None:
    adapter = _FakeAdapter(failing=True)

    with pytest.raises(probe.ProbeFailure, match="SQLSTATE 23505"):
        probe.run_recalculation_probe(adapter)

    assert adapter.calls.count("release") >= 1
    assert adapter.calls[-1] == "remove"
