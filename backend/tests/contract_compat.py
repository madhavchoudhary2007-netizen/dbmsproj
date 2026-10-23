HTTP_METHODS = {"get", "put", "post", "delete", "options", "head", "patch", "trace"}


def _resolve(schema, document):
    seen = set()
    while "$ref" in schema:
        ref = schema["$ref"]
        if ref in seen:
            raise AssertionError(f"circular schema reference: {ref}")
        seen.add(ref)
        if not ref.startswith("#/components/schemas/"):
            raise AssertionError(f"unsupported schema reference: {ref}")
        name = ref.rsplit("/", 1)[1].replace("~1", "/").replace("~0", "~")
        schema = document["components"]["schemas"][name]
    return schema


def _check_union(old, new, old_doc, new_doc, seen, keyword):
    if keyword not in new:
        raise AssertionError(f"schema {keyword} branches were removed")
    for old_branch in old[keyword]:
        failure = None
        for new_branch in new[keyword]:
            try:
                _schema_compatible(old_branch, new_branch, old_doc, new_doc, set(seen))
                break
            except AssertionError as error:
                failure = error
        else:
            if failure:
                raise failure
            raise AssertionError(f"schema {keyword} branches were removed")


def _check_enum(old, new):
    if "enum" in old and "enum" in new and not set(old["enum"]) <= set(new["enum"]):
        raise AssertionError("schema enum values were removed")


def _schema_compatible(old, new, old_doc, new_doc, seen):
    old = _resolve(old, old_doc)
    new = _resolve(new, new_doc)
    pair = (id(old), id(new))
    if pair in seen:
        return
    seen.add(pair)
    if "type" in old and old["type"] != new.get("type"):
        raise AssertionError(f"schema type changed: {old['type']} -> {new.get('type')}")
    if not set(old.get("required", ())) <= set(new.get("required", ())):
        raise AssertionError("schema required fields were removed")
    new_properties = new.get("properties", {})
    for name, old_property in old.get("properties", {}).items():
        if name not in new_properties:
            raise AssertionError(f"schema property was removed: {name}")
        _schema_compatible(old_property, new_properties[name], old_doc, new_doc, seen)
    if "items" in old:
        if "items" not in new:
            raise AssertionError("schema items were removed")
        _schema_compatible(old["items"], new["items"], old_doc, new_doc, seen)
    _check_enum(old, new)
    for keyword in ("anyOf", "oneOf", "allOf"):
        if keyword in old:
            _check_union(old, new, old_doc, new_doc, seen, keyword)


def assert_compatible(expected: dict, actual: dict) -> None:
    """Require the old paths, methods, response contracts, and schema fields to remain."""
    for path, old_item in expected.get("paths", {}).items():
        if path not in actual.get("paths", {}):
            raise AssertionError(f"path was removed: {path}")
        new_item = actual["paths"][path]
        for method, old_operation in old_item.items():
            if method not in HTTP_METHODS:
                continue
            if method not in new_item:
                raise AssertionError(f"method was removed: {method.upper()} {path}")
            new_operation = new_item[method]
            new_responses = new_operation.get("responses", {})
            for status, old_response in old_operation.get("responses", {}).items():
                if status not in new_responses:
                    raise AssertionError(f"response was removed: {method.upper()} {path} {status}")
                new_content = new_responses[status].get("content", {})
                for media, old_media in old_response.get("content", {}).items():
                    if media not in new_content:
                        raise AssertionError(f"response media type was removed: {media}")
                    old_schema = old_media.get("schema", {})
                    new_schema = new_content[media].get("schema", {})
                    _schema_compatible(old_schema, new_schema, expected, actual, set())
