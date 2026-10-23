import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.tests.contract_compat import assert_compatible
from backend.tests.test_contract_snapshot import _document


def _ref(name):
    return {"$ref": f"#/components/schemas/{name}"}


def _docs(old_schema, new_schema, old_defs=None, new_defs=None):
    old = _document(old_schema)
    new = _document(new_schema)
    old["components"] = {"schemas": old_defs or {}}
    new["components"] = {"schemas": new_defs or {}}
    return old, new


@pytest.mark.parametrize(
    ("old_branch", "new_branch", "old_defs", "new_defs", "message"),
    [
        (
            _ref("Payload"),
            _ref("Payload"),
            {
                "Payload": {
                    "type": "object",
                    "required": ["id"],
                    "properties": {"id": {"type": "string"}},
                }
            },
            {
                "Payload": {
                    "type": "object",
                    "required": [],
                    "properties": {"id": {"type": "string"}},
                }
            },
            "required fields were removed",
        ),
        (
            {
                "type": "object",
                "properties": {
                    "nested": {"type": "object", "properties": {"id": {"type": "string"}}}
                },
            },
            {"type": "object", "properties": {"nested": {"type": "object", "properties": {}}}},
            None,
            None,
            "property was removed",
        ),
        (
            {"type": "string"},
            {"type": "integer"},
            None,
            None,
            "schema type changed",
        ),
        (
            {"type": "string", "enum": ["a", "b"]},
            {"type": "string", "enum": ["a"]},
            None,
            None,
            "enum values were removed",
        ),
    ],
)
def test_union_ref_branch_contract_removals_fail(
    old_branch, new_branch, old_defs, new_defs, message
):
    old, new = _docs({"oneOf": [old_branch]}, {"oneOf": [new_branch]}, old_defs, new_defs)
    with pytest.raises(AssertionError, match=message):
        assert_compatible(old, new)


def test_union_additive_branch_and_ref_rename_equivalence_pass():
    old, new = _docs(
        {"anyOf": [_ref("OldName")]},
        {"anyOf": [{"type": "object", "properties": {"id": {"type": "string"}}}, {"type": "null"}]},
        {"OldName": {"type": "object", "properties": {"id": {"type": "string"}}}},
    )
    assert_compatible(old, new)


def test_allof_preserves_each_old_branch():
    old, new = _docs(
        {"allOf": [{"type": "object", "properties": {"id": {"type": "string"}}}]},
        {
            "allOf": [
                {
                    "type": "object",
                    "properties": {"id": {"type": "string"}, "name": {"type": "string"}},
                }
            ]
        },
    )
    assert_compatible(old, new)


def test_circular_refs_terminate_with_assertion():
    old, new = _docs(_ref("Node"), _ref("Node"), {"Node": _ref("Node")}, {"Node": _ref("Node")})
    with pytest.raises(AssertionError, match="circular schema reference"):
        assert_compatible(old, new)
