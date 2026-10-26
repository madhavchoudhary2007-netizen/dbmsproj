from __future__ import annotations

import asyncio
import logging
import sys
from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID

from fastapi import HTTPException
from pymongo.collection import Collection

from ..core.serialization import jsonable
from ..core.simulation_tick import advance_simulation_tick
from ..core.validation import _require_crud_record
from ..database import connection, fetch_all, fetch_one
from ..demo_race_repository import create_demo_race_records, get_demo_race_row
from ..demo_runtime import build_demo_race
from ..pit_repository import create_automatic_reservation
from ..pit_strategy_service import tire_stint_target
from ..runtime_lease import check_runtime_lease
from ..schemas_simulation import SimulationControl
from ..session_measurements import clear_measurements, ensure_reset_allowed
from ..simulation_core import MAX_SESSION_LAPS, Simulation
from ..simulation_finish import finalize_results
from ..simulation_incidents import record_generated_incidents
from ..simulation_lifecycle import sync_lifecycle
from ..simulation_persist import persist_tick
from ..simulation_pit import (
    cancel_automatic_reservations,
    refresh_pit_state,
    schedule_pit_stops,
)
from ..simulation_reset import reset_simulation
from ..simulation_restore import (
    restore_incident_state,
    restore_or_create_demo,
    restore_telemetry_state,
)
from ..simulation_runner import run_simulation_loop
from ..simulation_start import start_simulation

log = logging.getLogger("apexgrid")

_existing_sims: dict[str, Simulation] | None = None
for _mod_name in (
    "backend.app.core.simulation_service",
    "app.core.simulation_service",
    "backend.app.main",
    "app.main",
):
    _mod = sys.modules.get(_mod_name)
    _mod_sims = getattr(_mod, "simulations", None) if _mod is not None else None
    if isinstance(_mod_sims, dict):
        _existing_sims = cast(dict[str, Simulation], _mod_sims)
        break

simulations: dict[str, Simulation] = _existing_sims if _existing_sims is not None else {}


def _iter_main_modules() -> list[Any]:
    mods: list[Any] = []
    for mod_name in ("app.main", "backend.app.main"):
        mod = sys.modules.get(mod_name)
        if mod is not None and mod not in mods:
            mods.append(mod)
    return mods


def _resolve_main_attr[T](name: str, fallback: T) -> T:
    for mod in _iter_main_modules():
        val = getattr(mod, name, None)
        if val is not None and val is not fallback:
            return cast(T, val)
    for mod in _iter_main_modules():
        val = getattr(mod, name, None)
        if val is not None:
            return cast(T, val)
    return fallback


def _get_mongo_ready() -> Collection[dict[str, Any]]:
    for mod in _iter_main_modules():
        fn = getattr(mod, "mongo_ready", None)
        if fn is not None:
            default_fn = getattr(mod, "_default_mongo_ready", None)
            if default_fn is not None and fn is not default_fn and callable(fn):
                res = fn()
                if res is not None:
                    return cast(Collection[dict[str, Any]], res)
    for mod in _iter_main_modules():
        fn = getattr(mod, "mongo_ready", None)
        if callable(fn):
            res = fn()
            if res is not None:
                return cast(Collection[dict[str, Any]], res)
    raise HTTPException(503, "MongoDB telemetry store is unavailable")


def _publish_event(session_id: UUID | str, kind: str, data: Any) -> None:
    for mod in _iter_main_modules():
        pub_fn = getattr(mod, "publish", None)
        if pub_fn is not None:
            default_fn = getattr(mod, "_default_publish", None)
            if default_fn is not None and pub_fn is not default_fn and callable(pub_fn):
                pub_fn(session_id, kind, data)
                return
    for mod in _iter_main_modules():
        pub_fn = getattr(mod, "publish", None)
        if callable(pub_fn):
            pub_fn(session_id, kind, data)
            return
    for mod in _iter_main_modules():
        bus = getattr(mod, "bus", None)
        if bus is not None and hasattr(bus, "send"):
            bus.send(
                session_id,
                {
                    "type": kind,
                    "ts": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                    "session_id": str(session_id),
                    "data": jsonable(data),
                },
            )
            return


def demo_race_row(session_id: UUID | str) -> dict[str, Any] | None:
    get_row_fn = _resolve_main_attr("get_demo_race_row", get_demo_race_row)
    row = get_row_fn(session_id)
    if not row:
        return None
    jsonable_fn = _resolve_main_attr("jsonable", jsonable)
    result: dict[str, Any] = jsonable_fn(row)
    sims = _resolve_main_attr("simulations", simulations)
    sim = sims.get(str(session_id))
    result["simulation_state"] = sim.status if sim else "stopped"
    return result


_default_demo_race_row = demo_race_row


