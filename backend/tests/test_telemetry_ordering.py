"""Database independent characterization for ADR-005 telemetry ordering."""

from contextlib import contextmanager
from uuid import UUID

import pytest
from app import telemetry_repository
from app.telemetry_router import create_telemetry_router
from bson import ObjectId
from fastapi import FastAPI
from fastapi.testclient import TestClient

SESSION = UUID("00000000-0000-0000-0000-000000000001")
DRIVER_A = UUID("00000000-0000-0000-0000-000000000002")
DRIVER_B = UUID("00000000-0000-0000-0000-000000000003")


class FakeCursor:
    def __init__(self, rows):
        self.rows = list(rows)

    def sort(self, key, direction=-1):
        self.rows.sort(key=lambda row: row.get(key), reverse=direction < 0)
        return self

    def limit(self, count):
        self.rows = self.rows[:count]
        return self

    def __iter__(self):
        return iter(self.rows)


class FakeCollection:
    def __init__(self):
        self.documents = []

    def insert_one(self, document):
        inserted_id = ObjectId()
        self.documents.append({**document, "_id": inserted_id})
        return type("InsertResult", (), {"inserted_id": inserted_id})()

    def find(self, query):
        return FakeCursor(
            row for row in self.documents
            if all(row.get(key) == value for key, value in query.items())
        )


class FakeConnection:
    def cursor(self):
        return FakeSQLCursor()


class FakeSQLCursor:
    def __init__(self):
        self.query = ""

    def execute(self, query, params):
        self.query = query

    def fetchone(self):
        if "race_sessions" in self.query:
            return {"state": "ACTIVE"}
        return (1,)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


@contextmanager
def fake_connection():
    yield FakeConnection()


def setup_api(monkeypatch):
    collection = FakeCollection()
    events = []
    monkeypatch.setattr(telemetry_repository, "connection", fake_connection)
    app = FastAPI()
    app.include_router(
        create_telemetry_router(
            current_user=lambda: "user",
            jsonable=lambda value: value,
            mongo_ready=lambda: collection,
            roles=lambda *_roles: lambda: "ADMIN",
            telemetry_ws_payload=lambda document, packet_id: {
                **document, "id": str(packet_id)
            },
            publish=lambda *event: events.append(event),
        )
    )
    return TestClient(app), collection, events


def packet(driver=DRIVER_A, lap=1, sector=1, elapsed=1000, speed=200):
    return {
        "session_id": str(SESSION), "driver_id": str(driver),
        "ts": "2026-10-23T12:00:00Z", "lap": lap, "sector": sector,
        "elapsed_ms": elapsed, "speed_kph": speed, "throttle_pct": 80,
        "brake_pct": 0, "tire_compound": "MEDIUM", "tire_age_laps": 1,
        "tire_wear_pct": 2, "tire_temp_c": [80], "pit_state": "TRACK",
    }


def test_first_packet_is_accepted(monkeypatch):
    client, collection, events = setup_api(monkeypatch)
    response = client.post("/api/telemetry/ingest", json=packet())
    assert response.status_code == 202
    assert response.json()["accepted"] is True
    assert len(collection.documents) == len(events) == 1


def test_exact_retry_returns_original_response_without_insert_or_publish(monkeypatch):
    client, collection, events = setup_api(monkeypatch)
    body = packet()
    first = client.post("/api/telemetry/ingest", json=body)
    retry = client.post("/api/telemetry/ingest", json=body)
    assert retry.status_code == 202
    assert retry.json() == first.json()
    assert len(collection.documents) == len(events) == 1


@pytest.mark.xfail(strict=True, reason="F-DOM-04: retry of an older persisted packet is rejected")
def test_retry_of_older_persisted_packet_returns_original_without_side_effects(monkeypatch):
    client, collection, events = setup_api(monkeypatch)
    original_body = packet()
    original = client.post("/api/telemetry/ingest", json=original_body)
    advanced = client.post("/api/telemetry/ingest", json=packet(sector=2, elapsed=2000))
    retry = client.post("/api/telemetry/ingest", json=original_body)
    assert original.status_code == advanced.status_code == retry.status_code == 202
    assert retry.json() == original.json()
    assert len(collection.documents) == len(events) == 2


def test_older_and_conflicting_packets_are_rejected_without_side_effects(monkeypatch):
    client, collection, events = setup_api(monkeypatch)
    assert client.post("/api/telemetry/ingest", json=packet()).status_code == 202
    older = client.post("/api/telemetry/ingest", json=packet(lap=0, elapsed=900))
    conflict = client.post("/api/telemetry/ingest", json=packet(speed=201))
    assert older.status_code == conflict.status_code == 409
    assert "out of order" in older.json()["detail"].lower()
    assert len(collection.documents) == len(events) == 1


def test_driver_streams_advance_independently_and_publish_once_per_new_packet(monkeypatch):
    client, collection, events = setup_api(monkeypatch)
    assert client.post("/api/telemetry/ingest", json=packet()).status_code == 202
    assert client.post(
        "/api/telemetry/ingest", json=packet(DRIVER_B, lap=0, elapsed=50)
    ).status_code == 202
    assert client.post(
        "/api/telemetry/ingest", json=packet(DRIVER_B, lap=0, elapsed=40)
    ).status_code == 409
    assert len(collection.documents) == len(events) == 2
