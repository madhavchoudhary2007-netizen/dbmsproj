import importlib
import secrets
import sys
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect


@pytest.fixture
def offline_auth(monkeypatch):
    key = secrets.token_urlsafe(48)
    user_id = uuid.uuid4()
    revoked = set()
    monkeypatch.setenv("JWT_SECRET", key)
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    main = importlib.import_module("backend.app.main")
    auth_router = importlib.import_module("backend.app.auth_router")
    monkeypatch.setattr(main, "JWT_SECRET", key)
    monkeypatch.setattr(auth_router, "JWT_SECRET", key)
    monkeypatch.setattr(main.app.state, "runtime_lease", None, raising=False)
    monkeypatch.setattr(
        main,
        "fetch_one",
        lambda query, params=(): (
            {
                "id": user_id,
                "email": "fixture@example.test",
                "full_name": "Test User",
                "role": "ADMIN",
            }
            if params and str(params[0]) == str(user_id)
            else None
        ),
    )
    try:
        revocation = importlib.import_module("backend.app.token_revocation")
    except ModuleNotFoundError as error:
        if error.name != "backend.app.token_revocation":
            raise
    else:
        monkeypatch.setattr(revocation, "is_revoked", lambda jti: jti in revoked)
        monkeypatch.setattr(revocation, "revoke_token", lambda jti, expiry: revoked.add(jti))
        monkeypatch.setattr(revocation, "purge_expired_revocations", lambda: None)
    return TestClient(main.app), key, user_id, revoked, main


def signed_token(main, key, user_id, jti="opaque-fixture-jti"):
    claims = {"sub": str(user_id), "exp": datetime.now(UTC) + timedelta(minutes=5)}
    if jti is not None:
        claims["jti"] = jti
    return main.jwt.encode(claims, key, algorithm=main.JWT_ALGORITHM)


def csrf_token(jti, key):
    return importlib.import_module("backend.app.auth_cookie").create_csrf_token(jti, key)


@pytest.mark.parametrize("jti", ["opaque-fixture-jti", str(uuid.uuid4())])
def test_bearer_logout_rejects_reuse_for_opaque_and_uuid_jti(offline_auth, jti):
    client, key, user_id, _, main = offline_auth
    token = signed_token(main, key, user_id, jti)
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/auth/me", headers=headers).status_code == 200
    response = client.post("/api/auth/logout", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"detail": "Logged out"}
    assert client.get("/api/auth/me", headers=headers).status_code == 401


def test_revoked_bearer_is_rejected_during_websocket_handshake(offline_auth):
    client, key, user_id, _, main = offline_auth
    token = signed_token(main, key, user_id)
    headers = {"Authorization": f"Bearer {token}"}
    assert client.post("/api/auth/logout", headers=headers).status_code == 200
    with (
        pytest.raises(WebSocketDisconnect) as closed,
        client.websocket_connect(
            f"/api/ws/sessions/{uuid.uuid4()}", subprotocols=["apexgrid.jwt", token]
        ),
    ):
        pytest.fail("revoked bearer was accepted by the WebSocket handshake")
    assert closed.value.code == 4401


def test_no_jti_token_remains_usable_after_logout(offline_auth):
    client, key, user_id, _, main = offline_auth
    token = signed_token(main, key, user_id, None)
    headers = {"Authorization": f"Bearer {token}"}
    assert client.post("/api/auth/logout", headers=headers).status_code == 200
    assert client.get("/api/auth/me", headers=headers).status_code == 200


def test_cookie_logout_requires_signed_csrf_and_rejects_reuse(offline_auth):
    client, key, user_id, _, main = offline_auth
    jti = "browser-fixture-jti"
    token = signed_token(main, key, user_id, jti)
    csrf = csrf_token(jti, key)
    client.cookies.set("apexgrid_session", token)
    client.cookies.set("apexgrid_csrf", csrf)
    headers = {"Origin": "http://localhost:3000", "X-CSRF-Token": csrf}
    response = client.post("/api/auth/logout", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"detail": "Logged out"}
    assert client.get("/api/auth/me").status_code == 401


def test_bad_csrf_does_not_record_revocation(offline_auth):
    client, key, user_id, revoked, main = offline_auth
    jti = "csrf-failure-fixture-jti"
    token = signed_token(main, key, user_id, jti)
    csrf = csrf_token(jti, key)
    client.cookies.set("apexgrid_session", token)
    client.cookies.set("apexgrid_csrf", csrf)
    response = client.post(
        "/api/auth/logout",
        headers={"Origin": "http://localhost:3000", "X-CSRF-Token": "invalid"},
    )
    assert response.status_code == 403
    assert jti not in revoked
