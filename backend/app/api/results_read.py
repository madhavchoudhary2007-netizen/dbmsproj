from collections.abc import Callable
from typing import Any, cast
from uuid import UUID

from fastapi import APIRouter

from ..database import DatabaseRow


def create_results_read_router(
    fetch_all: Callable[..., list[DatabaseRow]],
    jsonable: Callable[[Any], Any],
    connection: Callable[..., Any],
    authenticated_user_dependency: Any,
    admin_steward_dependency: Any,
) -> tuple[APIRouter, dict[str, Callable[..., Any]]]:
    router = APIRouter()

    @router.get("/api/sessions/{session_id}/results", response_model=None)
    def results(
        session_id: UUID, user: dict[str, object] = authenticated_user_dependency
    ) -> list[dict[str, object]]:
        result = jsonable(
            fetch_all(
                """SELECT r.*,u.full_name AS driver_name,d.number,t.name AS team_name,
      EXISTS(SELECT 1 FROM incident_reports i JOIN penalties p ON p.incident_id=i.id
        WHERE i.session_id=r.session_id AND (p.time_seconds>0 OR p.grid_places>0)) AS provisional
      FROM session_results r JOIN race_sessions s ON s.id=r.session_id
      JOIN drivers d ON d.id=r.driver_id JOIN users u ON u.id=d.user_id
      LEFT JOIN LATERAL (SELECT team_id FROM team_memberships m WHERE m.driver_id=d.id
        AND m.start_date<=s.scheduled_at::date AND (m.end_date IS NULL OR """
                """m.end_date>=s.scheduled_at::date)
        ORDER BY m.start_date DESC LIMIT 1) membership ON true
      LEFT JOIN teams t ON t.id=membership.team_id WHERE r.session_id=%s ORDER BY r.position""",
                (session_id,),
            )
        )
        return cast(list[dict[str, object]], result)

    @router.post("/api/championships/{championship_id}/recalculate", response_model=None)
    def recalculate(
        championship_id: UUID, user: dict[str, object] = admin_steward_dependency
    ) -> dict[str, object]:
        with connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT recalculate_standings(%s)", (championship_id,))
        return {"championship_id": str(championship_id), "recalculated": True}

    @router.get("/api/championships/{championship_id}/standings", response_model=None)
    def standings(
        championship_id: UUID, user: dict[str, object] = authenticated_user_dependency
    ) -> list[dict[str, object]]:
        result = jsonable(
            fetch_all(
                """SELECT s.*,u.full_name AS driver_name,d.number,t.name AS team_name,
      EXISTS(SELECT 1 FROM race_events re JOIN race_sessions rs ON rs.event_id=re.id
        JOIN incident_reports i ON i.session_id=rs.id JOIN penalties p ON p.incident_id=i.id
        WHERE re.championship_id=s.championship_id AND rs.session_type='RACE'
          AND rs.state='COMPLETED' AND (p.time_seconds>0 OR p.grid_places>0)) AS provisional
      FROM driver_standings s JOIN drivers d ON d.id=s.driver_id JOIN users u ON u.id=d.user_id
      LEFT JOIN team_memberships tm ON tm.driver_id=d.id AND tm.end_date IS NULL
      LEFT JOIN teams t ON t.id=tm.team_id WHERE s.championship_id=%s ORDER BY s.rank""",
                (championship_id,),
            )
        )
        return cast(list[dict[str, object]], result)

    return router, {"results": results, "standings": standings, "recalculate": recalculate}
