import sys
import time
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app import main as main_module
from backend.app.main import app


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
