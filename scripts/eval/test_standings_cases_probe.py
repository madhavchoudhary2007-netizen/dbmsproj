from __future__ import annotations

# ruff: noqa: S101
import importlib.util
import sys
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest

_PROBE_PATH = Path(__file__).with_name("standings_cases_probe.py")
_PROBE_SPEC = importlib.util.spec_from_file_location(
    "standings_cases_probe_under_test", _PROBE_PATH
)
assert _PROBE_SPEC is not None and _PROBE_SPEC.loader is not None
probe = importlib.util.module_from_spec(_PROBE_SPEC)
sys.modules[_PROBE_SPEC.name] = probe
_PROBE_SPEC.loader.exec_module(probe)

DRIVERS = [
    "00000000-0000-0000-0000-000000000001",
    "00000000-0000-0000-0000-000000000002",
    "00000000-0000-0000-0000-000000000003",
]


def _ranked(case: Any) -> list[tuple[int, str, int, int, int]]:
    rows = sorted(case.expected, key=lambda row: (-row[1], -row[2], -row[3], row[0]))
    return [
        (rank, driver, points, wins, podiums)
        for rank, (driver, points, wins, podiums) in enumerate(rows, start=1)
    ]


@pytest.mark.parametrize(
    ("case_name", "expected"),
    [
        ("points_primary", ((DRIVERS[0], 25, 1, 1), (DRIVERS[1], 18, 0, 1))),
        ("wins_tiebreak", ((DRIVERS[0], 26, 1, 1), (DRIVERS[1], 26, 0, 1))),
        ("podiums_tiebreak", ((DRIVERS[0], 45, 1, 2), (DRIVERS[1], 45, 1, 1))),
        ("unclassified_bonus_ignored", ((DRIVERS[1], 18, 0, 1), (DRIVERS[0], 0, 0, 0))),
        (
            "configured_points_and_bonuses",
            ((DRIVERS[0], 9, 1, 1), (DRIVERS[1], 6, 0, 1), (DRIVERS[2], 0, 0, 1)),
        ),
    ],
)
def test_case_definitions_cover_expected_points_and_tiebreaks(
    case_name: str, expected: tuple[tuple[str, int, int, int], ...]
) -> None:
    cases = {case.name: case for case in probe.standings_cases(DRIVERS)}

    assert cases[case_name].expected == expected
    probe.assert_expected_standings(cases[case_name], _ranked(cases[case_name]))


def test_driver_id_case_uses_configured_points_and_stable_uuid_order() -> None:
    cases = {case.name: case for case in probe.standings_cases(DRIVERS)}
    case = cases["driver_id_tiebreak"]
    low, high = sorted(DRIVERS[:2])

    assert case.configured_points == ((1, 10), (4, 0), (5, 0))
    assert case.expected == ((low, 10, 1, 1), (high, 10, 1, 1))
    probe.assert_expected_standings(case, _ranked(case))


@pytest.mark.parametrize(
    "mutate",
    [
        lambda rows: rows[::-1],
        lambda rows: [(1, rows[0][1], rows[0][2] + 1, *rows[0][3:]), *rows[1:]],
        lambda rows: [(1, rows[0][1], rows[0][2], rows[0][3] + 1, rows[0][4]), *rows[1:]],
        lambda rows: [(1, rows[0][1], rows[0][2], rows[0][3], rows[0][4] + 1), *rows[1:]],
        lambda rows: rows[:-1],
        lambda rows: [*rows, (len(rows) + 1, DRIVERS[2], 0, 0, 0)],
    ],
)
def test_expected_case_assertion_rejects_wrong_rank_or_totals(mutate: Any) -> None:
    case = {item.name: item for item in probe.standings_cases(DRIVERS)}["points_primary"]

    with pytest.raises(probe.ProbeFailure, match="unexpected ranks or totals"):
        probe.assert_expected_standings(case, mutate(_ranked(case)))


def test_case_builder_fails_closed_without_three_seeded_drivers() -> None:
    with pytest.raises(probe.ProbeFailure, match="at least three seeded drivers"):
        probe.standings_cases(DRIVERS[:2])


def test_owned_probe_validates_marker_before_database_adapter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env = {"DATABASE_URL": "sentinel"}
    marker_calls: list[dict[str, str]] = []
    sql_calls: list[str] = []
    context = type("Context", (), {"database_url": "validated-url"})()
    monkeypatch.setattr(
        probe.race_probe,
        "validate_owned_environment",
        lambda value: (marker_calls.append(value), context)[1],
    )
    monkeypatch.setattr(
        probe,
        "run_sql_cases",
        lambda database_url: (sql_calls.append(database_url), {"cases": 6})[1],
    )

    result = probe.run_owned_probe(env)

    assert result == {"cases": 6}
    assert marker_calls == [env]
    assert sql_calls == ["validated-url"]


def test_owned_probe_does_not_connect_when_ownership_validation_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sql_calls: list[str] = []
    monkeypatch.setattr(
        probe.race_probe,
        "validate_owned_environment",
        lambda _env: (_ for _ in ()).throw(probe.ProbeFailure("unowned target")),
    )
    monkeypatch.setattr(probe, "run_sql_cases", lambda url: sql_calls.append(url))

    with pytest.raises(probe.ProbeFailure, match="unowned target"):
        probe.run_owned_probe({})

    assert sql_calls == []


def test_probe_scenarios_use_existing_seeded_driver_ids_as_uuid_values() -> None:
    cases = probe.standings_cases(DRIVERS)

    assert all(UUID(item.driver) for case in cases for session in case.sessions for item in session)
    assert len(cases) == 6
