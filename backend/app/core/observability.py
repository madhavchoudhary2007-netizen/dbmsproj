from __future__ import annotations

import contextvars
import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

request_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)
request_id_var = request_id_ctx


class JSONLogFormatter(logging.Formatter):
    """Formats log records as single-line JSON with context correlation."""

    def format(self, record: logging.LogRecord) -> str:
        record.message = record.getMessage()
        req_id = getattr(record, "request_id", None) or request_id_ctx.get()
        if self.datefmt:
            timestamp = self.formatTime(record, self.datefmt)
        else:
            timestamp = datetime.fromtimestamp(record.created, tz=UTC).isoformat()

        payload: dict[str, Any] = {
            "timestamp": timestamp,
            "level": record.levelname,
            "logger": record.name,
            "message": record.message,
            "request_id": req_id,
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging(level: int = logging.INFO) -> None:
    """Configures root and apexgrid loggers with JSONLogFormatter."""
    handler = logging.StreamHandler()
    handler.setFormatter(JSONLogFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = [handler]

    apexgrid_logger = logging.getLogger("apexgrid")
    apexgrid_logger.setLevel(level)


class RequestCorrelationMiddleware(BaseHTTPMiddleware):
    """Extracts or generates an X-Request-ID header and propagates via request_id_ctx."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        incoming_id = request.headers.get("x-request-id")
        req_id = incoming_id.strip() if incoming_id and incoming_id.strip() else uuid.uuid4().hex
        token = request_id_ctx.set(req_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = req_id
            return response
        finally:
            request_id_ctx.reset(token)


__all__ = [
    "JSONLogFormatter",
    "RequestCorrelationMiddleware",
    "configure_logging",
    "request_id_ctx",
    "request_id_var",
]
