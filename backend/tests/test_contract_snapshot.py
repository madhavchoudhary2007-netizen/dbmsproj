import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.tests.contract_compat import assert_compatible

SNAPSHOT = Path(__file__).parent / "snapshots" / "openapi.json"


def _document(schema=None):
    response_schema = schema if schema is not None else {}
    return {
        "openapi": "3.0.0",
        "paths": {
            "/items": {
                "get": {
                    "responses": {
                        "200": {"content": {"application/json": {"schema": response_schema}}}
                    }
                }
            }
        },
    }


def test_current_openapi_matches_captured_snapshot():
    from backend.app.main import app

    assert_compatible(json.loads(SNAPSHOT.read_text()), app.openapi())


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        (_document(), {"openapi": "3.0.0", "paths": {}}, "path was removed"),
        (_document(), {"openapi": "3.0.0", "paths": {"/items": {}}}, "method was removed"),
        (
            _document(),
            {"openapi": "3.0.0", "paths": {"/items": {"get": {"responses": {}}}}},
            "response was removed",
        ),
        (
            _document(),
            {
                "openapi": "3.0.0",
                "paths": {"/items": {"get": {"responses": {"200": {"content": {}}}}}},
            },
            "response media type was removed",
        ),
        (
            _document({"type": "object", "properties": {"id": {"type": "string"}}}),
            _document({"type": "object", "properties": {}}),
            "schema property was removed",
        ),
        (
            _document(
                {"type": "object", "required": ["id"], "properties": {"id": {"type": "string"}}}
            ),
            _document({"type": "object", "required": [], "properties": {"id": {"type": "string"}}}),
            "schema required fields were removed",
        ),
    ],
)
def test_breaking_contract_changes_fail(old, new, message):
    with pytest.raises(AssertionError, match=message):
        assert_compatible(old, new)


def test_additive_paths_and_properties_pass():
    old = _document({"type": "object", "properties": {"id": {"type": "string"}}})
    new = _document(
        {"type": "object", "properties": {"id": {"type": "string"}, "name": {"type": "string"}}}
    )
    new["paths"]["/extra"] = {"post": {"responses": {"201": {}}}}
    assert_compatible(old, new)


def test_untyped_old_response_accepts_typed_addition():
    assert_compatible(
        _document(), _document({"type": "object", "properties": {"id": {"type": "string"}}})
    )
