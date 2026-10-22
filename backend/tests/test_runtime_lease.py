import sys
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


@pytest.mark.xfail(strict=True, reason="F-STRUCT-01")
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
