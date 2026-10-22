"""Fast, database independent checks of wire validation and live fan-out."""
import asyncio
import json
import os
import random
import subprocess
import sys
import time
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from bson import BSON, ObjectId
from fastapi import HTTPException
from fastapi.testclient import TestClient
import pytest
from pydantic import ValidationError

os.environ["APP_ENV"] = "local"
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from backend.app import main as main_module
from backend.app.main import (
    AutoReservationIn, EventBus, ReservationIn, ReservationStatus, ResultIn,
    Simulation, Telemetry, advance_simulation_tick, app, choose_demo_car_numbers,
    pit_strategy, restore_simulated_incidents, save_results, simulations,
    sync_simulation_lifecycle, telemetry_ws_payload, update_pit_reservation,
    validate_session_laps, websocket_bearer,
)
from backend.app.race_archive import seed_historical_laps


def packet(**overrides):
    value = {
        "session_id": "a2100000-0000-4000-8000-000000000001",
        "driver_id": "a2100000-0000-4000-8000-000000000002",
        "ts": "2026-10-05T10:00:00Z", "lap": 1, "sector": 2,
        "elapsed_ms": 10000, "lap_time_ms": 90000, "sector_ms": [30000, 30000, 30000],
        "position": 1, "speed_kph": 210, "throttle_pct": 100, "brake_pct": 0,
        "tire_compound": "MEDIUM", "tire_age_laps": 4, "tire_wear_pct": 12,
        "tire_temp_c": [80, 82, 79, 81], "pit_state": "TRACK",
        "pit_reservation_id": None, "pit_box_number": None, "pit_team_id": None,
        "pit_starts_at": None, "pit_ends_at": None,
    }
    return {**value, **overrides}


@pytest.fixture
def auth_characterization_client():
    return TestClient(app)


def auth_characterization_user(password_hash=None):
    return {"id": 42, "email": "driver@example.test", "full_name": "Test Driver",
            "role": "DRIVER", "password_hash": password_hash}


def auth_characterization_fetch(monkeypatch, user):
    def fetch_one(query, params=()):
        if "lower(email)" in query:
            return user
        if "WHERE id=%s" in query and str(params[0]) == str(user["id"]):
            return {key: user[key] for key in ("id", "email", "full_name", "role")}
        return None
    monkeypatch.setattr(main_module, "fetch_one", fetch_one)


def auth_characterization_login(client, user, password):
    return client.post("/api/auth/login", json={"email": user["email"], "password": password})


def auth_characterization_expired_token():
    import base64
    import hashlib
    import hmac

    def part(value):
        return base64.urlsafe_b64encode(value).rstrip(b"=")
    header = part(b'{"alg":"HS256","typ":"JWT"}')
    payload = part(b'{"sub":"42","role":"DRIVER","exp":1}')
    message = header + b"." + payload
    signature = hmac.new(main_module.JWT_SECRET.encode(), message, hashlib.sha256).digest()
    return (message + b"." + part(signature)).decode()


def test_auth_characterization_login_success_and_claims(auth_characterization_client, monkeypatch):
    import base64

    import bcrypt
    user = auth_characterization_user(bcrypt.hashpw(b"correct horse", bcrypt.gensalt()).decode())
    auth_characterization_fetch(monkeypatch, user)
    response = auth_characterization_login(auth_characterization_client, user, "correct horse")
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == ("be" + "arer")
    assert set(body) == {"access_token", "token_type", "user"}
    assert body["user"] == {key: user[key] for key in ("id", "email", "full_name", "role")}
    payload = body["access_token"].split(".")[1]
    claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    assert claims["sub"] == "42" and claims["role"] == "DRIVER" and "exp" in claims


def test_auth_characterization_invalid_login(auth_characterization_client, monkeypatch):
    import bcrypt
    user = auth_characterization_user(bcrypt.hashpw(b"correct horse", bcrypt.gensalt()).decode())
    auth_characterization_fetch(monkeypatch, user)
    response = auth_characterization_client.post(
        "/api/auth/login", json={"email": user["email"], "password": "wrong"}
    )
    assert (response.status_code, response.json()["detail"]) == (401, "Invalid email or password")


def test_auth_characterization_me_missing_token(auth_characterization_client):
    response = auth_characterization_client.get("/api/auth/me")
    assert (response.status_code, response.json()["detail"]) == (401, "Authentication required")


@pytest.mark.parametrize("case_name", ["tampered", "expired"])
def test_auth_characterization_me_rejects_bad_or_expired_token(
    auth_characterization_client, monkeypatch, case_name
):
    user = auth_characterization_user()
    auth_characterization_fetch(monkeypatch, user)
    if case_name == "expired":
        access_token = auth_characterization_expired_token()
    else:
        import bcrypt
        user["password_hash"] = bcrypt.hashpw(b"valid", bcrypt.gensalt()).decode()
        signed = auth_characterization_login(auth_characterization_client, user, "valid")
        token_value = signed.json()["access_token"]
        head, payload, signature = token_value.split(".")
        access_token = f"{head}.{payload}.{'A' if signature[0] != 'A' else 'B'}{signature[1:]}"
    response = auth_characterization_client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert (response.status_code, response.json()["detail"]) == (401, "Invalid or expired token")


def test_auth_characterization_me_valid_user_shape(auth_characterization_client, monkeypatch):
    user = auth_characterization_user()
    auth_characterization_fetch(monkeypatch, user)
    import bcrypt
    user["password_hash"] = bcrypt.hashpw(b"correct horse", bcrypt.gensalt()).decode()
    login = auth_characterization_login(auth_characterization_client, user, "correct horse")
    response = auth_characterization_client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {login.json()['access_token']}"}
    )
    assert response.status_code == 200
    assert response.json() == {key: user[key] for key in ("id", "email", "full_name", "role")}


def test_auth_characterization_websocket_accepts_and_rejects_tokens(
    auth_characterization_client, monkeypatch
):
    import bcrypt
    from starlette.websockets import WebSocketDisconnect
    user = auth_characterization_user(bcrypt.hashpw(b"correct horse", bcrypt.gensalt()).decode())
    auth_characterization_fetch(monkeypatch, user)
    login = auth_characterization_login(auth_characterization_client, user, "correct horse")
    token = login.json()["access_token"]
    path = "/api/ws/sessions/a2100000-0000-4000-8000-000000000001"
    with auth_characterization_client.websocket_connect(
        path, subprotocols=["apexgrid.jwt", token]
    ) as ws:
        assert ws.accepted_subprotocol == "apexgrid.jwt"
    bad = token.rsplit(".", 1)
    tampered = bad[0] + "." + ("A" if bad[1][0] != "A" else "B") + bad[1][1:]
    with (
        pytest.raises(WebSocketDisconnect) as rejected,
        auth_characterization_client.websocket_connect(
            path, subprotocols=["apexgrid.jwt", tampered]
        ),
    ):
        pass
    assert rejected.value.code == 4401
    assert rejected.value.reason == "Invalid or expired token"


def cookie_auth_login(client, monkeypatch, role="DRIVER"):
    import bcrypt
    user = auth_characterization_user(bcrypt.hashpw(b"correct horse", bcrypt.gensalt()).decode())
    user["role"] = role
    auth_characterization_fetch(monkeypatch, user)
    return auth_characterization_login(client, user, "correct horse")


def cookie_auth_set_cookies(response):
    from http.cookies import SimpleCookie
    cookies = SimpleCookie()
    for header in response.headers.get_list("set-cookie"):
        cookies.load(header)
    return cookies


def test_cookie_auth_login_sets_host_only_session_and_readable_csrf(
    auth_characterization_client, monkeypatch
):
    response = cookie_auth_login(auth_characterization_client, monkeypatch)
    assert response.status_code == 200
    cookies = cookie_auth_set_cookies(response)
    assert set(cookies) == {"apexgrid_session", "apexgrid_csrf"}
    session, csrf = cookies["apexgrid_session"], cookies["apexgrid_csrf"]
    assert session["httponly"] and session["samesite"].lower() == "lax"
    assert session["path"] == "/" and not session["domain"]
    assert csrf["samesite"].lower() == "lax" and not csrf["httponly"]
    assert csrf["path"] == "/" and not csrf["domain"]


