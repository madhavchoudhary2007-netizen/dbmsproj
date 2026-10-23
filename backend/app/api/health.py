from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, FastAPI, Response

from ..schemas_health import HealthReport as HealthReport
from ..schemas_health import LivenessReport as LivenessReport
from ..schemas_health import ReadinessReport as ReadinessReport

router = APIRouter()


@router.get("/health/live", response_model=LivenessReport)
def health_live(response: Response) -> LivenessReport:
    response.headers["Cache-Control"] = "no-store"
    return LivenessReport(status="alive")


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
