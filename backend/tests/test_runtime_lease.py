import asyncio
import subprocess
import sys
import time
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app import main as main_module
from backend.app.main import app
from backend.app.simulation_core import Simulation


@pytest.mark.xfail(strict=True, reason="F-STRUCT-02")
def test_uvicorn_import_contract():
    backend_dir = Path(__file__).resolve().parents[1]
    env = {"APP_ENV": "local", "PYTHONPATH": str(backend_dir)}
    result = subprocess.run(
        [sys.executable, "-c", "import app.main"],
        cwd=backend_dir,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        assert "No module named 'backend'" in result.stderr
    assert result.returncode == 0, result.stderr


def test_runtime_lease_exclusive():
    from backend.app.runtime_lease import acquire_runtime_lease, check_runtime_lease

    first = second = None
    try:
        first = acquire_runtime_lease()
        with pytest.raises(RuntimeError, match=r"(?i)active.*owner"):
            acquire_runtime_lease()

        first.close()
        second = acquire_runtime_lease()
        assert second.closed is False
        with pytest.raises(RuntimeError):
            check_runtime_lease(first)
    finally:
        if first is not None:
            first.close()
        if second is not None:
            second.close()


def test_runtime_lifespan_rejects_second_owner():
    from backend.app.runtime_lease import acquire_runtime_lease

    held_lease = acquire_runtime_lease()
    try:
        with pytest.raises(RuntimeError, match=r"(?i)active.*owner"), TestClient(app):
            pass
    finally:
        held_lease.close()


def test_runtime_lease_loss_fails_closed(monkeypatch):
    real_acquire = main_module.acquire_runtime_lease
    captured_leases = []

    def capture_runtime_lease():
        lease = real_acquire()
        captured_leases.append(lease)
        return lease

    try:
        with monkeypatch.context() as patch:
            patch.setattr(main_module, "acquire_runtime_lease", capture_runtime_lease)
            with TestClient(app) as client:
                assert len(captured_leases) == 1
                captured_leases[0].close()
                health_response = client.get("/api/health")
                live_response = client.get(f"/api/sessions/{uuid4()}/live")

            assert health_response.status_code == 503
            assert live_response.status_code == 503
    finally:
        for lease in captured_leases:
            lease.close()


def test_runtime_websocket_loss(monkeypatch):
    from starlette.websockets import WebSocketDisconnect

    real_acquire = main_module.acquire_runtime_lease
    captured_leases = []

    def capture_runtime_lease():
        lease = real_acquire()
        captured_leases.append(lease)
        return lease

    try:
        with monkeypatch.context() as patch:
            patch.setattr(main_module, "acquire_runtime_lease", capture_runtime_lease)
            with TestClient(app) as client:
                assert len(captured_leases) == 1
                captured_leases[0].close()
                with (
                    pytest.raises(WebSocketDisconnect) as disconnected,
                    client.websocket_connect(f"/api/ws/sessions/{uuid4()}"),
                ):
                    pass

            assert disconnected.value.code == 1011
            assert "runtime ownership was lost" in disconnected.value.reason.lower()
    finally:
        for lease in captured_leases:
            lease.close()


def test_active_websocket_loss_closes_before_delivering_event(monkeypatch):
    from starlette.websockets import WebSocketDisconnect

    real_acquire = main_module.acquire_runtime_lease
    captured_leases = []
    session_id = uuid4()

    def capture_runtime_lease():
        lease = real_acquire()
        captured_leases.append(lease)
        return lease

    try:
        with monkeypatch.context() as patch:
            patch.setattr(main_module, "acquire_runtime_lease", capture_runtime_lease)
            with TestClient(app) as client:
                assert len(captured_leases) == 1
                patch.setattr(main_module.jwt, "decode", lambda *args, **kwargs: {"sub": "qa-user"})
                patch.setattr(main_module, "fetch_one", lambda *args, **kwargs: {"id": "qa-user"})
                with client.websocket_connect(
                    f"/api/ws/sessions/{session_id}",
                    subprotocols=["apexgrid.jwt", "qa-token"],
                ) as websocket:
                    deadline = time.monotonic() + 2
                    while time.monotonic() < deadline:
                        with main_module.bus.lock:
                            subscriptions = list(main_module.bus.clients.get(str(session_id), ()))
                        if subscriptions:
                            break
                        time.sleep(0.01)
                    assert subscriptions, "WebSocket did not subscribe before timeout"

                    captured_leases[0].close()
                    main_module.bus.send(str(session_id), {"type": "timing", "data": {"lap": 1}})
                    with pytest.raises(WebSocketDisconnect) as disconnected:
                        websocket.receive_json()

                    assert disconnected.value.code == 1011
                    assert "runtime ownership was lost" in disconnected.value.reason.lower()
    finally:
        with main_module.bus.lock:
            subscriptions = list(main_module.bus.clients.get(str(session_id), ()))
        for _, queue in subscriptions:
            main_module.bus.unsubscribe(session_id, queue)
        for lease in captured_leases:
            lease.close()


def test_idle_websocket_loss_unsubscribes_without_bus_events(monkeypatch):
    real_acquire = main_module.acquire_runtime_lease
    captured_leases = []
    session_id = uuid4()

    def capture_runtime_lease():
        lease = real_acquire()
        captured_leases.append(lease)
        return lease

    try:
        with monkeypatch.context() as patch:
            patch.setattr(main_module, "acquire_runtime_lease", capture_runtime_lease)
            with TestClient(app) as client:
                assert len(captured_leases) == 1
                patch.setattr(main_module.jwt, "decode", lambda *args, **kwargs: {"sub": "qa-user"})
                patch.setattr(main_module, "fetch_one", lambda *args, **kwargs: {"id": "qa-user"})
                with client.websocket_connect(
                    f"/api/ws/sessions/{session_id}",
                    subprotocols=["apexgrid.jwt", "qa-token"],
                ):
                    deadline = time.monotonic() + 2
                    subscriptions = []
                    while time.monotonic() < deadline:
                        with main_module.bus.lock:
                            subscriptions = list(main_module.bus.clients.get(str(session_id), ()))
                        if subscriptions:
                            break
                        time.sleep(0.01)
                    assert subscriptions, "WebSocket did not subscribe before timeout"

                    captured_leases[0].close()
                    deadline = time.monotonic() + 2
                    while time.monotonic() < deadline:
                        with main_module.bus.lock:
                            subscriptions = list(main_module.bus.clients.get(str(session_id), ()))
                        if not subscriptions:
                            break
                        time.sleep(0.01)
                    assert not subscriptions, (
                        "idle WebSocket retained its bus subscription after lease loss"
                    )
    finally:
        with main_module.bus.lock:
            subscriptions = list(main_module.bus.clients.get(str(session_id), ()))
        for _, queue in subscriptions:
            main_module.bus.unsubscribe(session_id, queue)
        for lease in captured_leases:
            lease.close()


@pytest.mark.parametrize("status", ["paused", "running"])
def test_simulation_lease_loss(monkeypatch, status):
    from backend.app.runtime_lease import check_runtime_lease

    session_id = uuid4()
    sim = Simulation(session_id, [], 2.0, status=status)
    owner = type("ClosedOwner", (), {"closed": True})()
    state = app.state._state
    had_lease = "runtime_lease" in state
    previous_lease = state.get("runtime_lease")
    calls = []

    def record_fetch(*args, **kwargs):
        calls.append((args, kwargs))
        return None

    try:
        app.state.runtime_lease = owner
        with pytest.raises(RuntimeError, match="closed"):
            check_runtime_lease(owner)

        with monkeypatch.context() as patch:
            patch.setattr(main_module, "mongo_ready", lambda: object())
            patch.setattr(main_module, "fetch_one", record_fetch)
            try:
                asyncio.run(asyncio.wait_for(main_module.simulation_loop(sim), timeout=0.5))
            except TimeoutError:
                pytest.fail("simulation loop did not stop within 0.5 seconds")

        assert sim.status == "error"
        assert calls == []
    finally:
        if had_lease:
            app.state.runtime_lease = previous_lease
        else:
            state.pop("runtime_lease", None)
