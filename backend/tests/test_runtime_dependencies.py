import sys
from pathlib import Path
from typing import Annotated, Any

import pytest
from fastapi import Depends, FastAPI, WebSocket
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.core.runtime import (
    RuntimeState,
    get_bus,
    get_mongo,
    get_pool,
    get_runtime,
    get_simulations,
    get_telemetry,
)


class FakePool:
    def __init__(self, closed=False):
        self.closed = closed


class FakeMongo:
    def __init__(self, database):
        self.database = database

    def __getitem__(self, name):
        assert isinstance(name, str) and name
        return self.database


def _app():
    app = FastAPI()

    @app.get("/runtime")
    def runtime(
        pool: Annotated[Any, Depends(get_pool)],
        mongo: Annotated[Any, Depends(get_mongo)],
        telemetry: Annotated[Any, Depends(get_telemetry)],
        bus: Annotated[Any, Depends(get_bus)],
        simulations: Annotated[Any, Depends(get_simulations)],
    ):
        return {
            "pool": pool is app.state.expected_pool,
            "mongo": mongo is app.state.expected_mongo,
            "telemetry": telemetry is app.state.expected_telemetry,
            "bus": bus is app.state.runtime.bus,
            "simulations": simulations is app.state.runtime.simulations,
        }

    @app.websocket("/socket")
    async def socket(
        websocket: WebSocket,
        runtime_state: Annotated[RuntimeState, Depends(get_runtime)],
        bus: Annotated[Any, Depends(get_bus)],
        simulations: Annotated[Any, Depends(get_simulations)],
    ):
        await websocket.accept()
        await websocket.send_json(
            {
                "runtime": runtime_state is app.state.runtime,
                "bus": bus is app.state.runtime.bus,
                "simulations": simulations is app.state.runtime.simulations,
            }
        )

    return app


def test_runtime_instances_have_independent_bus_and_simulations():
    first, second = RuntimeState(), RuntimeState()
    assert first.bus is not second.bus
    assert first.simulations is not second.simulations


@pytest.mark.parametrize("runtime", [None, object()])
def test_missing_or_wrong_runtime_returns_503(runtime):
    app = _app()
    if runtime is not None:
        app.state.runtime = runtime
    with TestClient(app) as client:
        response = client.get("/runtime")
    assert response.status_code == 503
    assert response.json() == {"detail": "Application runtime is unavailable"}


@pytest.mark.parametrize(
    ("resource", "runtime", "message"),
    [
        (get_pool, RuntimeState(), "PostgreSQL is unavailable"),
        (get_pool, RuntimeState(pool=FakePool(closed=True)), "PostgreSQL is unavailable"),
        (get_mongo, RuntimeState(), "MongoDB document store is unavailable"),
        (get_telemetry, RuntimeState(), "MongoDB telemetry store is unavailable"),
    ],
)
def test_unavailable_runtime_resources_return_503(resource, runtime, message):
    app = FastAPI()
    app.state.runtime = runtime

    @app.get("/")
    def endpoint(value: Annotated[Any, Depends(resource)]):
        return {"available": value is not None}

    with TestClient(app) as client:
        response = client.get("/")
    assert response.status_code == 503
    assert response.json() == {"detail": message}


def test_http_and_websocket_receive_the_configured_runtime_resources():
    database, telemetry = object(), object()
    runtime = RuntimeState(
        pool=FakePool(), mongo_client=FakeMongo(database), telemetry_collection=telemetry
    )
    app = _app()
    app.state.runtime = runtime
    app.state.expected_pool = runtime.pool
    app.state.expected_mongo = database
    app.state.expected_telemetry = telemetry

    with TestClient(app) as client:
        assert client.get("/runtime").json() == {
            "pool": True,
            "mongo": True,
            "telemetry": True,
            "bus": True,
            "simulations": True,
        }
        with client.websocket_connect("/socket") as websocket:
            assert websocket.receive_json() == {
                "runtime": True,
                "bus": True,
                "simulations": True,
            }