def _make_demo_race(cars: int | None = None, auto_repeat: bool = False) -> dict[str, Any] | None:
    create_records_fn = _resolve_main_attr("create_demo_race_records", create_demo_race_records)
    sims = _resolve_main_attr("simulations", simulations)
    row_fn = _resolve_main_attr("demo_race_row", demo_race_row)
    result: dict[str, Any] | None = build_demo_race(
        cars,
        auto_repeat,
        _get_mongo_ready,
        create_records_fn,
        sims,
        row_fn,
    )
    return result


def launch_demo_simulation(session_id: UUID | str) -> None:
    sims = _resolve_main_attr("simulations", simulations)
    sim = sims[str(session_id)]
    sim.status = "running"
    loop_fn = _resolve_main_attr("simulation_loop", simulation_loop)
    sim.task = asyncio.create_task(loop_fn(sim))


def restore_simulation_from_telemetry(sim: Simulation) -> None:
    return restore_telemetry_state(sim, lambda: _get_mongo_ready())


def restore_simulated_incidents(sim: Simulation) -> None:
    fetch_all_fn = _resolve_main_attr("fetch_all", fetch_all)
    return restore_incident_state(sim, lambda *a, **kw: fetch_all_fn(*a, **kw))


async def resume_or_create_auto_demo_race(create_if_missing: bool = True) -> None:
    logger = _resolve_main_attr("log", log)
    sims = _resolve_main_attr("simulations", simulations)
    await restore_or_create_demo(
        create_if_missing,
        lambda *args, **kwargs: _resolve_main_attr("fetch_all", fetch_all)(*args, **kwargs),
        logger,
        lambda sim: _resolve_main_attr(
            "restore_simulation_from_telemetry", restore_simulation_from_telemetry
        )(sim),
        lambda sim: _resolve_main_attr("restore_simulated_incidents", restore_simulated_incidents)(
            sim
        ),
        lambda *args, **kwargs: _resolve_main_attr(
            "launch_demo_simulation", launch_demo_simulation
        )(*args, **kwargs),
        lambda *args, **kwargs: _resolve_main_attr("_make_demo_race", _make_demo_race)(
            *args, **kwargs
        ),
        sims,
    )


def sync_simulation_lifecycle(session_id: UUID, action: str) -> None:
    sims = _resolve_main_attr("simulations", simulations)
    sync_lifecycle(session_id, action, sims)


def ensure_session_reset_allowed(session_id: UUID | str) -> None:
    fetch_one_fn = _resolve_main_attr("fetch_one", fetch_one)
    return ensure_reset_allowed(session_id, fetch_one_fn)


def clear_session_measurements(session_id: UUID | str) -> None:
    connection_fn = _resolve_main_attr("connection", connection)
    publish_fn = _resolve_main_attr("publish", _publish_event)
    return clear_measurements(session_id, _get_mongo_ready, connection_fn, publish_fn)


def refresh_simulation_pit_state(sim: Simulation, timestamp: datetime) -> None:
    connection_fn = _resolve_main_attr("connection", connection)
    publish_fn = _resolve_main_attr("publish", _publish_event)
    refresh_pit_state(sim, timestamp, connection_fn, publish_fn, tire_stint_target)


def schedule_simulation_pit_stops(sim: Simulation, packets: list[dict[str, Any]]) -> None:
    publish_fn = _resolve_main_attr("publish", _publish_event)
    logger = _resolve_main_attr("log", log)
    return schedule_pit_stops(
        sim, packets, tire_stint_target, create_automatic_reservation, publish_fn, logger
    )


def record_simulated_incidents(sim: Simulation, packets: list[dict[str, Any]]) -> None:
    connection_fn = _resolve_main_attr("connection", connection)
    publish_fn = _resolve_main_attr("publish", _publish_event)
    return record_generated_incidents(sim, packets, connection_fn, publish_fn)


def cancel_automatic_pit_reservations(session_id: UUID | str) -> None:
    connection_fn = _resolve_main_attr("connection", connection)
    publish_fn = _resolve_main_attr("publish", _publish_event)
    return cancel_automatic_reservations(session_id, connection_fn, publish_fn)


def _simulation_lease_is_valid(sim: Simulation) -> bool:
    app_obj: Any = None
    for mod in _iter_main_modules():
        app_candidate = getattr(mod, "app", None)
        if app_candidate is not None:
            if (
                hasattr(app_candidate, "state")
                and getattr(app_candidate.state, "runtime_lease", None) is not None
            ):
                app_obj = app_candidate
                break
            if app_obj is None:
                app_obj = app_candidate
    runtime_lease = getattr(app_obj.state, "runtime_lease", None) if app_obj is not None else None
    if runtime_lease is None:
        return True
    try:
        check_runtime_lease(runtime_lease)
    except RuntimeError as error:
        sim.status = "error"
        logger = _resolve_main_attr("log", log)
        logger.error("Simulation stopped after PostgreSQL runtime ownership loss: %s", error)
        return False
    return True