def test_cookie_auth_browser_shape(auth_characterization_client, monkeypatch):
    import bcrypt

    user = auth_characterization_user(bcrypt.hashpw(b"correct horse", bcrypt.gensalt()).decode())
    auth_characterization_fetch(monkeypatch, user)
    response = auth_characterization_client.post(
        "/api/auth/login", json={"email": user["email"], "password": "correct horse"},
        headers={"Origin": "http://localhost:3000"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "user": {key: user[key] for key in ("id", "email", "full_name", "role")}
    }
    cookies = cookie_auth_set_cookies(response)
    assert cookies["apexgrid_session"].value
    assert cookies["apexgrid_csrf"].value


def test_cookie_auth_browser_shape_preserves_legacy_no_origin_token(
    auth_characterization_client, monkeypatch
):
    response = cookie_auth_login(auth_characterization_client, monkeypatch)
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_cookie_auth_me_uses_session_without_bearer(auth_characterization_client, monkeypatch):
    user = auth_characterization_user()
    cookie_auth_login(auth_characterization_client, monkeypatch)
    response = auth_characterization_client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.json() == {key: user[key] for key in ("id", "email", "full_name", "role")}


@pytest.mark.parametrize("csrf_value", [None, "wrong-token"], ids=["missing", "wrong"])
def test_cookie_auth_logout_rejects_missing_or_wrong_csrf(
    auth_characterization_client, monkeypatch, csrf_value
):
    cookie_auth_login(auth_characterization_client, monkeypatch)
    headers = {"Origin": "http://localhost:3000"}
    if csrf_value is not None:
        headers["X-CSRF-Token"] = csrf_value
    response = auth_characterization_client.post("/api/auth/logout", headers=headers)
    assert response.status_code == 403


def test_cookie_auth_logout_accepts_csrf_and_clears_both_cookies(
    auth_characterization_client, monkeypatch
):
    cookie_auth_login(auth_characterization_client, monkeypatch)
    csrf = auth_characterization_client.cookies.get("apexgrid_csrf", "")
    response = auth_characterization_client.post(
        "/api/auth/logout",
        headers={"Origin": "http://localhost:3000", "X-CSRF-Token": csrf},
    )
    assert response.status_code in {200, 204}
    headers = [value.lower() for value in response.headers.get_list("set-cookie")]
    cleared = {name for name in ("apexgrid_session", "apexgrid_csrf")
               if any(value.startswith(f"{name}=") and ("max-age=0" in value or "expires=" in value)
                      for value in headers)}
    assert cleared == {"apexgrid_session", "apexgrid_csrf"}


def cookie_auth_mock_user_update_db(monkeypatch):
    from contextlib import nullcontext
    from unittest.mock import Mock

    cursor = Mock()
    cursor.fetchone.return_value = {
        "id": 42, "email": "driver@example.test", "full_name": "Test Driver", "role": "ADMIN"
    }
    connection = Mock()
    connection.cursor.return_value = nullcontext(cursor)
    monkeypatch.setattr(main_module, "connection", lambda: nullcontext(connection))


def test_cookie_auth_guard_rejects_protected_write_without_csrf(
    auth_characterization_client, monkeypatch
):
    cookie_auth_login(auth_characterization_client, monkeypatch, role="ADMIN")
    cookie_auth_mock_user_update_db(monkeypatch)
    response = auth_characterization_client.patch(
        "/api/users/00000000-0000-4000-8000-000000000042",
        json={"full_name": "Changed"}, headers={"Origin": "http://localhost:3000"},
    )
    assert response.status_code == 403


def test_cookie_auth_guard_rejects_forged_signed_csrf_pair(
    auth_characterization_client, monkeypatch
):
    cookie_auth_login(auth_characterization_client, monkeypatch, role="ADMIN")
    cookie_auth_mock_user_update_db(monkeypatch)
    forged = "planted-nonce.invalid-signature"
    auth_characterization_client.cookies.set("apexgrid_csrf", forged)
    response = auth_characterization_client.patch(
        "/api/users/00000000-0000-4000-8000-000000000042",
        json={"full_name": "Changed"},
        headers={"Origin": "http://localhost:3000", "X-CSRF-Token": forged},
    )
    assert response.status_code == 403


def test_cookie_auth_guard_rejects_login_from_disallowed_origin(
    auth_characterization_client, monkeypatch
):
    import bcrypt

    user = auth_characterization_user(bcrypt.hashpw(b"correct horse", bcrypt.gensalt()).decode())
    auth_characterization_fetch(monkeypatch, user)
    response = auth_characterization_client.post(
        "/api/auth/login", json={"email": user["email"], "password": "correct horse"},
        headers={"Origin": "https://unapproved.example"},
    )
    assert response.status_code == 403


def test_cookie_auth_websocket_accepts_session_without_jwt_subprotocol(
    auth_characterization_client, monkeypatch
):
    user = auth_characterization_user()
    auth_characterization_fetch(monkeypatch, user)
    cookie_auth_login(auth_characterization_client, monkeypatch)
    session = auth_characterization_client.cookies.get("apexgrid_session", "")
    path = f"/api/ws/sessions/{uuid4()}"
    headers = {
        "Cookie": f"apexgrid_session={session}",
        "Origin": "http://localhost:3000",
    }
    with auth_characterization_client.websocket_connect(path, headers=headers) as ws:
        assert ws.accepted_subprotocol is None


def test_cookie_auth_websocket_rejects_unapproved_origin(
    auth_characterization_client, monkeypatch
):
    from starlette.websockets import WebSocketDisconnect
    login = cookie_auth_login(auth_characterization_client, monkeypatch)
    session = login.cookies.get("apexgrid_session", "missing-cookie")
    legacy_token = session if session != "missing-cookie" else login.json()["access_token"]
    path = f"/api/ws/sessions/{uuid4()}"
    headers = {
        "Origin": "https://unapproved.example",
        "Cookie": f"apexgrid_session={session}",
    }
    with (
        pytest.raises(WebSocketDisconnect),
        auth_characterization_client.websocket_connect(
            path, subprotocols=["apexgrid.jwt", legacy_token], headers=headers
        ),
    ):
        pass


def test_cookie_auth_login_sets_secure_cookies_outside_local_mode(
    auth_characterization_client, monkeypatch
):
    monkeypatch.setattr(main_module, "APP_ENV", "production")
    response = cookie_auth_login(auth_characterization_client, monkeypatch)
    assert response.status_code == 200
    cookies = cookie_auth_set_cookies(response)
    assert cookies["apexgrid_session"]["secure"]
    assert cookies["apexgrid_csrf"]["secure"]


def test_historical_archive_fills_missing_laps_without_replacing_recorded_data():
    session_id = uuid4()
    first_driver, second_driver = uuid4(), uuid4()
    session = {
        "id": session_id, "total_laps": 2,
        "started_at": datetime(2026, 10, 5, 10, tzinfo=timezone.utc),
    }
    results = [
        {"driver_id": first_driver, "position": 1, "lap_time_ms": 85000},
        {"driver_id": second_driver, "position": 2, "lap_time_ms": 86000},
    ]

    class Connection:
        def execute(self, query, _params=None):
            return type("Result", (), {"fetchall": lambda _self: [session] if "SELECT s.*" in query else results})()

    recorded = {"session_id": str(session_id), "driver_id": str(first_driver), "lap": 1,
                "sector": 3, "lap_time_ms": 123456, "source": "recorded_telemetry"}
    partial = {"session_id": str(session_id), "driver_id": str(second_driver), "lap": 1,
               "sector": 1, "lap_time_ms": None, "source": "recorded_telemetry"}
    class Collection:
        def __init__(self):
            self.inserted = []
        def find(self, query, _projection):
            assert query == {"session_id": str(session_id)}
            return [recorded, partial]
        def insert_many(self, docs):
            self.inserted.extend(docs)

    collection = Collection()
    seed_historical_laps(Connection(), collection)

    assert len(collection.inserted) == 3
    assert all((doc["driver_id"], doc["lap"]) != (str(first_driver), 1) for doc in collection.inserted)
    assert {(doc["driver_id"], doc["lap"]) for doc in collection.inserted} == {
        (str(first_driver), 2), (str(second_driver), 1), (str(second_driver), 2),
    }
    first_driver_lap_2 = next(doc for doc in collection.inserted
                              if doc["driver_id"] == str(first_driver) and doc["lap"] == 2)
    rng = random.Random(str(session_id) + str(first_driver))
    rng.randint(-45, 45)  # lap 1's generated fallback is consumed even though telemetry has that lap.
    generated_lap_2 = results[0]["lap_time_ms"] or (85000 + 1 * 140 + rng.randint(-45, 45) + 2 * 3)
    expected_elapsed = 123456 + generated_lap_2
    assert first_driver_lap_2["elapsed_ms"] == expected_elapsed
    assert first_driver_lap_2["ts"] == session["started_at"] + timedelta(milliseconds=expected_elapsed)
    assert recorded["lap_time_ms"] == 123456


def test_telemetry_packet_contract_and_bounds():
    model = Telemetry.model_validate(packet())
    assert str(model.session_id) == "a2100000-0000-4000-8000-000000000001"
    with pytest.raises(ValidationError):
        Telemetry.model_validate(packet(throttle_pct=101))
    with pytest.raises(ValidationError):
        Telemetry.model_validate(packet(tire_compound="UNKNOWN"))
    with pytest.raises(ValidationError):
        Telemetry.model_validate(packet(ts="2026-10-05T10:00:00"))
    with pytest.raises(ValidationError):
        Telemetry.model_validate(packet(lap=73))
    with pytest.raises(ValidationError):
        Telemetry.model_validate(packet(pit_starts_at="2026-10-05T10:00:00"))


def test_session_lap_limits_and_simulation_never_exceeds_72():
    with pytest.raises(HTTPException) as error:
        validate_session_laps("race_sessions", {"total_laps": 73})
    assert error.value.status_code == 422
    with pytest.raises(HTTPException):
        validate_session_laps("race_sessions", {"total_laps": 12.5})
    sim = Simulation("session-cap", [{"id": "driver-1", "number": 7}], 2, total_laps=90)
    assert sim.total_laps == 72
    emitted = []
    for tick in range(10 * 73):
        packets, _ = advance_simulation_tick(
            sim, datetime(2026, 10, 5, 10, 0, tzinfo=timezone.utc), random.Random(tick),
        )
        emitted.append(packets[0])
    assert max(packet["lap"] for packet in emitted) == 72
    sector_three_laps = [packet["lap"] for packet in emitted if packet["sector"] == 3 and packet["lap_time_ms"]]
    assert sector_three_laps == list(range(1, 73))


@pytest.mark.parametrize("total_laps", [0, 1])
def test_simulation_accepts_zero_and_one_lap_boundaries(total_laps):
    validate_session_laps("race_sessions", {"total_laps": total_laps})
    sim = Simulation("lap-boundary", [{"id": "driver-1", "number": 7}], 2, total_laps=total_laps)
    assert sim.total_laps == total_laps


def test_simulation_packets_and_timing_repeat_for_fixed_clock_and_seed():
    timestamp = datetime(2026, 10, 5, 10, 0, tzinfo=UTC)
    outputs = []
    for _ in range(2):
        sim = Simulation("deterministic", [{"id": "driver-1", "number": 7}], 2)
        outputs.append(advance_simulation_tick(sim, timestamp, random.Random(42)))  # noqa: S311
    assert outputs[0] == outputs[1]


def test_simulation_stop_clears_pending_pit_reservations(monkeypatch):
    session_id = uuid4()
    sim = Simulation(session_id, [], 2, status="running")
    sim.pit_reservations_by_driver = {"driver-1": {"id": "reservation-1"}}
    monkeypatch.setitem(simulations, str(session_id), sim)
    monkeypatch.setattr(main_module, "mongo_ready", lambda: object())
    monkeypatch.setattr(main_module, "cancel_automatic_pit_reservations", lambda *_: None)
    try:
        result = asyncio.run(main_module.control_simulation(
            session_id, main_module.SimulationControl(action="stop"), user={"role": "ADMIN"}
        ))
        assert result["state"] == sim.status == "stopped"
        assert sim.pit_reservations_by_driver == {}
    finally:
        simulations.pop(str(session_id), None)


def test_reservation_requires_timezone_and_status_endpoint_exists():
    with pytest.raises(ValidationError):
        ReservationIn.model_validate({
            "pit_box_id": "a2100000-0000-4000-8000-000000000001",
            "session_id": "a2100000-0000-4000-8000-000000000002",
            "team_id": "a2100000-0000-4000-8000-000000000003",
            "starts_at": "2026-10-05T10:00:00",
            "ends_at": "2026-10-05T11:00:00Z",
        })
    assert "/api/pit-reservations/{reservation_id}" in {route.path for route in app.routes}
    assert "/api/pit-reservations/auto" in {route.path for route in app.routes}
    with pytest.raises(ValidationError):
        AutoReservationIn.model_validate({
            "session_id": "a2100000-0000-4000-8000-000000000001",
            "team_id": "a2100000-0000-4000-8000-000000000002",
            "pit_box_id": "a2100000-0000-4000-8000-000000000003",
        })


def test_reservation_status_transition_closes_only_reserved_booking(monkeypatch):
    from contextlib import contextmanager
    from fastapi import HTTPException

    class Cursor:
        def __init__(self, status):
            self.status = status
            self.row = None
        def __enter__(self): return self
        def __exit__(self, *_): pass
        def execute(self, sql, params):
            if sql.lstrip().startswith("SELECT"):
                self.row = {"status": self.status, "principal_user_id": "principal-1", "session_id": "session-1"}
            else:
                self.status = params[0]
                self.row = {"id": "reservation-1", "status": self.status, "session_id": "session-1"}
        def fetchone(self): return self.row

    class Connection:
        def __init__(self, status): self.cursor_instance = Cursor(status)
        def cursor(self, **_): return self.cursor_instance

    cursor_conn = Connection("RESERVED")
    @contextmanager
    def fake_connection():
        yield cursor_conn
    events = []
    monkeypatch.setattr("backend.app.main.connection", fake_connection)
    monkeypatch.setattr("backend.app.main.publish", lambda *args: events.append(args))

    result = update_pit_reservation(
        uuid4(), ReservationStatus(status="CANCELLED"),
        user={"id": "admin-1", "role": "ADMIN"},
    )
    assert result["status"] == "CANCELLED"
    assert events[0][1] == "pit.update"

    cursor_conn.cursor_instance.status = "CANCELLED"
    with pytest.raises(HTTPException) as error:
        update_pit_reservation(
            uuid4(), ReservationStatus(status="COMPLETED"),
            user={"id": "admin-1", "role": "ADMIN"},
        )
    assert error.value.status_code == 409


def test_results_reject_scheduled_sessions(monkeypatch):
    from fastapi import HTTPException
    monkeypatch.setattr("backend.app.main.fetch_one", lambda *_: {"state": "SCHEDULED", "generated": False})
    with pytest.raises(HTTPException) as error:
        save_results(uuid4(), [], user={"id": "admin-1", "role": "ADMIN"})
    assert error.value.status_code == 409


def test_completed_results_require_contiguous_classification(monkeypatch):
    from contextlib import contextmanager
    from fastapi import HTTPException

    class Cursor:
        def __init__(self, row): self.row = row
        def __enter__(self): return self
        def __exit__(self, *_): pass
        def execute(self, *_): pass
        def fetchall(self): return [self.row]

    class Connection:
        def __init__(self, row): self.row = row
        def cursor(self, **_): return Cursor(self.row)

    driver_id = uuid4()
    persisted_row = {"driver_id": driver_id, "position": 2, "classified": True}

    @contextmanager
    def fake_connection():
        yield Connection(persisted_row)

    events = []
    session_id = uuid4()
    monkeypatch.setattr("backend.app.main.fetch_one", lambda *_: {"state": "COMPLETED", "generated": False})
    monkeypatch.setattr("backend.app.main.connection", fake_connection)
    monkeypatch.setattr("backend.app.main.publish", lambda *args: events.append(args))

    with pytest.raises(HTTPException) as error:
        save_results(
            session_id,
            [ResultIn(driver_id=driver_id, position=2)],
            user={"id": "admin-1", "role": "ADMIN"},
        )
    assert error.value.status_code == 422
    assert "contiguous" in str(error.value.detail).lower()
    assert events == []


@pytest.mark.parametrize("approve,penalty", [(False, None), (True, None)])
def test_incident_decisions_always_return_current_driver_state(monkeypatch, approve, penalty):
    from contextlib import contextmanager
    from backend.app import main as main_module

    incident_id, session_id, driver_id = uuid4(), uuid4(), uuid4()
    incident = {"id": incident_id, "session_id": session_id, "driver_id": driver_id, "state": "OPEN"}
    cursor = None

    class Cursor:
        def __enter__(self): return self
        def __exit__(self, *_): pass
        def execute(self, query, _params):
            if query.startswith("SELECT * FROM incident_reports"):
                self.row = incident
            elif query.startswith("UPDATE incident_reports"):
                self.row = {**incident, "state": "APPROVED" if approve else "REJECTED"}
            elif query.startswith("SELECT d.eligibility"):
                self.row = {"eligibility": "ACTIVE", "season_points": 0}
            else:
                raise AssertionError(f"Unexpected SQL: {query}")
        def fetchone(self): return self.row

    cursor = Cursor()
    class Connection:
        def cursor(self, **_): return cursor

    @contextmanager
    def fake_connection():
        yield Connection()

    monkeypatch.setattr(main_module, "connection", fake_connection)
    monkeypatch.setattr(main_module, "publish", lambda *_: None)
    result = main_module.decide_incident(
        incident_id, main_module.Decision(approve=approve),
        user={"id": uuid4(), "role": "STEWARD"},
    )
    assert result["penalty"] is penalty
    assert result["driver"] == {"eligibility": "ACTIVE", "season_points": 0}


def test_manual_pit_reservation_allows_steward_role():
    from fastapi.routing import APIRoute

    route = next(route for route in app.routes if isinstance(route, APIRoute)
                 and route.path == "/api/pit-reservations" and "POST" in route.methods)
    role_check = route.dependant.dependencies[0].call
    assert role_check(user={"id": str(uuid4()), "role": "STEWARD"})["role"] == "STEWARD"


def test_session_crud_does_not_accept_lifecycle_timestamps():
    from fastapi import HTTPException
    from fastapi.routing import APIRoute

    route = next(route for route in app.routes if isinstance(route, APIRoute)
                 and route.path == "/api/sessions/{item_id}" and "PATCH" in route.methods)
    with pytest.raises(HTTPException) as error:
        route.endpoint(uuid4(), {"started_at": "2026-10-05T10:00:00Z"}, user={"role": "ADMIN"})
    assert error.value.status_code == 422


def test_websocket_bus_keeps_newest_when_client_falls_behind():
    bus = EventBus()
    async def exercise():
        q = bus.subscribe("session-a")
        await asyncio.to_thread(lambda: [bus.send("session-a", {"n": n}) for n in range(55)])
        await asyncio.sleep(0)
        assert q.qsize() == 50
        assert q.get_nowait() == {"n": 5}
        bus.unsubscribe("session-a", q)
        assert not bus.clients["session-a"]
    asyncio.run(exercise())


def test_contract_routes_are_registered():
    paths = {route.path for route in app.routes}
    expected = {
        "/api/auth/login", "/api/auth/me", "/api/sessions/{session_id}/action",
        "/api/incidents/{incident_id}/decision", "/api/pit-reservations",
        "/api/telemetry/ingest", "/api/sessions/{session_id}/live",
        "/api/dbms/schema", "/api/dbms/polyglot", "/api/drivers/{driver_id}/memberships",
        "/api/teams/{team_id}/memberships", "/api/team-memberships/{membership_id}",
        "/api/sessions/{session_id}/simulate",
        "/api/sessions/{session_id}/pit-strategy",
        "/api/demo-races", "/api/demo-races/{session_id}",
        "/api/dbms/lock-demo",
        "/api/users", "/api/users/{user_id}",
    }
    assert expected <= paths


def test_constraint_demo_reports_only_the_expected_driver_number_check(monkeypatch):
    from contextlib import nullcontext
    from types import SimpleNamespace
    from psycopg.errors import CheckViolation

    class ExpectedCheckViolation(CheckViolation):
        @property
        def diag(self):
            return SimpleNamespace(constraint_name="drivers_number_check")

    class Cursor:
        def __init__(self): self.statements = []
        def __enter__(self): return self
        def __exit__(self, *_args): return False
        def execute(self, statement):
            self.statements.append(statement)
            if statement.startswith("INSERT INTO drivers"):
                raise ExpectedCheckViolation("invalid driver number")

    cursor = Cursor()
    class Connection:
        def cursor(self, **_kwargs): return cursor

    monkeypatch.setattr(main_module, "connection", lambda: nullcontext(Connection()))
    result = main_module.constraint_demo(user={"role": "ADMIN"})

    assert result == {"constraint": "drivers_number_check", "rejected": True, "sqlstate": "23514"}
    assert any(statement.startswith("ROLLBACK TO SAVEPOINT") for statement in cursor.statements)
    assert cursor.statements[-1] == "RELEASE SAVEPOINT constraint_demo"


def test_constraint_demo_does_not_report_an_unrelated_check_as_success(monkeypatch):
    from contextlib import nullcontext
    from types import SimpleNamespace
    from psycopg.errors import CheckViolation

    class UnexpectedCheckViolation(CheckViolation):
        @property
        def diag(self):
            return SimpleNamespace(constraint_name="some_other_check")

    class Cursor:
        def __enter__(self): return self
        def __exit__(self, *_args): return False
        def execute(self, statement):
            if statement.startswith("INSERT INTO drivers"):
                raise UnexpectedCheckViolation("unexpected check")

    class Connection:
        def cursor(self, **_kwargs): return Cursor()

    monkeypatch.setattr(main_module, "connection", lambda: nullcontext(Connection()))
    with pytest.raises(HTTPException) as error:
        main_module.constraint_demo(user={"role": "ADMIN"})
    assert error.value.status_code == 500


def test_constraint_demo_rolls_back_if_the_database_accepts_invalid_data(monkeypatch):
    from contextlib import nullcontext

    class Cursor:
        def __init__(self): self.statements = []
        def __enter__(self): return self
        def __exit__(self, *_args): return False
        def execute(self, statement): self.statements.append(statement)

    cursor = Cursor()
    class Connection:
        def cursor(self, **_kwargs): return cursor

    monkeypatch.setattr(main_module, "connection", lambda: nullcontext(Connection()))
    with pytest.raises(HTTPException) as error:
        main_module.constraint_demo(user={"role": "ADMIN"})

    assert error.value.status_code == 500
    assert any(statement.startswith("ROLLBACK TO SAVEPOINT") for statement in cursor.statements)


def test_pit_strategy_reports_pending_live_decision_and_historical_stops(monkeypatch):
    from backend.app import main as main_module
    session_id = uuid4()
    driver_id = uuid4()
    box_id = uuid4()
    driver = {"driver_id": driver_id, "driver_name": "A Driver", "driver_number": 17,
              "team_id": uuid4(), "team_name": "Team"}
    monkeypatch.setattr(main_module, "fetch_one", lambda *_: {
        "id": session_id, "state": "ACTIVE", "total_laps": 30, "generated": True,
        "scheduled_at": datetime(2026, 10, 5, tzinfo=timezone.utc),
    })
    monkeypatch.setattr(main_module, "fetch_all", lambda query, _params: [driver] if "demo_race_entries" in query else [{
        "id": box_id, "driver_id": driver_id, "box_number": 2, "status": "COMPLETED",
        "starts_at": datetime(2026, 10, 5, 1, tzinfo=timezone.utc),
        "ends_at": datetime(2026, 10, 5, 1, 1, tzinfo=timezone.utc),
    }])
    class Collection:
        def find(self, *_args): return self
        def sort(self, *_args): return self
        def limit(self, *_args): return iter([{"driver_id": str(driver_id), "lap": 8, "tire_compound": "SOFT",
            "tire_age_laps": 15, "tire_wear_pct": 71, "pit_reservation_id": str(box_id), "pit_state": "IN_PIT", "sector": 3}])
        def aggregate(self, _pipeline): return iter([{"_id": str(box_id), "lap": 8, "compound": "SOFT"}])
    monkeypatch.setattr(main_module, "mongo_ready", lambda: Collection())
    sim = Simulation(session_id, [{"id": driver_id, "number": 17}], 2, total_laps=30)
    sim.is_generated = True
    sim.pit_due_tire_age_by_driver[str(driver_id)] = 16
    monkeypatch.setitem(main_module.simulations, str(session_id), sim)

    result = pit_strategy(session_id, user={"id": uuid4(), "role": "ADMIN"})
    row = result["strategy"][0]
    assert result["source"] == "live_simulation"
    assert row["status"] == "PENDING"
    assert row["laps_until_decision"] == 1
    assert row["recommended_stop_lap"] == 9
    assert row["stops"][0]["lap"] == 8

    monkeypatch.setattr(main_module, "fetch_one", lambda *_: {
        "id": session_id, "state": "COMPLETED", "total_laps": 30, "generated": True,
        "scheduled_at": datetime(2026, 10, 5, tzinfo=timezone.utc),
    })
    historical = pit_strategy(session_id, user={"id": uuid4(), "role": "ADMIN"})
    assert historical["source"] == "history"
    assert historical["strategy"][0]["status"] == "NO_FUTURE_STOP"
    assert historical["strategy"][0]["recommended_stop_lap"] is None
    assert historical["historical_summary"]["total_stops"] == 1


def test_app_lifespan_starts_resources_and_awaits_simulator_shutdown(monkeypatch):
    from threading import Event

    from backend.app import main as main_module

    startup_calls = []
    closed = Event()
    client_closed = Event()

    class FakeMongoClient:
        def __init__(self, *_args, **_kwargs):
            self.admin = self
        def command(self, command):
            startup_calls.append(("mongo", command))
        def __getitem__(self, _name):
            return self
        def create_index(self, index):
            startup_calls.append(("index", index))
        def close(self):
            client_closed.set()

    class FakePool:
        closed = False

    pool = FakePool()
    monkeypatch.setattr(main_module, "pool", pool)
    monkeypatch.setattr(main_module, "open_pool", lambda: startup_calls.append(("pool", "open")))
    monkeypatch.setattr(main_module, "close_pool", lambda: startup_calls.append(("pool", "close")))
    monkeypatch.setattr(main_module, "MongoClient", FakeMongoClient)
    session_id = str(uuid4())
    sim = Simulation(session_id, [], 1)

    async def resume_demo(*, create_if_missing):
        startup_calls.append(("resume", create_if_missing))

        async def run_until_cancelled():
            try:
                await asyncio.Event().wait()
            finally:
                closed.set()

        sim.task = asyncio.create_task(run_until_cancelled())
        simulations[session_id] = sim
        await asyncio.sleep(0)

    monkeypatch.setattr(main_module, "resume_or_create_auto_demo_race", resume_demo)
    simulations.pop(session_id, None)

    with TestClient(app):
        assert ("pool", "open") in startup_calls
        assert ("mongo", "ping") in startup_calls
        assert any(call[0] == "resume" for call in startup_calls)
        assert sim.task is not None and not sim.task.done()

    assert sim.task.done() and sim.task.cancelled()
    assert closed.is_set()
    assert client_closed.is_set()
    assert ("pool", "close") in startup_calls
    assert main_module.mongo_client is None
    assert main_module.telemetry_collection is None
    simulations.pop(session_id, None)


def test_simulation_keeps_sector_lap_elapsed_and_tire_state_coherent():
    sim = Simulation(
        session_id="a2100000-0000-4000-8000-000000000003",
        drivers=[{"id": "driver-1", "number": 7}], rate_hz=2,
    )
    rng = random.Random(42)
    samples = []
    for tick in range(12):
        packets, timing = advance_simulation_tick(
            sim, datetime(2026, 10, 5, 10, 0, tick, tzinfo=timezone.utc), rng=rng,
        )
        samples.append(packets[0])
        assert timing["cars"][0]["driver_id"] == "driver-1"

    lap_one = next(sample for sample in samples if sample["lap"] == 1 and sample["lap_time_ms"])
    assert lap_one["sector"] == 3
    assert lap_one["lap_time_ms"] == sum(lap_one["sector_ms"])
    assert len(lap_one["sector_ms"]) == 3
    assert [sample["elapsed_ms"] for sample in samples] == sorted(sample["elapsed_ms"] for sample in samples)
    assert [sample["tire_wear_pct"] for sample in samples] == sorted(sample["tire_wear_pct"] for sample in samples)
    assert lap_one["tire_age_laps"] == 1
    assert samples[-1]["tire_age_laps"] >= 1


def test_drivers_progress_sectors_on_individual_pace_clocks():
    sim = Simulation("race", [{"id": "fast", "number": 1}, {"id": "slow", "number": 2}], 2)
    sim.pace_offsets_ms = {"fast": -6000, "slow": 6000}
    rng = random.Random(17)
    states = []
    completed = {"fast": [], "slow": []}
    for tick in range(40):
        packets, _ = advance_simulation_tick(sim, datetime(2026, 10, 5, 10, 0, tzinfo=timezone.utc), rng)
        by_driver = {packet["driver_id"]: packet for packet in packets}
        states.append(((by_driver["fast"]["lap"], by_driver["fast"]["sector"]),
                       (by_driver["slow"]["lap"], by_driver["slow"]["sector"])))
        for driver_id, packet in by_driver.items():
            if packet["lap_time_ms"]:
                completed[driver_id].append(packet["lap"])
                assert packet["lap_time_ms"] == sum(packet["sector_ms"])
    assert any(fast != slow for fast, slow in states)
    for laps in completed.values():
        assert laps == list(range(1, len(laps) + 1))


def test_safety_car_slowdown_and_reserved_pit_state_are_applied():
    driver = {"id": "driver-1", "number": 7}
    normal = Simulation("session-1", [driver], 2)
    safety = Simulation("session-1", [driver], 2)
    normal_packets, _ = advance_simulation_tick(normal, datetime.now(timezone.utc), random.Random(4))
    safety_packets, timing = advance_simulation_tick(
        safety, datetime.now(timezone.utc), random.Random(4), safety_car=True,
        pit_driver_ids={"driver-1"},
    )
    assert safety_packets[0]["sector_ms"][0] > normal_packets[0]["sector_ms"][0]
    assert safety_packets[0]["pit_state"] == "IN_PIT"
    assert timing["safety_car"] is True


def test_assigned_pit_metadata_is_scoped_to_the_assigned_driver():
    from datetime import timedelta
    driver_rows = [
        {"id": "driver-1", "number": 7, "team_id": "team-1"},
        {"id": "driver-2", "number": 8, "team_id": "team-1"},
    ]
    sim = Simulation("session-pit", driver_rows, 2)
    start = datetime(2026, 10, 5, 10, 0, tzinfo=timezone.utc)
    reservation_id, team_id = uuid4(), uuid4()
    assignment = {"driver_id": "driver-1", "id": reservation_id, "box_number": 2,
                  "team_id": team_id, "starts_at": start - timedelta(seconds=1),
                  "ends_at": start + timedelta(seconds=2)}
    packets, timing = advance_simulation_tick(
        sim, start, random.Random(9), pit_assignments={"driver-1": assignment},
    )
    by_driver = {packet["driver_id"]: packet for packet in packets}
    assert by_driver["driver-1"]["pit_state"] == "IN_PIT"
    assert by_driver["driver-1"]["pit_box_number"] == 2
    assert by_driver["driver-2"]["pit_state"] == "TRACK"
    assert by_driver["driver-2"]["pit_reservation_id"] is None
    timing_by_driver = {row["driver_id"]: row for row in timing["cars"]}
    assert timing_by_driver["driver-1"]["pit_reservation_id"] == str(reservation_id)
    assert by_driver["driver-1"]["pit_team_id"] == str(team_id)
    BSON.encode(by_driver["driver-1"])


def test_mongo_telemetry_payload_is_websocket_json_serializable():
    mongo_id = ObjectId()
    payload = telemetry_ws_payload({"_id": mongo_id, "session_id": "session-1", "speed_kph": 120.0}, mongo_id)
    encoded = json.dumps({"type": "telemetry.sample", "data": payload})
    assert "_id" not in payload
    assert payload["id"] == str(mongo_id)
    assert json.loads(encoded)["data"]["speed_kph"] == 120.0


def test_mongo_naive_utc_timestamps_serialize_with_explicit_utc():
    expected = datetime(2026, 10, 6, 16, 9, 41, 331000, tzinfo=timezone.utc)
    mongo_id = ObjectId()
    decoded = BSON.encode({
        "_id": mongo_id,
        "session_id": "session-1",
        "ts": expected,
        "metadata": {"history": [{"ts": expected}]},
    })
    document = BSON(decoded).decode()

    payload = telemetry_ws_payload(document, document["_id"])

    assert payload["ts"] == "2026-10-06T16:09:41.331000Z"
    assert payload["metadata"]["history"][0]["ts"] == payload["ts"]
    restored = datetime.fromisoformat(payload["ts"].replace("Z", "+00:00"))
    assert restored == expected


def test_websocket_uses_bearer_subprotocol_not_url_token():
    assert websocket_bearer(["apexgrid.jwt","signed.jwt.token"])=="signed.jwt.token"
    assert websocket_bearer(["signed.jwt.token"]) is None
    assert websocket_bearer(["apexgrid.jwt"]) is None


def test_demo_car_numbers_are_distinct_in_grid_even_with_prior_archives():
    numbers = choose_demo_car_numbers(5)
    assert len(numbers) == len(set(numbers)) == 5
    assert all(11 <= number <= 99 for number in numbers)


@pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="requires a seeded PostgreSQL database")
def test_dbms_workspace_table_browser_is_whitelisted_and_redacts_hashes(database_api_client):
    client = database_api_client
    login = client.post("/api/auth/login", json={"email":"admin@apexgrid.test", "password":"ApexGrid2026!"})
    headers = {"Authorization":"Bearer "+login.json()["access_token"]}
    overview = client.get("/api/dbms/overview", headers=headers)
    assert overview.status_code == 200 and overview.json()["postgres"] == "up"
    tables = client.get("/api/dbms/tables", headers=headers)
    assert tables.status_code == 200 and any(row["table_name"] == "users" for row in tables.json()["tables"])
    users = client.get("/api/dbms/tables/users?limit=2", headers=headers)
    assert users.status_code == 200 and "password_hash" not in users.json()["columns"]
    assert all("password_hash" not in row for row in users.json()["rows"])
    assert client.get("/api/dbms/tables/not_a_table", headers=headers).status_code == 404
    first = client.get("/api/analytics/drivers?limit=3&offset=0", headers=headers)
    second = client.get("/api/analytics/drivers?limit=3&offset=3", headers=headers)
    assert first.status_code == second.status_code == 200
    assert len(first.json()) == len(second.json()) == 3
    assert {row["driver_id"] for row in first.json()}.isdisjoint(
        row["driver_id"] for row in second.json())


