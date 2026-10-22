from typing import Any
from uuid import UUID

from .database import fetch_all, fetch_one


def get_dashboard_data() -> dict[str, Any]:
    active_sessions = fetch_one("SELECT count(*) AS count FROM race_sessions WHERE state='ACTIVE'")
    scheduled_events = fetch_one(
        "SELECT count(DISTINCT e.id) AS count FROM race_events e "
        "JOIN race_sessions s ON s.event_id=e.id "
        "WHERE s.session_type='RACE' AND s.state='SCHEDULED'"
    )
    open_incidents = fetch_one("SELECT count(*) AS count FROM incident_reports WHERE state='OPEN'")
    drivers = fetch_one("SELECT count(*) AS count FROM drivers")
    active_session = fetch_one(
        "SELECT s.*,e.name AS event_name,c.name AS circuit_name "
        "FROM race_sessions s JOIN race_events e ON e.id=s.event_id "
        "JOIN circuits c ON c.id=e.circuit_id "
        "WHERE s.state IN ('ACTIVE','PAUSED') "
        "ORDER BY s.started_at DESC NULLS LAST LIMIT 1"
    )
    return {
        "active_sessions": active_sessions["count"],
        "scheduled_events": scheduled_events["count"],
        "open_incidents": open_incidents["count"],
        "drivers": drivers["count"],
        "active_session": active_session,
    }


def get_driver_analytics(
    championship_id: UUID | None,
    season: int | None,
    circuit_id: UUID | None,
    driver_id: UUID | None,
    team_id: UUID | None,
    limit: int,
    offset: int,
) -> list[dict[str, Any]]:
    filters: list[str] = []
    params: list[Any] = []
    for value, expression in (
        (championship_id, "ch.id"),
        (season, "ch.season"),
        (circuit_id, "c.id"),
        (driver_id, "d.id"),
        (team_id, "tm.team_id"),
    ):
        if value is not None:
            filters.append(expression + "=%s")
            params.append(value)
    query = (
        "SELECT d.id AS driver_id,u.full_name,d.number,t.name AS team_name,"
        "COUNT(DISTINCT sr.session_id) AS sessions,"
        "COUNT(sr.id) FILTER(WHERE sr.classified) AS classified,"
        "MIN(sr.position) AS best_finish,"
        "COUNT(sr.id) FILTER(WHERE sr.position=1) AS wins,"
        "AVG(sr.lap_time_ms) AS avg_lap_time_ms,"
        "COALESCE(MAX(st.points),0) AS points FROM drivers d "
        "JOIN users u ON u.id=d.user_id "
        "LEFT JOIN team_memberships tm ON tm.driver_id=d.id AND tm.end_date IS NULL "
        "LEFT JOIN teams t ON t.id=tm.team_id "
        "LEFT JOIN session_results sr ON sr.driver_id=d.id "
        "LEFT JOIN race_sessions rs ON rs.id=sr.session_id "
        "LEFT JOIN race_events e ON e.id=rs.event_id "
        "LEFT JOIN championships ch ON ch.id=e.championship_id "
        "LEFT JOIN circuits c ON c.id=e.circuit_id "
        "LEFT JOIN driver_standings st "
        "ON st.driver_id=d.id AND st.championship_id=ch.id"
    )
    if filters:
        query += " WHERE " + " AND ".join(filters)
    query += (
        " GROUP BY d.id,u.full_name,d.number,t.name "
        "ORDER BY points DESC,wins DESC,d.id LIMIT %s OFFSET %s"
    )
    params.extend((limit, offset))
    return fetch_all(query, params)
