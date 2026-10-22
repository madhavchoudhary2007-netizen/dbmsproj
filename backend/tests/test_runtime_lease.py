import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

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
