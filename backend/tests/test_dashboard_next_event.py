from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID

import pytest
from app import analytics_repository


@pytest.mark.parametrize(
    "candidate",
    [
        None,
        {
            "id": UUID("00000000-0000-0000-0000-000000000001"),
            "name": "Harbor Grand Prix",
            "session_id": UUID("00000000-0000-0000-0000-000000000002"),
            "scheduled_at": datetime(2026, 10, 25, 12, 0, tzinfo=UTC),
            "circuit_name": "Harbor Ring",
        },
    ],
)
def test_dashboard_next_event_preserves_old_fields_and_candidate(candidate):
    rows = iter(
        [
            {"count": 2},
            {"count": 3},
            {"count": 1},
            {"count": 24},
            None,
            candidate,
        ]
    )
    database = SimpleNamespace(fetch_one=lambda *_args: next(rows))

    dashboard = analytics_repository.get_dashboard_data(database)

    assert dashboard == {
        "active_sessions": 2,
        "scheduled_events": 3,
        "open_incidents": 1,
        "drivers": 24,
        "active_session": None,
        "next_event": candidate,
    }
