"""Offline safety tests for the acceptance script's owned fixture helpers."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from urllib.parse import quote

import pytest

_ACCEPTANCE_PATH = Path(__file__).resolve().parents[1] / "acceptance.py"
_ACCEPTANCE_SPEC = importlib.util.spec_from_file_location("acceptance_under_test", _ACCEPTANCE_PATH)
assert _ACCEPTANCE_SPEC is not None and _ACCEPTANCE_SPEC.loader is not None
acceptance = importlib.util.module_from_spec(_ACCEPTANCE_SPEC)
_ACCEPTANCE_SPEC.loader.exec_module(acceptance)


def _database_url(host: str, port: int, database: str) -> str:
    # These are inert fake credentials; the tests never open this URL.
    return f"postgresql://unit:unit@{host}:{port}/{quote(database)}"


@pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "[::1]"])
def test_disposable_guard_accepts_owned_loopback_database_names(host: str) -> None:
    suffix = "unit-44647-a82d"
    name = f"apexgrid_acceptance_{suffix}"

    acceptance.ensure_disposable_target(_database_url(host, 15432, name), name)


@pytest.mark.parametrize(
    ("host", "port", "database", "mongo_database"),
    [
        ("db.example.invalid", 15432, "apexgrid_acceptance_run1", "apexgrid_acceptance_run1"),
        ("127.0.0.1", 5432, "apexgrid_acceptance_run1", "apexgrid_acceptance_run1"),
        ("127.0.0.1", 15432, "apexgrid", "apexgrid_acceptance_run1"),
        ("127.0.0.1", 15432, "apexgrid_acceptance_run1", "apexgrid"),
        ("127.0.0.1", 15432, "apexgrid_acceptance_run1", "apexgrid_acceptance_other"),
        ("127.0.0.1", 15432, "apexgrid_acceptance_", "apexgrid_acceptance_"),
    ],
)
def test_disposable_guard_rejects_unsafe_or_unowned_targets(
    host: str, port: int, database: str, mongo_database: str
) -> None:
    with pytest.raises((ValueError, RuntimeError)):
        acceptance.ensure_disposable_target(
            _database_url(host, port, database), mongo_database
        )


def test_fixture_uses_unique_named_championship_and_round_three_event(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, str | None, dict[str, object] | None, str | None]] = []
    existing = [
        {"id": "old-champ", "name": "ApexGrid World Series", "season": 2028},
        {"id": "other-champ", "name": "Acceptance fixture prior", "season": 2031},
    ]

    def fake_expect(
        path: str,
        token: str | None = None,
        body: dict[str, object] | None = None,
        method: str | None = None,
        status: int = 200,
    ) -> object:
        calls.append((path, token, body, method))
        if path.startswith("/championships?"):
            return existing
        if path == "/championships":
            assert method == "POST"
            return {"id": "owned-champ", **(body or {})}
        if path == "/events":
            assert method == "POST"
            return {"id": "owned-event", **(body or {})}
        raise AssertionError(f"unexpected fake API request: {path}")

    monkeypatch.setattr(acceptance, "expect", fake_expect)
    fixture = acceptance.create_owned_fixture("fake-token", "circuit-7", "unit-44647-z91")

    posts = [(path, body) for path, _, body, method in calls if method == "POST"]
    assert len(posts) == 2
    championship_body = posts[0][1]
    event_body = posts[1][1]
    assert championship_body is not None and event_body is not None
    assert "unit-44647-z91" in str(championship_body["name"])
    assert "test" in str(championship_body["name"]).lower()
    assert championship_body["season"] not in {2028, 2031}
    assert event_body["championship_id"] == "owned-champ"
    assert event_body["circuit_id"] == "circuit-7"
    assert event_body["round_number"] == 3
    assert fixture["championship_id"] == "owned-champ"
    assert fixture["event_id"] == "owned-event"
    assert fixture["unique_suffix"] == "unit-44647-z91"


def test_failed_event_creation_removes_only_just_created_championship(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, str | None]] = []

    def fake_expect(
        path: str,
        token: str | None = None,
        body: dict[str, object] | None = None,
        method: str | None = None,
        status: int = 200,
    ) -> object:
        calls.append((f"{method or 'GET'} {path}", token))
        if path.startswith("/championships?"):
            return [{"id": "unrelated", "name": "Untouched", "season": 2040}]
        if path == "/championships" and method == "POST":
            return {"id": "owned-partial", **(body or {})}
        if path == "/events" and method == "POST":
            raise RuntimeError("simulated event API failure")
        if path == "/championships/owned-partial" and method == "DELETE":
            return None
        raise AssertionError(f"unexpected fake API request: {method} {path}")

    monkeypatch.setattr(acceptance, "expect", fake_expect)
    with pytest.raises(RuntimeError, match="event API failure"):
        acceptance.create_owned_fixture("fake-token", "circuit-7", "unit-partial-k4")

    assert calls.count(("DELETE /championships/owned-partial", "fake-token")) == 1
    assert not any("/unrelated" in path for path, _ in calls)


def test_cleanup_deletes_dependents_before_owned_event_and_championship(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, str | None]] = []
    dependent_rows: dict[str, list[dict[str, str]]] = {
        "/sessions?limit=200&offset=0": [{"id": "owned-session", "event_id": "owned-event"}],
        "/results?limit=200&offset=0": [{"id": "owned-result", "event_id": "owned-event"}],
    }

    def fake_expect(
        path: str,
        token: str | None = None,
        body: dict[str, object] | None = None,
        method: str | None = None,
        status: int = 200,
    ) -> object:
        calls.append((f"{method or 'GET'} {path}", token))
        if method is None:
            return dependent_rows.get(path, [])
        if method == "DELETE":
            return None
        raise AssertionError(f"unexpected fake API request: {method} {path}")

    monkeypatch.setattr(acceptance, "expect", fake_expect)
    acceptance.cleanup_owned_fixture(
        "fake-token",
        {
            "championship_id": "owned-champ",
            "event_id": "owned-event",
            "unique_suffix": "unit-cleanup-v2",
        },
    )

    deleted = [path for path, _ in calls if path.startswith("DELETE ")]
    assert deleted.index("DELETE /sessions/owned-session") < deleted.index(
        "DELETE /events/owned-event"
    )
    assert deleted.index("DELETE /results/owned-result") < deleted.index(
        "DELETE /events/owned-event"
    )
    assert deleted.index("DELETE /events/owned-event") < deleted.index(
        "DELETE /championships/owned-champ"
    )
    assert all("unrelated" not in path for path in deleted)


def test_cleanup_is_safe_for_partial_owned_fixture(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_expect(
        path: str,
        token: str | None = None,
        body: dict[str, object] | None = None,
        method: str | None = None,
        status: int = 200,
    ) -> object:
        calls.append(f"{method or 'GET'} {path}")
        if method is None:
            return []
        return None

    monkeypatch.setattr(acceptance, "expect", fake_expect)
    acceptance.cleanup_owned_fixture(
        "fake-token",
        {"championship_id": "owned-partial", "event_id": None, "unique_suffix": "unit-partial"},
    )

    assert "DELETE /championships/owned-partial" in calls
    assert not any(path.startswith("DELETE /events/") for path in calls)


class _FakeListeningSocket:
    def __init__(self) -> None:
        self.closed = False
        self.bound: tuple[str, int] | None = None
        self.fd = 71

    def bind(self, address: tuple[str, int]) -> None:
        self.bound = address

    def listen(self, backlog: int) -> None:
        assert self.bound is not None
        assert backlog > 0

    def getsockname(self) -> tuple[str, int]:
        assert self.bound is not None
        return (self.bound[0], 43127)

    def fileno(self) -> int:
        return self.fd

    def close(self) -> None:
        self.closed = True


class _FakeProcess:
    def __init__(self) -> None:
        self.terminated = False
        self.killed = False

    def poll(self) -> int | None:
        return -15 if self.terminated else None

    def terminate(self) -> None:
        self.terminated = True

    def wait(self, timeout: int) -> int:
        assert self.terminated or self.killed
        return -15

    def kill(self) -> None:
        self.killed = True


def test_owned_api_passes_open_listener_and_owned_environment_to_child(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    listener = _FakeListeningSocket()
    process = _FakeProcess()
    launch: dict[str, object] = {}

    monkeypatch.setattr(acceptance.socket, "socket", lambda *_args: listener)

    def fake_popen(args: list[str], **kwargs: object) -> _FakeProcess:
        launch["args"] = args
        launch.update(kwargs)
        assert not listener.closed
        return process

    monkeypatch.setattr(acceptance.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(
        acceptance,
        "expect",
        lambda *_args, **_kwargs: {"services": {"postgres": "up", "mongodb": "up"}},
    )

    result = acceptance.start_owned_api(
        _database_url("127.0.0.1", 15432, "apexgrid_acceptance_unit"),
        "mongodb://unit:unit@127.0.0.1:27017/apexgrid_acceptance_owned-a8?authSource=admin",
    )

    args = launch["args"]
    assert isinstance(args, list)
    fd_index = args.index("--fd")
    assert args[fd_index + 1] == str(listener.fd)
    assert launch["pass_fds"] == (listener.fd,)
    child_env = launch["env"]
    assert isinstance(child_env, dict)
    assert child_env["MONGODB_DATABASE"] == "apexgrid_acceptance_owned-a8"
    assert child_env["AUTO_DEMO_RACE"] == "0"
    assert listener.closed
    assert result is process


def test_owned_api_closes_listener_when_child_cannot_start(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    listener = _FakeListeningSocket()
    monkeypatch.setattr(acceptance.socket, "socket", lambda *_args: listener)

    def failed_popen(*_args: object, **_kwargs: object) -> None:
        raise OSError("simulated child launch failure")

    monkeypatch.setattr(acceptance.subprocess, "Popen", failed_popen)
    with pytest.raises(OSError, match="child launch failure"):
        acceptance.start_owned_api("postgresql://unit:unit@127.0.0.1:15432/apexgrid_acceptance_x", "mongodb://127.0.0.1/apexgrid_acceptance_x")

    assert listener.closed


def test_owned_api_terminates_child_and_closes_listener_if_health_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    listener = _FakeListeningSocket()
    process = _FakeProcess()
    monkeypatch.setattr(acceptance.socket, "socket", lambda *_args: listener)

    def fake_popen(*_args: object, **_kwargs: object) -> _FakeProcess:
        assert not listener.closed
        return process

    monotonic_values = iter([0.0, 31.0])
    monkeypatch.setattr(acceptance.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(acceptance.time, "monotonic", lambda: next(monotonic_values))
    monkeypatch.setattr(acceptance.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(acceptance, "expect", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("not healthy")))

    with pytest.raises(RuntimeError, match="did not become healthy"):
        acceptance.start_owned_api("postgresql://unit:unit@127.0.0.1:15432/apexgrid_acceptance_x", "mongodb://127.0.0.1/apexgrid_acceptance_x")

    assert listener.closed
    assert process.terminated
