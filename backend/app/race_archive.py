"""Backfill missing explicitly labeled local historical demonstration laps."""

import random
from datetime import timedelta


def seed_historical_laps(conn, collection):
    sessions = conn.execute("""SELECT s.* FROM race_sessions s JOIN race_events e ON e.id=s.event_id
      JOIN championships c ON c.id=e.championship_id WHERE c.name='ApexGrid World Series'
      AND c.season=2026 AND e.round_number<=2 AND s.session_type='RACE' AND s.state='COMPLETED'
      AND s.scheduled_at=e.start_date AND s.started_at=s.scheduled_at+interval '1 hour'
      AND s.ended_at=s.scheduled_at+interval '2 hours'""").fetchall()
    for session in sessions:
        sid = str(session["id"])
        # A partially recorded session must not suppress the rest of its archive.
        # Preserve existing telemetry and fill only missing driver/lap pairs.
        existing_laps = set()
        recorded_lap_times = {}
        for doc in collection.find(
            {"session_id": sid}, {"driver_id": 1, "lap": 1, "sector": 1, "lap_time_ms": 1}
        ):
            if doc.get("driver_id") is None or doc.get("lap") is None:
                continue
            if doc.get("sector") == 3 and doc.get("lap_time_ms"):
                key = (str(doc["driver_id"]), int(doc["lap"]))
                existing_laps.add(key)
                # Multiple telemetry packets can report a completed lap; use one time.
                recorded_lap_times.setdefault(key, int(doc["lap_time_ms"]))
        results = conn.execute(
            "SELECT driver_id,position,lap_time_ms FROM session_results "
            "WHERE session_id=%s AND classified ORDER BY position",
            (session["id"],),
        ).fetchall()
        docs = []
        for result in results:
            rng = random.Random(sid + str(result["driver_id"]))  # noqa: S311 - deterministic race simulation, not security-sensitive.
            elapsed = 0
            for lap in range(1, session["total_laps"] + 1):
                # Stable pace spread keeps cumulative finishing order
                # consistent with SQL classification.
                lap_ms = 85000 + result["position"] * 140 + rng.randint(-45, 45) + lap * 3
                if lap == session["total_laps"]:
                    lap_ms = result["lap_time_ms"] or lap_ms
                key = (str(result["driver_id"]), lap)
                lap_ms = recorded_lap_times.get(key, lap_ms)
                elapsed += lap_ms
                if key in existing_laps:
                    continue
                split = [int(lap_ms * 0.33), int(lap_ms * 0.35)]
                split.append(lap_ms - sum(split))
                docs.append(
                    {
                        "session_id": sid,
                        "driver_id": str(result["driver_id"]),
                        "ts": session["started_at"] + timedelta(milliseconds=elapsed),
                        "lap": lap,
                        "sector": 3,
                        "elapsed_ms": elapsed,
                        "lap_time_ms": lap_ms,
                        "sector_ms": split,
                        "position": result["position"],
                        "speed_kph": 230,
                        "throttle_pct": 80,
                        "brake_pct": 10,
                        "tire_compound": "MEDIUM",
                        "tire_age_laps": lap,
                        "tire_wear_pct": min(95, lap * 2),
                        "tire_temp_c": [88, 89, 88, 89],
                        "pit_state": "TRACK",
                        "source": "historical_demo",
                    }
                )
        if docs:
            collection.insert_many(docs)
