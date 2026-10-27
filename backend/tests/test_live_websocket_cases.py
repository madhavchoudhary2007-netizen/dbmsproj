from __future__ import annotations

import os
import sys
import time
from collections.abc import Iterator
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ.setdefault("APP_ENV", "local")

import backend.app.core.legacy_compat as legacy_compat
from backend.app.core.events import EventBus
from backend.app.core.runtime import get_bus
from backend.app.main import app

SESSION_ID = UUID("a2100000-0000-4000-8000-000000000001")
ALLOWED_ORIGIN = "https://race.example.test"
AUTH_TOKEN = ".".join(("qa", "signed", "token"))


@pytest.fixture
def live_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[TestClient, EventBus]]:
    previous_overrides = app.dependency_overrides.copy()
    previous_lease = getattr(app.state, "runtime_lease", None)
    bus = EventBus()
    app.dependency_overrides[get_bus] = lambda: bus
    monkeypatch.setattr("backend.app.main.CORS_ORIGINS", [ALLOWED_ORIGIN])
    monkeypatch.setattr("backend.app.main._check_ws_runtime_lease", _lease_is_open)
    monkeypatch.setattr(
        "backend.app.main._websocket_authenticated_user",
        lambda candidate: {"id": "qa-user"} if candidate == AUTH_TOKEN else None,
    )
    try:
        yield TestClient(app), bus
    finally:
        for session_id in list(bus.clients):
            with bus.lock:
                queues = [queue for _, queue in bus.clients.get(session_id, set())]
            for queue in queues:
                bus.unsubscribe(session_id, queue)
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)
        app.state.runtime_lease = previous_lease


async def _lease_is_open(_websocket: object) -> bool:
    return True


def _connect(client: TestClient, session_id: UUID = SESSION_ID, **kwargs: object) -> object:
    return client.websocket_connect(
        f"/api/ws/sessions/{session_id}",
        subprotocols=["apexgrid.jwt", AUTH_TOKEN],
        **kwargs,
    )


def _wait_for_subscription(bus: EventBus, session_id: UUID) -> None:
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        with bus.lock:
            if bus.clients.get(str(session_id)):
                return
        time.sleep(0.01)
    raise AssertionError("WebSocket did not subscribe to its session event bus")


def _wait_for_unsubscribe(bus: EventBus, session_id: UUID) -> bool:
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        with bus.lock:
            if not bus.clients.get(str(session_id)):
                return True
        time.sleep(0.01)
    return False


def test_allowed_origin_authenticates_and_forwards_session_event(
    live_client: tuple[TestClient, EventBus],
) -> None:
    client, bus = live_client

    with _connect(client, headers={"origin": ALLOWED_ORIGIN}) as websocket:
        _wait_for_subscription(bus, SESSION_ID)
        event = {"type": "timing.update", "session_id": str(SESSION_ID), "data": {"lap": 4}}
        bus.send(SESSION_ID, event)
        assert websocket.receive_json() == event


def test_disallowed_origin_is_rejected_before_authentication(
    live_client: tuple[TestClient, EventBus],
) -> None:
    client, bus = live_client

    with pytest.raises(WebSocketDisconnect) as disconnected, client.websocket_connect(
        f"/api/ws/sessions/{SESSION_ID}",
        headers={"origin": "https://attacker.invalid"},
    ):
        pytest.fail("A disallowed origin must not establish a WebSocket")

    assert disconnected.value.code == 4403
    assert not bus.clients


@pytest.mark.parametrize(
    ("subprotocols", "expected_reason"),
    [
        ([], "Expected apexgrid.jwt subprotocol and bearer token"),
        (["apexgrid.jwt", "bad-token"], "Invalid or expired token"),
    ],
)
def test_missing_or_invalid_authentication_is_rejected(
    live_client: tuple[TestClient, EventBus],
    subprotocols: list[str],
    expected_reason: str,
) -> None:
    client, bus = live_client

    with pytest.raises(WebSocketDisconnect) as disconnected, client.websocket_connect(
        f"/api/ws/sessions/{SESSION_ID}",
        subprotocols=subprotocols,
        headers={"origin": ALLOWED_ORIGIN},
    ):
        pytest.fail("Unauthenticated WebSocket must be rejected")

    assert disconnected.value.code == 4401
    assert expected_reason in disconnected.value.reason
    assert not bus.clients


def test_closed_runtime_lease_rejects_connection_before_auth(
    live_client: tuple[TestClient, EventBus], monkeypatch: pytest.MonkeyPatch
) -> None:
    client, bus = live_client
    app.state.runtime_lease = object()

    def closed(_lease: object) -> None:
        raise RuntimeError("runtime lease lost")

    monkeypatch.setattr(legacy_compat, "check_runtime_lease", closed)
    monkeypatch.setattr(
        "backend.app.main._check_ws_runtime_lease", legacy_compat._check_ws_runtime_lease
    )

    with pytest.raises(WebSocketDisconnect) as disconnected, client.websocket_connect(
        f"/api/ws/sessions/{SESSION_ID}"
    ):
        pytest.fail("A closed runtime lease must reject the WebSocket")

    assert disconnected.value.code == 1011
    assert "runtime ownership was lost" in disconnected.value.reason.lower()
    assert not bus.clients


def test_idle_client_disconnect_unsubscribes_without_waiting_for_an_event(
    live_client: tuple[TestClient, EventBus],
) -> None:
    client, bus = live_client
    subscribed = False

    with _connect(client) as websocket:
        _wait_for_subscription(bus, SESSION_ID)
        subscribed = True
        websocket.close()

    cleaned_up = _wait_for_unsubscribe(bus, SESSION_ID)
    if not cleaned_up and subscribed:
        # Wake the route after recording the result so the test leaves no task behind.
        bus.send(SESSION_ID, {"type": "cleanup"})
        _wait_for_unsubscribe(bus, SESSION_ID)
    assert cleaned_up, "Idle client disconnect should unsubscribe without a later bus event"

