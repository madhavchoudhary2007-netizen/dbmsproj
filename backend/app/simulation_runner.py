from __future__ import annotations

import asyncio
import logging
import sys
from collections.abc import Callable
from datetime import UTC as UTC
from datetime import datetime as datetime
from datetime import tzinfo
from typing import Any, cast

from pymongo.errors import PyMongoError

from .core import legacy_compat as _legacy_compat
from .core import lifespan as _lifespan
from .simulation_core import Simulation

# Register legacy symbols so main_module.open_pool does not raise AttributeError
_legacy_compat._SYMBOL_MAP.setdefault("open_pool", "app.database")
_legacy_compat._SYMBOL_MAP.setdefault("close_pool", "app.database")

_lifespan_any: Any = _lifespan
_orig_acquire_lease = getattr(_lifespan_any, "acquire_runtime_lease", None)
_orig_open_pool = getattr(_lifespan_any, "open_pool", None)
_orig_close_pool = getattr(_lifespan_any, "close_pool", None)
_orig_get_pool = getattr(_lifespan_any, "get_pool", None)
_orig_mongo_client = getattr(_lifespan_any, "MongoClient", None)


def _is_default_symbol(val: Any) -> bool:
    mod = getattr(val, "__module__", "")
    return mod in ("app.database", "backend.app.database")


def _make_compat_resolver(target_mod: Any, orig_resolve: Any) -> Any:
    def _compat_resolve_main_attr(name: str, fallback: Any) -> Any:
        iter_fn: Callable[[], list[Any]] = getattr(target_mod, "_iter_main_modules", list)
        for m in reversed(iter_fn()):
            val = getattr(m, name, None)
            if val is not None and val is not fallback and not _is_default_symbol(val):
                return val
        for m in iter_fn():
            val = getattr(m, name, None)
            if val is not None and val is not fallback and not _is_default_symbol(val):
                return val
        return orig_resolve(name, fallback)

    return _compat_resolve_main_attr


def _patch_simulation_service() -> None:
    for mod_name in ("backend.app.core.simulation_service", "app.core.simulation_service"):
        mod: Any = sys.modules.get(mod_name)
        if mod is not None and hasattr(mod, "_resolve_main_attr"):
            if getattr(mod, "_is_patched", False):
                continue
            mod._is_patched = True
            mod._resolve_main_attr = _make_compat_resolver(mod, mod._resolve_main_attr)


_orig_resolve_symbol = _legacy_compat.resolve_legacy_symbol


def _compat_resolve_symbol(name: str, module_name: str = "") -> Any:
    _patch_simulation_service()
    return _orig_resolve_symbol(name, module_name)


_legacy_compat.resolve_legacy_symbol = _compat_resolve_symbol


def _compat_acquire_lease() -> Any:
    _patch_simulation_service()
    for mod_name in ("backend.app.main", "app.main"):
        mod = sys.modules.get(mod_name)
        if mod is not None:
            fn = getattr(mod, "acquire_runtime_lease", None)
            if fn is not None and fn is not _compat_acquire_lease and fn is not _orig_acquire_lease:
                return fn()
    return _orig_acquire_lease() if callable(_orig_acquire_lease) else None


def _compat_open_pool() -> Any:
    _patch_simulation_service()
    for mod_name in ("backend.app.main", "app.main"):
        mod = sys.modules.get(mod_name)
        if mod is not None:
            fn = getattr(mod, "open_pool", None)
            if fn is not None and fn is not _compat_open_pool and fn is not _orig_open_pool:
                return fn()
    return _orig_open_pool() if callable(_orig_open_pool) else None


def _compat_close_pool() -> Any:
    _patch_simulation_service()
    for mod_name in ("backend.app.main", "app.main"):
        mod = sys.modules.get(mod_name)
        if mod is not None:
            fn = getattr(mod, "close_pool", None)
            if fn is not None and fn is not _compat_close_pool and fn is not _orig_close_pool:
                return fn()
    return _orig_close_pool() if callable(_orig_close_pool) else None


def _compat_get_pool() -> Any:
    _patch_simulation_service()
    for mod_name in ("backend.app.main", "app.main"):
        mod = sys.modules.get(mod_name)
        if mod is not None:
            fn = getattr(mod, "get_pool", None)
            if fn is not None and fn is not _compat_get_pool and fn is not _orig_get_pool:
                return fn()
    return _orig_get_pool() if callable(_orig_get_pool) else None


def _compat_mongo_client(*args: Any, **kwargs: Any) -> Any:
    _patch_simulation_service()
    for mod_name in ("backend.app.main", "app.main"):
        mod = sys.modules.get(mod_name)
        if mod is not None:
            cls = getattr(mod, "MongoClient", None)
            if (
                cls is not None
                and cls is not _compat_mongo_client
                and cls is not _orig_mongo_client
            ):
                return cls(*args, **kwargs)
    return _orig_mongo_client(*args, **kwargs) if callable(_orig_mongo_client) else None


if _orig_acquire_lease is not None:
    _lifespan_any.acquire_runtime_lease = _compat_acquire_lease
if _orig_open_pool is not None:
    _lifespan_any.open_pool = _compat_open_pool
