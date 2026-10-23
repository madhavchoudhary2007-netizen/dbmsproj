import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from starlette.websockets import WebSocketDisconnect

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from backend.tests.test_logout_revocation import offline_auth as offline_auth
from backend.tests.test_logout_revocation import signed_token


@pytest.mark.parametrize("jti", ["", 7, ["bad"]])
def test_malformed_jti_is_rejected(offline_auth, jti):
    client, key, user_id, _, main = offline_auth
    token = main.jwt.encode(
        {"sub": str(user_id), "exp": datetime.now(UTC) + timedelta(minutes=5), "jti": jti},
        key,
        algorithm=main.JWT_ALGORITHM,
    )
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_revocation_lookup_outage_fails_closed_for_http_and_websocket(offline_auth, monkeypatch):
    client, key, user_id, _, main = offline_auth
    monkeypatch.setattr(
        main.token_revocation, "is_revoked", lambda _jti: (_ for _ in ()).throw(RuntimeError())
    )
    token = signed_token(main, key, user_id)
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 503
    with (
        pytest.raises(WebSocketDisconnect) as closed,
        client.websocket_connect(
            f"/api/ws/sessions/{user_id}", subprotocols=["apexgrid.jwt", token]
        ),
    ):
        pytest.fail("revocation lookup outage accepted the WebSocket")
    assert closed.value.code == 4401


def test_revoke_outage_returns_503_without_clearing_cookies(offline_auth, monkeypatch):
    client, key, user_id, _, main = offline_auth
    monkeypatch.setattr(
        main.token_revocation, "revoke_token", lambda *_: (_ for _ in ()).throw(RuntimeError())
    )
    token = signed_token(main, key, user_id)
    response = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 503
    assert "set-cookie" not in response.headers


@pytest.mark.parametrize("browser", [False, True])
def test_login_purges_revocations_before_issuing_tokens(offline_auth, monkeypatch, browser):
    client, _, user_id, _, main = offline_auth
    auth_router = __import__("backend.app.auth_router", fromlist=["auth_router"])
    user = {
        "id": user_id,
        "email": "fixture@example.test",
        "password_hash": "placeholder",
        "full_name": "Test User",
        "role": "ADMIN",
    }
    monkeypatch.setattr(main, "fetch_one", lambda *_: user)
    monkeypatch.setattr(auth_router.bcrypt, "checkpw", lambda *_: True)
    calls = []
    monkeypatch.setattr(
        auth_router.token_revocation,
        "purge_expired_revocations",
        lambda: calls.append("purged"),
    )
    headers = {"Origin": "http://localhost:3000"} if browser else {}
    response = client.post(
        "/api/auth/login",
        json={"email": user["email"], "password": "password"},
        headers=headers,
    )
    assert response.status_code == 200
    assert calls == ["purged"]
    if browser:
        assert "access_token" not in response.json()
        assert "apexgrid_session" in response.headers.get("set-cookie", "")
    else:
        claims = main.jwt.decode(
            response.json()["access_token"], main.JWT_SECRET, algorithms=[main.JWT_ALGORITHM]
        )
        assert claims["sub"] == str(user_id)
        assert claims["role"] == "ADMIN"


def test_login_cleanup_outage_returns_503_without_token_or_cookies(offline_auth, monkeypatch):
    client, _, user_id, _, main = offline_auth
    auth_router = __import__("backend.app.auth_router", fromlist=["auth_router"])
    user = {
        "id": user_id,
        "email": "fixture@example.test",
        "password_hash": "placeholder",
        "full_name": "Test User",
        "role": "ADMIN",
    }
    monkeypatch.setattr(main, "fetch_one", lambda *_: user)
    monkeypatch.setattr(auth_router.bcrypt, "checkpw", lambda *_: True)
    monkeypatch.setattr(
        auth_router.token_revocation,
        "purge_expired_revocations",
        lambda: (_ for _ in ()).throw(RuntimeError()),
    )
    response = client.post("/api/auth/login", json={"email": user["email"], "password": "password"})
    assert response.status_code == 503
    assert "access_token" not in response.json()
    assert "set-cookie" not in response.headers
