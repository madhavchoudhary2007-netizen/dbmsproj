from fastapi import APIRouter, Response

from ..schemas_health import LivenessReport

router = APIRouter()


@router.get("/health/live", response_model=LivenessReport)
def health_live(response: Response) -> LivenessReport:
    response.headers["Cache-Control"] = "no-store"
    return LivenessReport(status="alive")