async def _finalize_simulation_results(
    sim: Simulation,
    ordered: list[dict[str, Any]],
    best_laps: dict[str, int],
    pole_driver_id: str | None,
    fastest_driver_id: str | None,
    championship_id: UUID,
) -> None:
    connection_fn = _resolve_main_attr("connection", connection)
    publish_fn = _resolve_main_attr("publish", _publish_event)
    cancel_pit_fn = _resolve_main_attr(
        "cancel_automatic_pit_reservations", cancel_automatic_pit_reservations
    )
    make_demo_fn = _resolve_main_attr("_make_demo_race", _make_demo_race)
    launch_demo_fn = _resolve_main_attr("launch_demo_simulation", launch_demo_simulation)
    sims = _resolve_main_attr("simulations", simulations)

    await finalize_results(
        sim,
        ordered,
        best_laps,
        pole_driver_id,
        fastest_driver_id,
        championship_id,
        connection_fn,
        publish_fn,
        cancel_pit_fn,
        make_demo_fn,
        launch_demo_fn,
        sims,
    )


def _persist_simulation_tick(
    col: Collection[dict[str, Any]],
    sim: Simulation,
    packets: list[dict[str, Any]],
    timing: dict[str, Any],
) -> None:
    publish_fn = _resolve_main_attr("publish", _publish_event)
    schedule_stops_fn = _resolve_main_attr(
        "schedule_simulation_pit_stops", schedule_simulation_pit_stops
    )
    record_incidents_fn = _resolve_main_attr(
        "record_simulated_incidents", record_simulated_incidents
    )
    persist_tick(
        col,
        sim,
        packets,
        timing,
        publish_fn,
        schedule_stops_fn,
        record_incidents_fn,
    )


simulation_tick_work = _persist_simulation_tick


async def simulation_loop(sim: Simulation) -> None:
    logger = _resolve_main_attr("log", log)
    await run_simulation_loop(
        sim,
        _simulation_lease_is_valid=lambda *args, **kwargs: _resolve_main_attr(
            "_simulation_lease_is_valid", _simulation_lease_is_valid
        )(*args, **kwargs),
        mongo_ready=lambda *args, **kwargs: _resolve_main_attr("mongo_ready", _get_mongo_ready)(
            *args, **kwargs
        ),
        fetch_one=lambda *args, **kwargs: _resolve_main_attr("fetch_one", fetch_one)(
            *args, **kwargs
        ),
        refresh_simulation_pit_state=lambda *args, **kwargs: _resolve_main_attr(
            "refresh_simulation_pit_state", refresh_simulation_pit_state
        )(*args, **kwargs),
        advance_simulation_tick=lambda *args, **kwargs: _resolve_main_attr(
            "advance_simulation_tick", advance_simulation_tick
        )(*args, **kwargs),
        _persist_simulation_tick=lambda *args, **kwargs: _resolve_main_attr(
            "_persist_simulation_tick", _persist_simulation_tick
        )(*args, **kwargs),
        _finalize_simulation_results=lambda *args, **kwargs: _resolve_main_attr(
            "_finalize_simulation_results", _finalize_simulation_results
        )(*args, **kwargs),
        log=logger,
        MAX_SESSION_LAPS=MAX_SESSION_LAPS,
        datetime=datetime,
        UTC=UTC,
    )


async def _start_session_simulation(
    session_id: UUID, body: SimulationControl, sim: Simulation | None
) -> Simulation:
    fetch_one_fn = _resolve_main_attr("fetch_one", fetch_one)
    clear_measurements_fn = _resolve_main_attr(
        "clear_session_measurements", clear_session_measurements
    )
    fetch_all_fn = _resolve_main_attr("fetch_all", fetch_all)
    restore_incidents_fn = _resolve_main_attr(
        "restore_simulated_incidents", restore_simulated_incidents
    )
    sims = _resolve_main_attr("simulations", simulations)
    sim_loop_fn = _resolve_main_attr("simulation_loop", simulation_loop)

    return await start_simulation(
        session_id,
        body,
        sim,
        _require_crud_record,
        fetch_one_fn,
        clear_measurements_fn,
        fetch_all_fn,
        restore_incidents_fn,
        sims,
        sim_loop_fn,
    )


async def _reset_session_simulation(
    session_id: UUID, body: SimulationControl, sim: Simulation | None
) -> Simulation:
    fetch_one_fn = _resolve_main_attr("fetch_one", fetch_one)
    ensure_reset_fn = _resolve_main_attr(
        "ensure_session_reset_allowed", ensure_session_reset_allowed
    )
    sync_lifecycle_fn = _resolve_main_attr("sync_simulation_lifecycle", sync_simulation_lifecycle)
    clear_measurements_fn = _resolve_main_attr(
        "clear_session_measurements", clear_session_measurements
    )
    sims = _resolve_main_attr("simulations", simulations)

    return await reset_simulation(
        session_id,
        body,
        sim,
        fetch_one_fn,
        ensure_reset_fn,
        sync_lifecycle_fn,
        clear_measurements_fn,
        sims,
    )