if _orig_close_pool is not None:
    _lifespan_any.close_pool = _compat_close_pool
if _orig_get_pool is not None:
    _lifespan_any.get_pool = _compat_get_pool
if _orig_mongo_client is not None:
    _lifespan_any.MongoClient = _compat_mongo_client


def _aggregate_best_laps(collection: Any, session_id_str: str) -> dict[str, int]:
    return {
        row["_id"]: row["best_lap_ms"]
        for row in collection.aggregate(
            [
                {
                    "$match": {
                        "session_id": session_id_str,
                        "lap_time_ms": {"$gt": 0},
                    }
                },
                {
                    "$group": {
                        "_id": "$driver_id",
                        "best_lap_ms": {"$min": "$lap_time_ms"},
                    }
                },
            ]
        )
    }


async def _resolve_simulation_session(
    fetch_one: Callable[..., Any], session_id: Any
) -> dict[str, Any] | None:
    query = """SELECT s.state,s.safety_car,e.championship_id
    FROM race_sessions s JOIN race_events e ON e.id=s.event_id WHERE s.id=%s"""
    if asyncio.iscoroutinefunction(fetch_one):
        return cast(dict[str, Any] | None, await fetch_one(query, (session_id,)))
    return cast(dict[str, Any] | None, await asyncio.to_thread(fetch_one, query, (session_id,)))


async def _refresh_pit_assignments(
    refresh_fn: Callable[..., Any], sim: Simulation, timestamp: datetime
) -> dict[str, Any]:
    if asyncio.iscoroutinefunction(refresh_fn):
        return cast(dict[str, Any], await refresh_fn(sim, timestamp))
    return cast(dict[str, Any], await asyncio.to_thread(refresh_fn, sim, timestamp))


async def _persist_tick(
    persist_fn: Callable[..., Any],
    col: Any,
    sim: Simulation,
    packets: list[dict[str, Any]],
    timing: dict[str, Any],
) -> None:
    if asyncio.iscoroutinefunction(persist_fn):
        await persist_fn(col, sim, packets, timing)
    else:
        await asyncio.to_thread(persist_fn, col, sim, packets, timing)


async def _handle_completion_if_finished(
    sim: Simulation,
    packets: list[dict[str, Any]],
    col: Any,
    MAX_SESSION_LAPS: int,
    championship_id: Any,
    finalize_fn: Callable[..., Any],
) -> bool:
    completion_lap = min(sim.total_laps or MAX_SESSION_LAPS, MAX_SESSION_LAPS)
    if not all(p["lap"] == completion_lap and p["sector"] == 3 for p in packets):
        return False
    ordered = sorted(packets, key=lambda p: p["elapsed_ms"])
    best_laps = await asyncio.to_thread(_aggregate_best_laps, col, str(sim.session_id))
    fastest_driver_id = min(best_laps, key=lambda d: best_laps[d]) if best_laps else None
    pole_driver_id = (
        min(sim.pace_offsets_ms, key=lambda d: sim.pace_offsets_ms[d])
        if sim.is_generated and sim.pace_offsets_ms
        else None
    )
    await finalize_fn(sim, ordered, best_laps, pole_driver_id, fastest_driver_id, championship_id)
    return True


async def run_simulation_loop(
    sim: Simulation,
    *,
    _simulation_lease_is_valid: Callable[..., Any],
    mongo_ready: Callable[..., Any],
    fetch_one: Callable[..., Any],
    refresh_simulation_pit_state: Callable[..., Any],
    advance_simulation_tick: Callable[..., Any],
    _persist_simulation_tick: Callable[..., Any],
    _finalize_simulation_results: Callable[..., Any],
    log: logging.Logger,
    MAX_SESSION_LAPS: int,
    datetime: type[datetime],
    UTC: tzinfo,
) -> None:
    _patch_simulation_service()
    if not _simulation_lease_is_valid(sim):
        return
    col = mongo_ready()
    while sim.status in {"running", "paused"}:
        if not _simulation_lease_is_valid(sim):
            return
        if sim.status == "paused":
            await asyncio.sleep(0.05)
            continue
        try:
            session = await _resolve_simulation_session(fetch_one, sim.session_id)
            if not session or session["state"] != "ACTIVE":
                if session and session["state"] == "PAUSED":
                    sim.status = "paused"
                    continue
                sim.status = "error" if not session else "stopped"
                return
            timestamp = datetime.now(UTC)
            pit_assignments = await _refresh_pit_assignments(
                refresh_simulation_pit_state, sim, timestamp
            )
            packets, timing = advance_simulation_tick(
                sim, timestamp, safety_car=session["safety_car"], pit_assignments=pit_assignments
            )
            await _persist_tick(_persist_simulation_tick, col, sim, packets, timing)
            finished = await _handle_completion_if_finished(
                sim,
                packets,
                col,
                MAX_SESSION_LAPS,
                session["championship_id"],
                _finalize_simulation_results,
            )
            if finished:
                return
        except PyMongoError:
            sim.status = "error"
            log.exception("Telemetry simulator could not write packet")
            return
        except Exception:
            sim.status = "error"
            log.exception("Telemetry simulator could not advance state")
            return
        await asyncio.sleep(1 / sim.rate_hz)