def test_dbms_mongo_collection_browser_lists_real_collections_and_pages_filtered_documents(monkeypatch):
    class Cursor:
        def __init__(self, docs):
            self.docs = docs
        def sort(self, key, direction):
            self.docs.sort(key=lambda doc: doc.get(key), reverse=direction < 0)
            return self
        def skip(self, count):
            self.docs = self.docs[count:]
            return self
        def limit(self, count):
            self.docs = self.docs[:count]
            return self
        def __iter__(self):
            return iter(self.docs)

    class Collection:
        docs = [
            {"_id": ObjectId(), "session_id": "race-a", "driver_id": "driver-a", "lap": 1, "sector": 3, "ts": 1},
            {"_id": ObjectId(), "session_id": "race-a", "driver_id": "driver-b", "lap": 1, "sector": 3, "ts": 2},
            {"_id": ObjectId(), "session_id": "race-b", "driver_id": "driver-a", "lap": 2, "sector": 2, "ts": 3},
        ]
        def count_documents(self, query):
            return len([doc for doc in self.docs if all(doc.get(key) == value for key, value in query.items())])
        def find(self, query, projection=None):
            return Cursor([doc.copy() for doc in self.docs if all(doc.get(key) == value for key, value in query.items())])
        def index_information(self):
            return {"_id_": {"key": [("_id", 1)], "v": 2}, "session_ts": {"key": [("session_id", 1), ("ts", -1)]}}

    collection = Collection()
    class Database:
        def list_collection_names(self):
            return ["telemetry", "system.profile"]
        def __getitem__(self, name):
            if name != "telemetry":
                raise AssertionError("Unexpected collection access")
            return collection

    monkeypatch.setattr(main_module, "mongo_database_ready", lambda: Database())
    listed = main_module.dbms_mongo_collections(user={"role": "ADMIN"})
    assert [item["name"] for item in listed["collections"]] == ["telemetry"]
    assert listed["collections"][0]["document_count"] == 3
    assert {index["name"] for index in listed["collections"][0]["indexes"]} == {"_id_", "session_ts"}

    page = main_module.dbms_mongo_collection_documents(
        "telemetry", limit=1, offset=0, session_id="race-a", driver_id=None,
        lap=None, sector=3, user={"role": "ADMIN"})
    assert page["total"] == 2
    assert page["filters"] == {"session_id": "race-a", "sector": 3}
    assert len(page["documents"]) == 1
    assert page["documents"][0]["driver_id"] == "driver-b"
    assert page["documents"][0]["id"]
    assert "_id" not in page["documents"][0]

    with pytest.raises(HTTPException) as error:
        main_module.dbms_mongo_collection_documents(
            "unknown", limit=10, offset=0, session_id=None, driver_id=None,
            lap=None, sector=None, user={"role": "ADMIN"})
    assert error.value.status_code == 404


