from collections.abc import Callable, Mapping
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from psycopg.rows import dict_row

from ..database import DatabaseRow
from ..schemas_competition import ResultIn


def _save_results(
    session_id: UUID,
    rows: list[ResultIn],
    user: Any,
    fetch_one: Callable[..., DatabaseRow | None],
    connection: Callable[..., Any],
    simulations: Mapping[str, Any],
    publish: Callable[[UUID, str, Any], Any],
    jsonable: Callable[[Any], Any],
) -> Any:
    if len(rows) > 100:
        raise HTTPException(422, "At most 100 results per request")
    session = fetch_one(
        """SELECT s.state,EXISTS(SELECT 1 FROM demo_races d WHERE d.session_id=s.id) AS generated
        FROM race_sessions s WHERE s.id=%s""",
        (session_id,),
    )
    if not session:
        raise HTTPException(404, "Session not found")
    if session["state"] not in {"ACTIVE", "PAUSED", "COMPLETED"}:
        raise HTTPException(409, "Results cannot be recorded for a scheduled or cancelled session")
    sim = simulations.get(str(session_id))
    if session["generated"] and session["state"] == "ACTIVE" and sim and sim.status == "running":
        raise HTTPException(409, "The active demo simulator owns this session's results")
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        for r in rows:
            cur.execute(
                (
                    "INSERT INTO session_results(session_id,driver_id,position,lap_time_ms,pole,f"
                    "astest_lap,classified) VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(session_id,"
                    "driver_id) DO UPDATE SET position=excluded.position,lap_time_ms=excluded.lap"
                    "_time_ms,pole=excluded.pole,fastest_lap=excluded.fastest_lap,classified=excl"
                    "uded.classified"
                ),
                (
                    session_id,
                    r.driver_id,
                    r.position,
                    r.lap_time_ms,
                    r.pole,
                    r.fastest_lap,
                    r.classified,
                ),
            )
        cur.execute(
            (
                "SELECT r.*,u.full_name AS driver_name FROM session_results r JOIN drivers d ON d"
                ".id=r.driver_id JOIN users u ON u.id=d.user_id WHERE r.session_id=%s ORDER BY r."
                "position"
            ),
            (session_id,),
        )
        result = cur.fetchall()
        if session["state"] == "COMPLETED":
            classified_positions = [r["position"] for r in result if r["classified"]]
            if any(position is None for position in classified_positions) or sorted(
                classified_positions
            ) != list(range(1, len(classified_positions) + 1)):
                raise HTTPException(
                    422, "Classified result positions must be contiguous starting at 1"
                )
    publish(session_id, "timing.update", jsonable(result))
    return jsonable(result)


def create_results_write_router(
    fetch_one: Callable[..., DatabaseRow | None],
    connection: Callable[..., Any],
    simulations_provider: Callable[[], Mapping[str, Any]],
    publish: Callable[[UUID, str, Any], Any],
    jsonable: Callable[[Any], Any],
    admin_steward_dependency: Any,
) -> tuple[APIRouter, dict[str, Callable[..., Any]]]:
    router = APIRouter()

    @router.post("/api/sessions/{session_id}/results")
    def save_results(session_id: UUID, rows: list[ResultIn], user=admin_steward_dependency):
        return _save_results(
            session_id,
            rows,
            user,
            fetch_one,
            connection,
            simulations_provider(),
            publish,
            jsonable,
        )

    return router, {"save_results": save_results}
