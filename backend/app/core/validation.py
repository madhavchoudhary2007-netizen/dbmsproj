from typing import Any

from fastapi import HTTPException

from ..simulation_core import MAX_SESSION_LAPS


def limit_offset(limit: int, offset: int) -> tuple[int, int]:
    return min(limit, 200), max(offset, 0)


def validate_session_laps(table: str, values: dict[str, Any]) -> None:
    if table != "race_sessions" or "total_laps" not in values or values["total_laps"] is None:
        return
    value = values["total_laps"]
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= MAX_SESSION_LAPS:
        raise HTTPException(422, f"total_laps must be an integer between 0 and {MAX_SESSION_LAPS}")


def _crud_write_payload(payload: dict[str, Any], cols: tuple[str, ...]) -> dict[str, Any]:
    clean = {k: v for k, v in payload.items() if k in cols and k != "id"}
    if not clean:
        raise HTTPException(422, "At least one writable field is required")
    return clean


def _require_crud_record(record: Any, detail: str) -> Any:
    if not record:
        raise HTTPException(404, detail)
    return record