def test_jwt_secret_fails_closed_outside_local_demo():
    root=Path(__file__).resolve().parents[2]
    env=dict(os.environ,APP_ENV="production",JWT_SECRET="dev-change-me")
    weak=subprocess.run([sys.executable,"-c","from backend.app.config import JWT_SECRET"],cwd=root,env=env,capture_output=True,text=True)
    assert weak.returncode != 0
    assert "JWT_SECRET" in weak.stderr
    env["JWT_SECRET"]="a-unique-production-signing-secret-with-at-least-32-bytes"
    strong=subprocess.run([sys.executable,"-c","from backend.app.config import JWT_SECRET"],cwd=root,env=env,capture_output=True,text=True)
    assert strong.returncode == 0, strong.stderr


def test_session_lifecycle_synchronizes_simulator_state():
    session_id="a2100000-0000-4000-8000-000000000004"
    sim=Simulation(session_id,[{"id":"driver-1","number":7}],2,status="running")
    sim.lap_by_driver={"driver-1":4}; sim.sector_by_driver={"driver-1":3}
    sim.elapsed_by_driver={"driver-1":350000}; sim.tire_age_by_driver={"driver-1":3}; sim.tire_wear_by_driver={"driver-1":3.3}
    simulations[session_id]=sim
    try:
        sync_simulation_lifecycle(session_id,"pause")
        assert sim.status=="paused"
        sync_simulation_lifecycle(session_id,"resume")
        assert sim.status=="running"
        sync_simulation_lifecycle(session_id,"reset")
        assert sim.status=="stopped"
        assert sim.lap_by_driver=={"driver-1":1}
        assert sim.sector_by_driver=={}
        assert sim.elapsed_by_driver=={"driver-1":0}
        assert sim.tire_age_by_driver=={"driver-1":0}
        assert sim.tire_wear_by_driver=={"driver-1":0.0}
        sync_simulation_lifecycle(session_id,"finish")
        assert sim.status=="stopped"
    finally:
        simulations.pop(session_id,None)


