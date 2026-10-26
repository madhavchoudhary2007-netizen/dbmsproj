from __future__ import annotations

from pathlib import Path
from uuid import UUID

import pytest

from backend.app.schemas_competition import PointsSystemOut, PointsSystemPositionOut

STANDARD_F1_POINTS: dict[int, int] = {
    1: 25,
    2: 18,
    3: 15,
    4: 12,
    5: 10,
    6: 8,
    7: 6,
    8: 4,
    9: 2,
    10: 1,
}


def f1_points_for_position(position: int) -> int:
    """Return points awarded under standard Formula 1 rules (top 10 positions)."""
    return STANDARD_F1_POINTS.get(position, 0)


def test_migration_005_points_systems_content() -> None:
    migration_path = Path("backend/migrations/005_points_systems.sql")
    assert migration_path.is_file(), "Migration 005_points_systems.sql does not exist"
    content = migration_path.read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS points_systems" in content
    assert "points_system_positions" in content
    assert "points_system_id" in content
    assert "recalculate_standings" in content


@pytest.mark.parametrize(
    ("position", "expected_points"),
    [
        (1, 25),
        (2, 18),
        (3, 15),
        (4, 12),
        (5, 10),
        (6, 8),
        (7, 6),
        (8, 4),
        (9, 2),
        (10, 1),
        (11, 0),
        (12, 0),
        (15, 0),
        (20, 0),
        (99, 0),
    ],
)
def test_standard_f1_points_distribution(position: int, expected_points: int) -> None:
    assert f1_points_for_position(position) == expected_points


def test_points_system_position_schema_validates_payload() -> None:
    payload = {
        "id": "00000000-0000-0000-0000-000000000010",
        "system_id": "00000000-0000-0000-0000-000000000001",
        "position": 1,
        "points": 25,
    }
    pos = PointsSystemPositionOut.model_validate(payload)
    assert pos.id == UUID("00000000-0000-0000-0000-000000000010")
    assert pos.system_id == UUID("00000000-0000-0000-0000-000000000001")
    assert pos.position == 1
    assert pos.points == 25


def test_points_system_schema_validates_payload() -> None:
    payload = {
        "id": "00000000-0000-0000-0000-000000000001",
        "name": "FIA Formula 1 Standard (2025)",
        "is_default": True,
        "positions": [
            {
                "id": "00000000-0000-0000-0000-000000000010",
                "system_id": "00000000-0000-0000-0000-000000000001",
                "position": 1,
                "points": 25,
            },
            {
                "id": "00000000-0000-0000-0000-000000000011",
                "system_id": "00000000-0000-0000-0000-000000000001",
                "position": 2,
                "points": 18,
            },
        ],
    }
    sys_out = PointsSystemOut.model_validate(payload)
    assert sys_out.id == UUID("00000000-0000-0000-0000-000000000001")
    assert sys_out.name == "FIA Formula 1 Standard (2025)"
    assert sys_out.is_default is True
    assert sys_out.positions is not None
    assert len(sys_out.positions) == 2
    assert sys_out.positions[0].points == 25
    assert sys_out.positions[1].points == 18
