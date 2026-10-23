"""Database independent contract tests for login attempt throttling."""

from app.auth_router import create_auth_router
from fastapi import FastAPI
from fastapi.testclient import TestClient


def _client(monkeypatch, *, users=None, host="192.0.2.1"):
    users = users or {}
    monkeypatch.setattr("app.auth_router.bcrypt.checkpw", lambda *_: False)

    def fetch_one(_query, params=()):
        return users.get(params[0].lower())

    app = FastAPI()
    app.include_router(
        create_auth_router(
            lambda _request: None,
            lambda: fetch_one,
            lambda value: value,
            lambda: False,
            lambda: None,
        )
    )
    return TestClient(app, client=(host, 50000))


def _login(client, email, *, headers=None):
    return client.post(
        "/api/auth/login",
        json={"email": email, "password": "wrong"},
        headers=headers,
    )


def test_invalid_credentials_keep_existing_response(monkeypatch):
    response = _login(_client(monkeypatch), "unknown@example.test")
    assert (response.status_code, response.json()["detail"]) == (
        401,
        "Invalid email or password",
    )


def test_sixth_attempt_for_normalized_account_is_limited_across_sources(monkeypatch):
    client = _client(monkeypatch)
    for attempt in range(5):
        source = TestClient(client.app, client=(f"192.0.2.{attempt + 1}", 50000))
        response = _login(source, "User@example.test" if attempt % 2 else "user@example.test")
        assert response.status_code == 401
    response = _login(TestClient(client.app, client=("192.0.2.99", 50000)), "USER@example.test")
    assert response.status_code == 429
    assert "Retry-After" in response.headers


def test_sixth_attempt_for_source_is_limited_across_accounts_and_proxy_headers(monkeypatch):
    client = _client(monkeypatch)
    for attempt in range(5):
        response = _login(
            client,
            f"person{attempt}@example.test",
            headers={"X-Forwarded-For": f"198.51.100.{attempt + 1}"},
        )
        assert response.status_code == 401
    response = _login(
        client,
        "person5@example.test",
        headers={"X-Forwarded-For": "203.0.113.200"},
    )
    assert response.status_code == 429
    assert "Retry-After" in response.headers


def test_unknown_accounts_are_limited_and_recover_after_window(monkeypatch):
    import time

    now = [1000.0]
    monkeypatch.setattr(time, "monotonic", lambda: now[0])
    client = _client(
        monkeypatch,
        users={
            "known@example.test": {
                "id": 7,
                "email": "known@example.test",
                "password_hash": "unused",
                "full_name": "Known User",
                "role": "DRIVER",
            }
        },
    )
    known_client = TestClient(client.app, client=("192.0.2.2", 50000))
    for _ in range(5):
        response = _login(client, "missing@example.test")
        assert response.status_code == 401
    limited = _login(client, "MISSING@example.test")
    assert limited.status_code == 429
    assert "Retry-After" in limited.headers
    for _ in range(5):
        assert _login(known_client, "known@example.test").status_code == 401
    known_limited = _login(known_client, "KNOWN@example.test")
    assert known_limited.status_code == 429
    assert "Retry-After" in known_limited.headers
    now[0] += 61
    recovered = _login(client, "missing@example.test")
    assert recovered.status_code == 401


def test_repeated_successful_logins_do_not_consume_account_limit(monkeypatch):
    email = "known@example.test"
    user = {
        "id": 7,
        "email": email,
        "password_hash": "unused",
        "full_name": "Known User",
        "role": "DRIVER",
    }
    client = _client(monkeypatch, users={email: user})
    monkeypatch.setattr("app.auth_router.bcrypt.checkpw", lambda *_: True)

    for _ in range(6):
        response = _login(client, email)
        assert response.status_code == 200
        assert set(response.json()) == {"access_token", "token_type", "user"}
        assert response.json()["user"] == {
            "id": 7,
            "email": email,
            "full_name": "Known User",
            "role": "DRIVER",
        }
        assert "access_token" in response.json()
        assert "set-cookie" in response.headers


def test_distinct_successful_accounts_do_not_consume_source_limit(monkeypatch):
    users = {
        f"person{index}@example.test": {
            "id": index,
            "email": f"person{index}@example.test",
            "password_hash": "unused",
            "full_name": f"Person {index}",
            "role": "DRIVER",
        }
        for index in range(6)
    }
    client = _client(monkeypatch, users=users)
    monkeypatch.setattr("app.auth_router.bcrypt.checkpw", lambda *_: True)

    for email in users:
        response = _login(client, email)
        assert response.status_code == 200
        assert response.json()["user"]["email"] == email
        assert set(response.json()) == {"access_token", "token_type", "user"}
        assert "set-cookie" in response.headers