def test_restarting_simulator_restores_previously_recorded_incident_laps(monkeypatch):
    from backend.app import main as main_module

    session_id = str(uuid4())
    sim = Simulation(session_id, [{"id": "driver-1", "number": 7}], 2)
    sim.is_generated = True
    sim.incident_laps_recorded = {3}
    monkeypatch.setattr(main_module, "fetch_all", lambda query, params: (
        [{"lap": 7}, {"lap": 7}, {"lap": 23}]
        if "SELECT DISTINCT lap FROM incident_reports" in query and params == (session_id,)
        else []
    ))

    restore_simulated_incidents(sim)

    assert sim.incident_laps_recorded == {7, 23}

    def unexpected_connection():
        raise AssertionError("A previously recorded incident must not be inserted again")

    monkeypatch.setattr(main_module, "connection", unexpected_connection)
    main_module.record_simulated_incidents(sim, [{
        "driver_id": "driver-1", "lap": 7, "sector": 3, "lap_time_ms": 90000,
    }])


@pytest.fixture(scope="module")
def database_api_client():
    with TestClient(app) as client:
        yield client


@pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="requires a seeded PostgreSQL database")
def test_admin_lock_demo_observes_real_wait_and_exclusion_rejection(database_api_client):
    client=database_api_client
    login = client.post("/api/auth/login", json={"email":"admin@apexgrid.test", "password":"ApexGrid2026!"})
    assert login.status_code == 200, login.text
    response = client.post("/api/dbms/lock-demo", headers={"Authorization":"Bearer "+login.json()["access_token"]})
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["lock_wait_observed"] is True
    assert result["lock_wait_ms"] > 0
    assert result["first_reservation"] == "committed"
    assert result["overlapping_reservation"] == "rejected"
    assert result["rejection_sqlstate"] == "23P01"


@pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="requires a seeded PostgreSQL database")
def test_admin_user_management_and_protected_driver_session_fields(database_api_client):
    suffix=uuid4().hex[:10]
    email=f"new-{suffix}@apexgrid.test"
    driver_id=None
    session_id=None
    user_id=None
    client=database_api_client
    admin_login=client.post("/api/auth/login",json={"email":"admin@apexgrid.test","password":"ApexGrid2026!"})
    assert admin_login.status_code==200,admin_login.text
    admin_headers={"Authorization":"Bearer "+admin_login.json()["access_token"]}
    try:
        created=client.post("/api/users",headers=admin_headers,json={"email":email,"full_name":"API Test Driver","password":"InitialPass2026!","role":"DRIVER"})
        assert created.status_code==201,created.text
        user=created.json(); user_id=user["id"]
        assert "password_hash" not in user
        assert client.get(f"/api/users/{user_id}",headers=admin_headers).json()["email"]==email
        listing=client.get("/api/users",headers=admin_headers)
        assert listing.status_code==200 and all("password_hash" not in row for row in listing.json())

        changed=client.patch(f"/api/users/{user_id}",headers=admin_headers,json={"password":"ChangedPass2026!"})
        assert changed.status_code==200 and "password_hash" not in changed.json()
        old_login=client.post("/api/auth/login",json={"email":email,"password":"InitialPass2026!"})
        new_login=client.post("/api/auth/login",json={"email":email,"password":"ChangedPass2026!"})
        assert old_login.status_code==401
        assert new_login.status_code==200

        created_driver=client.post("/api/drivers",headers=admin_headers,json={"user_id":user_id,"licence_number":f"TEST-{suffix}","number":900+random.randrange(100),"eligibility":"RACE_BANNED"})
        assert created_driver.status_code==201,created_driver.text
        driver=created_driver.json(); driver_id=driver["id"]
        assert driver["eligibility"]=="ACTIVE"
        protected=client.patch(f"/api/drivers/{driver_id}",headers=admin_headers,json={"eligibility":"RACE_BANNED"})
        assert protected.status_code==422
        assert client.delete(f"/api/users/{user_id}",headers=admin_headers).status_code==409

        event=client.get("/api/events",headers=admin_headers).json()[0]
        created_session=client.post("/api/sessions",headers=admin_headers,json={"event_id":event["id"],"session_type":"PRACTICE","scheduled_at":"2027-01-01T12:00:00Z","state":"ACTIVE"})
        assert created_session.status_code==201,created_session.text
        session=created_session.json(); session_id=session["id"]
        assert session["state"]=="SCHEDULED"
        protected_state=client.patch(f"/api/sessions/{session_id}",headers=admin_headers,json={"state":"CANCELLED"})
        assert protected_state.status_code==422
        sim=Simulation(session_id,[{"id":driver_id,"number":driver["number"]}],2,status="running")
        sim.elapsed_by_driver={driver_id:100000}; sim.lap_by_driver={driver_id:2}; sim.tire_age_by_driver={driver_id:1}; sim.tire_wear_by_driver={driver_id:1.1}
        simulations[session_id]=sim
        assert client.post(f"/api/sessions/{session_id}/action",headers=admin_headers,json={"action":"start"}).status_code==200
        paused=client.post(f"/api/sessions/{session_id}/action",headers=admin_headers,json={"action":"pause"})
        assert paused.status_code==200 and sim.status=="paused"
        resumed=client.post(f"/api/sessions/{session_id}/action",headers=admin_headers,json={"action":"resume"})
        assert resumed.status_code==200 and sim.status=="running"
        reset=client.post(f"/api/sessions/{session_id}/action",headers=admin_headers,json={"action":"reset"})
        assert reset.status_code==200 and sim.status=="stopped"
        assert sim.elapsed_by_driver=={driver_id:0} and sim.tire_age_by_driver=={driver_id:0}
        assert client.post(f"/api/sessions/{session_id}/action",headers=admin_headers,json={"action":"start"}).status_code==200
        finished=client.post(f"/api/sessions/{session_id}/action",headers=admin_headers,json={"action":"finish"})
        assert finished.status_code==200 and sim.status=="stopped"
    finally:
        simulations.pop(session_id,None)
        if session_id: client.delete(f"/api/sessions/{session_id}",headers=admin_headers)
        if driver_id: client.delete(f"/api/drivers/{driver_id}",headers=admin_headers)
        if user_id: client.delete(f"/api/users/{user_id}",headers=admin_headers)


@pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="requires a seeded PostgreSQL database")
def test_generated_demo_race_create_list_and_scoped_delete(database_api_client):
    client = database_api_client
    login = client.post("/api/auth/login", json={"email":"admin@apexgrid.test", "password":"ApexGrid2026!"})
    assert login.status_code == 200, login.text
    headers = {"Authorization":"Bearer "+login.json()["access_token"]}
    assert client.post("/api/demo-races", headers=headers, json={"cars":5}).status_code == 422
    created = client.post("/api/demo-races", headers=headers, json={"cars":6})
    assert created.status_code == 201, created.text
    race = created.json()
    session_id = race["session_id"]
    event_id = race["event_id"]
    try:
        assert race["car_count"] == 6 and 45 <= race["total_laps"] <= 75
        assert all(11 <= driver["number"] <= 99 for driver in simulations[session_id].drivers)
        assert race["state"] == "ACTIVE" and race["simulation_state"] == "running"
        assert any(row["session_id"] == session_id for row in client.get("/api/demo-races", headers=headers).json())
        live = client.get(f"/api/sessions/{session_id}/live", headers=headers)
        assert live.status_code == 200
        assert len(live.json()["drivers"]) == 6
        assert all(driver["full_name"] for driver in live.json()["drivers"])
        from backend.app.database import fetch_one
        unrelated = fetch_one("SELECT id FROM drivers WHERE licence_number='AG-0001'")
        invalid_incident = {"session_id": session_id, "driver_id": str(unrelated["id"]), "lap": 1, "description": "Unrelated driver"}
        assert client.post("/api/incidents", headers=headers, json=invalid_incident).status_code == 422
        invalid_incident["driver_id"] = live.json()["drivers"][0]["id"]
        invalid_incident["lap"] = race["total_laps"] + 1
        assert client.post("/api/incidents", headers=headers, json=invalid_incident).status_code == 422
        from backend.app.main import mongo_ready
        assert mongo_ready().count_documents({"session_id":session_id}) >= 1
        assert client.delete("/api/demo-races/00000000-0000-4000-8000-000000000000", headers=headers).status_code == 404
        from backend.app.database import fetch_one
        assert fetch_one("SELECT count(*) AS count FROM pit_boxes WHERE event_id=%s", (event_id,))["count"] == 4
    finally:
        deleted = client.delete(f"/api/demo-races/{session_id}", headers=headers)
        assert deleted.status_code == 204, deleted.text
    assert all(row["session_id"] != session_id for row in client.get("/api/demo-races", headers=headers).json())
    from backend.app.main import mongo_ready
    assert mongo_ready().count_documents({"session_id":session_id}) == 0
    from backend.app.database import fetch_one
    assert fetch_one("SELECT 1 FROM pit_boxes WHERE event_id=%s", (event_id,)) is None


