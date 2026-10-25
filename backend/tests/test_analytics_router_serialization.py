from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from app.analytics_router import router
from app.core.request_auth import current_user
from app.core.request_database import get_database
from fastapi import FastAPI
from fastapi.testclient import TestClient

DRIVER_ID = UUID("12345678-1234-5678-1234-567812345678")
SESSION_ID = UUID("22345678-1234-5678-1234-567812345678")
EVENT_ID = UUID("32345678-1234-5678-1234-567812345678")
STARTED_AT = datetime(2026, 5, 1, 12, 30, tzinfo=UTC)
EVENT_DATE = date(2026, 6, 2)


class FakeDatabase:
    def __init__(self, *, nullable: bool = False) -> None:
        self.nullable = nullable
        self.fetch_one_calls = 0

    def fetch_all(self, sql: str, params: tuple[object, ...] = ()) -> list[dict[str, object]]:
        return [
            {
                "driver_id": DRIVER_ID,
                "full_name": "A. Driver",
                "number": 7,
                "team_name": "Example",
                "sessions": 3,
                "classified": 2,
                "best_finish": 1,
                "wins": 1,
                "avg_lap_time_ms": Decimal("91234.5"),
                "points": Decimal("42.75"),
            },
            {
                "driver_id": DRIVER_ID,
                "full_name": "B. Driver",
                "number": 8,
                "team_name": None,
                "sessions": 1,
                "classified": 0,
                "best_finish": None,
                "wins": 0,
                "avg_lap_time_ms": None,
                "points": Decimal("0"),
            },
        ]

    def fetch_one(self, sql: str, params: tuple[object, ...] = ()) -> dict[str, object] | None:
        index = self.fetch_one_calls
        self.fetch_one_calls += 1
        if index < 4:
            return {"count": 11 + index}
        if index == 4:
            return None if self.nullable else {"id": SESSION_ID, "started_at": STARTED_AT}
        if index == 5:
            return None if self.nullable else {"id": EVENT_ID, "event_date": EVENT_DATE}
        raise AssertionError("dashboard made more than six fetch_one calls")


def _client(database: FakeDatabase) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[current_user] = lambda: {"id": "offline-test-user"}
    app.dependency_overrides[get_database] = lambda: database
    return TestClient(app)


def test_driver_analytics_serializes_exact_numeric_values() -> None:
    database = FakeDatabase()
    with _client(database) as client:
        response = client.get("/api/analytics/drivers")
    assert response.status_code == 200, response.text
    rows = response.json()
    assert isinstance(rows, list) and len(rows) == 2
    first, second = rows
    assert isinstance(first["avg_lap_time_ms"], (int, float))
    assert first["avg_lap_time_ms"] == 91234.5
    assert isinstance(first["points"], (int, float)) and first["points"] == 42.75
    assert second["avg_lap_time_ms"] is None
    assert isinstance(second["points"], (int, float)) and second["points"] == 0
    assert first["driver_id"] == str(DRIVER_ID)


def test_dashboard_serializes_dates_uuids_counts_and_nullable_rows() -> None:
    database = FakeDatabase()
    with _client(database) as client:
        response = client.get("/api/dashboard")
    assert response.status_code == 200, response.text
    dashboard = response.json()
    assert database.fetch_one_calls == 6
    counts = [
        value for key, value in dashboard.items() if key not in {"active_session", "next_event"}
    ]
    assert all(isinstance(value, int) for value in counts)
    assert dashboard["active_session"]["id"] == str(SESSION_ID)
    assert dashboard["active_session"]["started_at"] == STARTED_AT.isoformat().replace(
        "+00:00", "Z"
    )
    assert dashboard["next_event"]["id"] == str(EVENT_ID)
    assert dashboard["next_event"]["event_date"] == EVENT_DATE.isoformat()

    nullable_database = FakeDatabase(nullable=True)
    with _client(nullable_database) as client:
        nullable_response = client.get("/api/dashboard")
    nullable_dashboard = nullable_response.json()
    assert nullable_response.status_code == 200, nullable_response.text
    assert nullable_dashboard["active_session"] is None
    assert nullable_dashboard["next_event"] is None
    nullable_counts = [
        value
        for key, value in nullable_dashboard.items()
        if key not in {"active_session", "next_event"}
    ]
    assert all(isinstance(value, int) for value in nullable_counts)
