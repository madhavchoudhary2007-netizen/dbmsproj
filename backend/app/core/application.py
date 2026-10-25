from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from psycopg import IntegrityError, OperationalError
from psycopg.errors import ExclusionViolation, ForeignKeyViolation, UniqueViolation
from psycopg_pool import PoolClosed, PoolTimeout
from starlette.middleware.base import RequestResponseEndpoint

from ..security_headers import SecurityHeadersMiddleware
from .errors import (
    conflict_handler,
    database_unavailable_handler,
    integrity_handler,
    reference_conflict_handler,
)


def create_application(
    lifespan: Callable[..., Any],
    cors_origins: list[str],
    check_runtime_lease: Callable[[Any], Any],
    secure: bool,
) -> tuple[FastAPI, Callable[..., Any]]:
    app = FastAPI(title="ApexGrid API", version="1.0.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def require_runtime_lease(
        request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if request.url.path in {"/health/live", "/health/ready"}:
            return await call_next(request)
        runtime_lease = getattr(request.app.state, "runtime_lease", None)
        if runtime_lease is not None:
            try:
                check_runtime_lease(runtime_lease)
            except RuntimeError:
                return JSONResponse(
                    status_code=503,
                    content={
                        "detail": (
                            "PostgreSQL runtime ownership was lost. Restart the backend to "
                            "restore service."
                        )
                    },
                )
        return await call_next(request)

    app.add_middleware(SecurityHeadersMiddleware, secure=secure)

    app.add_exception_handler(UniqueViolation, conflict_handler)
    app.add_exception_handler(ExclusionViolation, conflict_handler)
    app.add_exception_handler(ForeignKeyViolation, reference_conflict_handler)
    app.add_exception_handler(IntegrityError, integrity_handler)
    app.add_exception_handler(OperationalError, database_unavailable_handler)
    app.add_exception_handler(PoolTimeout, database_unavailable_handler)
    app.add_exception_handler(PoolClosed, database_unavailable_handler)

    return app, require_runtime_lease
