from collections.abc import Callable
from contextlib import suppress
from typing import Any, Literal

from fastapi import APIRouter, FastAPI, Response
from pymongo import MongoClient

from ..schemas_health import HealthReport as HealthReport
from ..schemas_health import LivenessReport as LivenessReport
from ..schemas_health import ReadinessReport as ReadinessReport

router = APIRouter()
legacy_router = APIRouter()


@router.get("/health/live", response_model=LivenessReport)
def health_live(response: Response) -> LivenessReport:
    response.headers["Cache-Control"] = "no-store"
    return LivenessReport(status="alive")


def register_legacy_health(
    fetch_one: Callable[[str], Any],
    get_mongo_client: Callable[[], MongoClient[dict[str, Any]] | None],
) -> Callable[[], HealthReport]:
    @legacy_router.get("/api/health", response_model=None)
    def health() -> HealthReport:
        mongo_client = get_mongo_client()
        state: dict[str, Literal["up", "down"]] = {
            "postgres": "down",
            "mongodb": "down",
        }
        with suppress(Exception):
            fetch_one("SELECT 1 AS ok")
            state["postgres"] = "up"
        with suppress(Exception):
            if mongo_client:
                mongo_client.admin.command("ping")
                state["mongodb"] = "up"
        return {
            "status": "ok" if all(v == "up" for v in state.values()) else "degraded",
            "services": state,
        }

    return health


def register_readiness(
    application: FastAPI,
    health: Callable[[], HealthReport],
    check_runtime_lease: Callable[[Any], None],
) -> Callable[[Response], ReadinessReport]:
    app = application

    @router.get("/health/ready", response_model=ReadinessReport)
    def health_ready(response: Response) -> ReadinessReport:
        services = dict(health()["services"])
        runtime_lease = getattr(app.state, "runtime_lease", None)
        if runtime_lease is None:
            services["runtime_lease"] = "down"
        else:
            try:
                check_runtime_lease(runtime_lease)
                services["runtime_lease"] = "up"
            except RuntimeError:
                services["runtime_lease"] = "down"

        ready = all(services.get(key) == "up" for key in ("postgres", "mongodb", "runtime_lease"))
        if not ready:
            response.status_code = 503
        return ReadinessReport(status="ready" if ready else "not_ready", services=services)

    return health_ready
