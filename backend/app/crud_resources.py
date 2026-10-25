from collections.abc import Callable
from typing import Any


def register_resources(crud_routes: Callable[..., Any]) -> None:
    crud_routes("championships", "championships", ("id", "name", "season"))
    crud_routes("circuits", "circuits", ("id", "name", "country", "length_km"))
    crud_routes(
        "teams",
        "teams",
        ("id", "name", "principal_user_id"),
        "LEFT JOIN users u ON u.id=teams.principal_user_id",
        "teams.*,u.full_name AS principal_name",
    )
    crud_routes(
        "drivers",
        "drivers",
        ("id", "user_id", "licence_number", "number"),
        (
            "LEFT JOIN users u ON u.id=drivers.user_id LEFT JOIN "
            "team_memberships tm ON tm.driver_id="
            "drivers.id AND tm.end_date IS NULL LEFT JOIN teams t ON t.id=tm.team_id"
        ),
        "drivers.*,u.full_name,u.email,t.name AS team_name",
    )
    crud_routes(
        "events",
        "race_events",
        ("id", "championship_id", "circuit_id", "round_number", "name", "start_date"),
        (
            "LEFT JOIN championships ch ON ch.id=race_events.championship_id LEFT JOIN "
            "circuits c ON "
            "c.id=race_events.circuit_id"
        ),
        (
            "race_events.*,ch.name AS championship_name,c.name AS ci"
            "rcuit_name,c.country AS circuit_country"
        ),
    )
    crud_routes(
        "sessions",
        "race_sessions",
        ("id", "event_id", "session_type", "scheduled_at", "total_laps", "safety_car"),
        (
            "LEFT JOIN race_events e ON e.id=race_sessions.event_id LEFT JOIN "
            "circuits c ON c.id=e.ci"
            "rcuit_id"
        ),
        "race_sessions.*,e.name AS event_name,c.name AS circuit_name",
    )