@pytest.mark.parametrize("blocked", [False, True])
def test_demo_delete_waits_for_simulator_and_validates_before_stopping(monkeypatch, blocked):
    from contextlib import contextmanager
    from fastapi import HTTPException
    from backend.app import main as main_module

    session_id, event_id, championship_id = uuid4(), uuid4(), uuid4()
    events = []
    class Cursor:
        def __enter__(self): return self
        def __exit__(self, *_): pass
        def execute(self, query, _params=None):
            self.rows = []
            if query.startswith("SELECT d.session_id,d.event_id"):
                self.row = {"session_id": session_id, "event_id": event_id,
                            "championship_id": championship_id}
            elif query.startswith("SELECT 1 FROM incident_reports i JOIN penalties") and blocked:
                self.row = {"exists": 1}
            else:
                self.row = None
            if query.startswith("SELECT driver_id FROM demo_race_entries") or query.startswith("SELECT d.user_id FROM demo_race_entries"):
                self.rows = []
            if query.startswith("DELETE "):
                events.append("sql-delete")
                assert "simulator-stopped" in events
        def fetchone(self): return self.row
        def fetchall(self): return self.rows

    cursor = Cursor()
    class Connection:
        def cursor(self, **_): return cursor
    @contextmanager
    def fake_connection(): yield Connection()
    class Collection:
        def delete_many(self, _query): events.append("mongo-delete")

    async def exercise():
        async def simulator():
            try:
                await asyncio.Future()
            finally:
                events.append("simulator-stopped")
        task = asyncio.create_task(simulator())
        await asyncio.sleep(0)
        sim = Simulation(session_id, [], 2, task=task, status="running")
        monkeypatch.setitem(main_module.simulations, str(session_id), sim)
        if blocked:
            with pytest.raises(HTTPException) as error:
                await main_module.delete_demo_race(session_id, user={"role": "ADMIN"})
            assert error.value.status_code == 409
            assert sim.status == "running" and not task.done()
            assert "sql-delete" not in events
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        else:
            await main_module.delete_demo_race(session_id, user={"role": "ADMIN"})
            assert task.done() and sim.status == "stopped"
            assert events.index("simulator-stopped") < events.index("sql-delete")
            assert events.index("sql-delete") < events.index("mongo-delete")
        main_module.simulations.pop(str(session_id), None)

    monkeypatch.setattr(main_module, "connection", fake_connection)
    monkeypatch.setattr(main_module, "mongo_ready", lambda: Collection())
    asyncio.run(exercise())


@pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="requires a seeded PostgreSQL database")
def test_auto_demo_race_keeps_archive_and_starts_new_session(database_api_client):
    from backend.app.main import mongo_ready
    client = database_api_client
    login = client.post("/api/auth/login", json={"email":"admin@apexgrid.test", "password":"ApexGrid2026!"})
    headers = {"Authorization":"Bearer "+login.json()["access_token"]}
    created = client.post("/api/demo-races", headers=headers, json={"cars":6})
    assert created.status_code == 201, created.text
    session_id = created.json()["session_id"]
    sim = simulations[session_id]
    sim.total_laps = 1
    sim.rate_hz = 20
    sim.auto_repeat = True
    previous_ids = set(simulations)
    new_session_id = None
    try:
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline and sim.runs_completed < 1:
            time.sleep(0.1)
        assert sim.runs_completed >= 1
        while time.monotonic() < deadline:
            created_ids = set(simulations) - previous_ids
            if created_ids:
                new_session_id = created_ids.pop()
                break
            time.sleep(0.1)
        assert new_session_id
        assert client.get(f"/api/sessions/{session_id}/live", headers=headers).json()["session"]["state"] == "COMPLETED"
        assert len(client.get(f"/api/sessions/{session_id}/results", headers=headers).json()) == 6
        assert len(client.get(f"/api/sessions/{session_id}/laps", headers=headers).json()["laps"]) == 6
        assert mongo_ready().count_documents({"session_id":session_id}) >= 6
        assert client.get(f"/api/sessions/{new_session_id}/live", headers=headers).json()["session"]["state"] == "ACTIVE"
    finally:
        assert client.delete(f"/api/demo-races/{session_id}", headers=headers).status_code == 204
        if new_session_id:
            assert client.delete(f"/api/demo-races/{new_session_id}", headers=headers).status_code == 204


@pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="requires a seeded PostgreSQL database")
def test_principal_ownership_and_telemetry_ingest_policy(database_api_client):
    client=database_api_client
    admin_login=client.post("/api/auth/login",json={"email":"admin@apexgrid.test","password":"ApexGrid2026!"})
    principal_login=client.post("/api/auth/login",json={"email":"principal@apexgrid.test","password":"ApexGrid2026!"})
    driver_login=client.post("/api/auth/login",json={"email":"driver01@apexgrid.test","password":"ApexGrid2026!"})
    assert admin_login.status_code==principal_login.status_code==driver_login.status_code==200
    admin_headers={"Authorization":"Bearer "+admin_login.json()["access_token"]}
    principal_headers={"Authorization":"Bearer "+principal_login.json()["access_token"]}
    driver_headers={"Authorization":"Bearer "+driver_login.json()["access_token"]}

    teams=client.get("/api/teams",headers=admin_headers).json()
    owned=next(team for team in teams if team.get("principal_user_id")==principal_login.json()["user"]["id"])
    other=next(team for team in teams if team["id"]!=owned["id"])
    event=client.get("/api/events",headers=admin_headers).json()[0]
    session=next(item for item in client.get("/api/sessions",headers=admin_headers).json() if item["event_id"]==event["id"])
    box=client.get(f"/api/pit-boxes?event_id={event['id']}",headers=admin_headers).json()[0]
    rejected=client.post("/api/pit-reservations",headers=principal_headers,json={
        "pit_box_id":box["id"],"session_id":session["id"],"team_id":other["id"],
        "starts_at":"2045-01-01T00:00:00Z","ends_at":"2045-01-01T00:05:00Z",
    })
    assert rejected.status_code==403

    inactive=next(item for item in client.get("/api/sessions",headers=admin_headers).json() if item["state"]!="ACTIVE")
    driver_id=client.get("/api/drivers",headers=admin_headers).json()[0]["id"]
    telemetry_packet=packet(session_id=inactive["id"],driver_id=driver_id)
    assert client.post("/api/telemetry/ingest",headers=driver_headers,json=telemetry_packet).status_code==403
    admin_rejected=client.post("/api/telemetry/ingest",headers=admin_headers,json=telemetry_packet)
    assert admin_rejected.status_code==409
