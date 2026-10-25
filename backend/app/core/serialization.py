from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID

from bson import ObjectId


def jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            value = value.replace(tzinfo=UTC)
        return value.isoformat().replace("+00:00", "Z")
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, ObjectId):
        return str(value)
    return value


def telemetry_ws_payload(packet: dict[str, Any], inserted_id: ObjectId | str) -> dict[str, Any]:
    """Build a JSON-safe telemetry packet without leaking Mongo's `_id`."""
    payload = {key: value for key, value in packet.items() if key != "_id"}
    payload["id"] = str(inserted_id)
    return cast(dict[str, Any], jsonable(payload))
