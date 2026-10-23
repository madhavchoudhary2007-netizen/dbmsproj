import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.tests.contract_fixture import capture_contracts

SNAPSHOT = Path(__file__).parent / "snapshots" / "get-responses.json"
EXPECTED = json.loads(SNAPSHOT.read_text())


def _assert_golden(expected, actual):
    assert type(expected) is type(actual)
    if isinstance(expected, dict):
        assert expected.keys() <= actual.keys()
        for key, value in expected.items():
            _assert_golden(value, actual[key])
    elif isinstance(expected, list):
        assert len(expected) == len(actual)
        for old_value, new_value in zip(expected, actual, strict=True):
            _assert_golden(old_value, new_value)
    else:
        assert expected == actual


@pytest.fixture(scope="module")
def actual_responses():
    return capture_contracts()


@pytest.mark.parametrize("path", sorted(EXPECTED))
def test_get_response_matches_golden(path, actual_responses):
    assert path in actual_responses
    _assert_golden(EXPECTED[path], actual_responses[path])


def test_comparison_allows_additive_object_keys():
    _assert_golden({"retained": {"id": 1}}, {"retained": {"id": 1, "added": True}})


@pytest.mark.parametrize(
    ("expected", "actual"),
    [
        ({"retained": 1, "removed": 2}, {"retained": 1}),
        ({"value": 1}, {"value": 2}),
        ({"value": 1}, {"value": True}),
    ],
)
def test_comparison_rejects_removed_or_changed_values(expected, actual):
    with pytest.raises(AssertionError):
        _assert_golden(expected, actual)
