"""Offline route tests for live simulation controls."""

from types import SimpleNamespace
from uuid import uuid4

import pytest
from app.api import simulation as simulation_api
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient


@pytest.fixture
def simulation_client(monkeypatch):
    simulations = {}
    app = FastAPI()
    app.include_router(simulation_api.router)
    app.dependency_overrides[simulation_api.get_simulations] = lambda: simulations
    app.dependency_overrides[simulation_api.admin_steward_dependency.dependency] = (
        lambda: {"role": "ADMIN"}
    )
    monkeypatch.setattr(simulation_api, "_resolve_mongo_ready", lambda: object())
    with TestClient(app) as client:
        yield client, simulations, app


def test_start_pause_resume_transitions_use_in_memory_simulation(
    simulation_client, monkeypatch
):
    client, simulations, _app = simulation_client
    session_id = uuid4()
    calls = []

    async def start(requested_id, body, existing):
        calls.append((requested_id, body.action, existing))
        sim = SimpleNamespace(
            status="running",
            drivers=[{"id": "driver-a"}, {"id": "driver-b"}],
            rate_hz=2.0,
        )
        simulations[str(requested_id)] = sim
        return sim

    monkeypatch.setattr(simulation_api, "_resolve_start_simulation", lambda: start)

    started = client.post(f"/api/sessions/{session_id}/simulate", json={"action": "start"})
    assert started.status_code == 200
    assert started.json() == {
        "session_id": str(session_id),
        "state": "running",
        "cars": 2,
        "rate_hz": 2.0,
    }
    assert calls == [(session_id, "start", None)]

    paused = client.post(f"/api/sessions/{session_id}/simulate", json={"action": "pause"})
    assert paused.status_code == 200
    assert paused.json() == {
        "session_id": str(session_id),
        "state": "paused",
        "cars": 2,
        "rate_hz": 2.0,
    }
    assert simulations[str(session_id)].status == "paused"

    resumed = client.post(f"/api/sessions/{session_id}/simulate", json={"action": "resume"})
    assert resumed.status_code == 200
    assert resumed.json() == {
        "session_id": str(session_id),
        "state": "running",
        "cars": 2,
        "rate_hz": 2.0,
    }
    assert simulations[str(session_id)].status == "running"


def test_reset_delegates_and_returns_reset_simulation(simulation_client, monkeypatch):
    client, simulations, _app = simulation_client
    session_id = uuid4()
    existing = SimpleNamespace(status="paused", drivers=[{"id": "driver-a"}], rate_hz=1.5)
    simulations[str(session_id)] = existing
    calls = []

    async def reset(requested_id, body, sim):
        calls.append((requested_id, body.action, sim))
        sim.status = "stopped"
        return sim

    monkeypatch.setattr(simulation_api, "_resolve_reset_simulation", lambda: reset)
    response = client.post(f"/api/sessions/{session_id}/simulate", json={"action": "reset"})

    assert response.status_code == 200
    assert response.json() == {
        "session_id": str(session_id),
        "state": "stopped",
        "cars": 1,
        "rate_hz": 1.5,
    }
    assert calls == [(session_id, "reset", existing)]


@pytest.mark.parametrize(
    ("action", "status", "detail"),
    [
        ("pause", None, "Simulation is not running"),
        ("resume", "running", "Simulation is not paused"),
    ],
)
def test_pause_and_resume_reject_invalid_states(simulation_client, action, status, detail):
    client, simulations, _app = simulation_client
    session_id = uuid4()
    if status is not None:
        simulations[str(session_id)] = SimpleNamespace(
            status=status, drivers=[], rate_hz=2.0
        )

    response = client.post(f"/api/sessions/{session_id}/simulate", json={"action": action})

    assert response.status_code == 409
    assert response.json() == {"detail": detail}


def test_start_preserves_missing_session_error(simulation_client, monkeypatch):
    client, _simulations, _app = simulation_client
    session_id = uuid4()

    async def missing_session(_requested_id, _body, _existing):
        raise HTTPException(status_code=404, detail="Session not found")

    monkeypatch.setattr(
        simulation_api, "_resolve_start_simulation", lambda: missing_session
    )
    response = client.post(f"/api/sessions/{session_id}/simulate", json={"action": "start"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Session not found"}


def test_readiness_failure_prevents_start(simulation_client, monkeypatch):
    client, _simulations, _app = simulation_client
    session_id = uuid4()
    start_calls = []

    def unavailable():
        raise HTTPException(status_code=503, detail="MongoDB telemetry store is unavailable")

    async def start(*args):
        start_calls.append(args)
        return SimpleNamespace(status="running", drivers=[], rate_hz=2.0)

    monkeypatch.setattr(simulation_api, "_resolve_mongo_ready", unavailable)
    monkeypatch.setattr(simulation_api, "_resolve_start_simulation", lambda: start)
    response = client.post(f"/api/sessions/{session_id}/simulate", json={"action": "start"})

    assert response.status_code == 503
    assert response.json() == {"detail": "MongoDB telemetry store is unavailable"}
    assert start_calls == []


def test_authorization_dependency_rejection_prevents_simulation(simulation_client, monkeypatch):
    client, _simulations, app = simulation_client
    session_id = uuid4()
    readiness_calls = []

    def deny():
        raise HTTPException(status_code=403, detail="Admin or steward role required")

    def mongo_ready():
        readiness_calls.append(True)
        return object()

    app.dependency_overrides[simulation_api.admin_steward_dependency.dependency] = deny
    monkeypatch.setattr(simulation_api, "_resolve_mongo_ready", mongo_ready)
    response = client.post(f"/api/sessions/{session_id}/simulate", json={"action": "pause"})

    assert response.status_code == 403
    assert response.json() == {"detail": "Admin or steward role required"}
    assert readiness_calls == []
