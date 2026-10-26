from __future__ import annotations

import json
import logging
import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.api.health import router as health_router
from backend.app.core.observability import (
    JSONLogFormatter,
    RequestCorrelationMiddleware,
    request_id_ctx,
)


def test_json_log_formatter_format_record_with_request_id() -> None:
    formatter = JSONLogFormatter()
    token = request_id_ctx.set("req-test-1234")
    try:
        record = logging.LogRecord(
            name="apexgrid.test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="User %s logged in",
            args=("admin",),
            exc_info=None,
        )
        formatted = formatter.format(record)
        data = json.loads(formatted)

        assert "timestamp" in data
        assert data["level"] == "INFO"
        assert data["logger"] == "apexgrid.test"
        assert data["message"] == "User admin logged in"
        assert data["request_id"] == "req-test-1234"
    finally:
        request_id_ctx.reset(token)


def test_json_log_formatter_format_record_without_request_id() -> None:
    formatter = JSONLogFormatter()
    record = logging.LogRecord(
        name="apexgrid.test",
        level=logging.WARNING,
        pathname="test.py",
        lineno=25,
        msg="Warning event without request context",
        args=(),
        exc_info=None,
    )
    formatted = formatter.format(record)
    data = json.loads(formatted)

    assert "timestamp" in data
    assert data["level"] == "WARNING"
    assert data["logger"] == "apexgrid.test"
    assert data["message"] == "Warning event without request context"
    assert "request_id" in data
    assert data["request_id"] is None or data["request_id"] == ""


def test_request_id_ctx_get_set() -> None:
    test_id = "test-req-id-5678"
    token = request_id_ctx.set(test_id)
    try:
        assert request_id_ctx.get() == test_id
    finally:
        request_id_ctx.reset(token)
    assert request_id_ctx.get() is None


@pytest.fixture
def test_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestCorrelationMiddleware)
    app.include_router(health_router)

    @app.get("/ping")
    def ping() -> dict[str, str]:
        current_req_id = request_id_ctx.get() or ""
        return {"ping": "pong", "ctx_id": current_req_id}

    return app


def test_request_correlation_middleware_echoes_incoming_request_id(test_app: FastAPI) -> None:
    client = TestClient(test_app)
    custom_id = "trace-client-abc-123"
    response = client.get("/ping", headers={"X-Request-ID": custom_id})

    assert response.status_code == 200
    assert response.headers.get("x-request-id") == custom_id
    data = response.json()
    assert data["ctx_id"] == custom_id


def test_request_correlation_middleware_generates_uuid_when_omitted(test_app: FastAPI) -> None:
    client = TestClient(test_app)
    response = client.get("/ping")

    assert response.status_code == 200
    req_id = response.headers.get("x-request-id")
    assert req_id is not None
    parsed = uuid.UUID(req_id)
    assert parsed.hex == req_id or str(parsed) == req_id
    data = response.json()
    assert data["ctx_id"] == req_id


def test_health_live_endpoint(test_app: FastAPI) -> None:
    client = TestClient(test_app)
    response = client.get("/health/live")

    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "alive"}
    assert response.headers.get("cache-control") == "no-store"
