import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Annotated, Any

import jwt
import pytest
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.auth_cookie import create_csrf_token
from backend.app.core import request_auth
from backend.app.core.request_auth import current_user, require_roles
from backend.app.core.request_database import DatabaseSession
from backend.app.core.runtime import RuntimeState

KEY = "unit-only-signing-key-for-tests-32-bytes"


class FakeCursor:
    def __init__(self, pool):
        self.pool = pool
        self.row = None

    def __enter__(self):
        self.pool.cursor_enters += 1
        return self

    def __exit__(self, *exc):
        self.pool.cursor_exits += 1

    def execute(self, sql, params):
        self.pool.queries.append((sql, params))
        self.row = self.pool.rows.pop(0)

    def fetchone(self):
        return self.row

    def fetchall(self):
        return self.row


class FakePool:
    closed = False

    def __init__(self, rows=()):
        self.rows = list(rows)
        self.queries = []
        self.enters = self.exits = self.cursor_enters = self.cursor_exits = 0

    @contextmanager
    def connection(self):
        self.enters += 1
        try:
            yield self
        finally:
            self.exits += 1

    def cursor(self):
        return FakeCursor(self)


def token(**claims):
    return jwt.encode({"sub": "user-7", "jti": "session-1", **claims}, KEY, algorithm="HS256")


def app(pool=None):
    application = FastAPI()
    application.state.runtime = RuntimeState(pool=pool)

    @application.get("/me")
    def me(request: Request, user: Annotated[dict[str, Any], Depends(current_user)]):
        return [user["id"], user["role"], request.state.auth_claims["sub"]]

    @application.post("/cookie")
    def cookie(user: Annotated[dict[str, Any], Depends(current_user)]):
        return user

    @application.get("/admin")
    def admin(user: Annotated[dict[str, Any], Depends(require_roles("admin"))]):
        return user

    return application


@pytest.fixture(autouse=True)
def auth_config(monkeypatch):
    monkeypatch.setattr(request_auth, "JWT_SECRET", KEY)
    monkeypatch.setattr(request_auth, "JWT_ALGORITHM", "HS256")
    monkeypatch.setattr(request_auth, "CORS_ORIGINS", ("https://app.test",))


def test_authentication_failures_and_pool_access_order():
    pool = FakePool()
    with TestClient(app(pool)) as client:
        missing = client.get("/me")
        malformed = client.get("/me", headers={"Authorization": "Bearer invalid"})
    assert missing.status_code == malformed.status_code == 401
    assert pool.queries == [] and pool.enters == 0
    revoked = FakePool([{"jti": "session-1"}])
    with TestClient(app(revoked)) as client:
        rejected = client.get("/me", headers={"Authorization": f"Bearer {token()}"})
    assert rejected.status_code == 401 and len(revoked.queries) == 1
    with TestClient(app()) as client:
        unavailable = client.get("/me", headers={"Authorization": f"Bearer {token()}"})
    assert unavailable.status_code == 503


def test_signed_bearer_uses_injected_pool_and_stores_claims():
    pool = FakePool([None, {"id": "user-7", "role": "member"}])
    with TestClient(app(pool)) as client:
        response = client.get("/me", headers={"Authorization": f"Bearer {token()}"})
    assert response.status_code == 200 and response.json() == ["user-7", "member", "user-7"]
    assert len(pool.queries) == 2 and pool.enters == pool.exits == 2
    assert tuple(query[0].split()[1] for query in pool.queries) == (
        "jti",
        "id,email,full_name,role",
    )


def test_cookie_post_requires_csrf_and_accepts_matching_token_and_origin():
    member = {"id": "user-7", "role": "member"}
    pool = FakePool([None, None, member, None, member])
    session = token()
    csrf = create_csrf_token("session-1", KEY)
    with TestClient(app(pool)) as client:
        missing = client.post("/cookie", cookies={"apexgrid_session": session})
        accepted = client.post(
            "/cookie",
            cookies={"apexgrid_session": session, "apexgrid_csrf": csrf},
            headers={"x-csrf-token": csrf, "origin": "https://app.test"},
        )
    assert missing.status_code == 403
    assert accepted.status_code == 200 and accepted.json()["role"] == "member"


def test_role_guard_and_fetch_all_copy_rows_and_balance_resources():
    source_rows = [{"id": "a"}, {"id": "b"}]
    pool = FakePool([None, {"id": "user-7", "role": "member"}, source_rows])
    with TestClient(app(pool)) as client:
        denied = client.get("/admin", headers={"Authorization": f"Bearer {token()}"})
    rows = DatabaseSession(pool).fetch_all("SELECT id FROM rows")
    assert denied.status_code == 403
    assert rows == [{"id": "a"}, {"id": "b"}] and rows[0] is not source_rows[0]
    assert pool.enters == pool.exits == pool.cursor_enters == pool.cursor_exits == 3
