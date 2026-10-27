from __future__ import annotations

from collections.abc import Iterator
import os
from pathlib import Path
import sys
from typing import Any

import jwt
import pytest
from fastapi.testclient import TestClient

SESSION_ID = "synthetic-showcase-session"
TEST_SECRET = "synthetic-test-secret-for-showcase"
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
_prior_app_env = os.environ.get("APP_ENV")
os.environ.setdefault("APP_ENV", "local")
try:
    import backend.app.config as app_config
    import backend.app.core.request_auth as request_auth
    import backend.app.main as main_module
    from backend.app.api import dbms_showcase
    from backend.app.api.laps import current_user, get_race_telemetry
    from backend.app.main import app
finally:
    if _prior_app_env is None:
        os.environ.pop("APP_ENV", None)
    else:
        os.environ["APP_ENV"] = _prior_app_env


GAPS_URL = "/api/analytics/gaps?session_id=00000000-0000-0000-0000-000000000001"
SENSITIVE_ROUTES = (
    ("GET", "/api/dbms/isolation-demo"),
    ("GET", "/api/dbms/audit"),
    ("GET", "/api/dbms/security"),
    ("GET", "/api/dbms/views"),
    ("GET", GAPS_URL),
    ("POST", "/api/dbms/deadlock-demo"),
    ("POST", "/api/dbms/refresh-standings-mv"),
)


@pytest.fixture
def client() -> Iterator[TestClient]:
    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides.clear()
    app.dependency_overrides[get_race_telemetry] = lambda: _EmptyTelemetry()
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)


class _EmptyTelemetry:
    def aggregate(self, _pipeline: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return []


def _as_role(role: str) -> None:
    app.dependency_overrides[current_user] = lambda: {
        "id": f"synthetic-{role.lower()}-user",
        "email": f"{role.lower()}@example.invalid",
        "role": role,
    }


class _Cursor:
    def __init__(self, rows: list[dict[str, Any]] | None = None, *, error: Exception | None = None):
        self.rows = rows or []
        self.error = error
        self.executed: list[str] = []

    def __enter__(self) -> _Cursor:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def execute(self, sql: str, params: object = None) -> None:
        self.executed.append(sql)
        if self.error:
            raise self.error

    def fetchall(self) -> list[dict[str, Any]]:
        return self.rows


class _Connection:
    def __init__(self, cursor: _Cursor):
        self._cursor = cursor
        self.autocommit = False

    def __enter__(self) -> _Connection:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def cursor(self, *args: object, **kwargs: object) -> _Cursor:
        return self._cursor


def _install_connection(monkeypatch: pytest.MonkeyPatch, cursor: _Cursor) -> None:
    monkeypatch.setattr(dbms_showcase, "connection", lambda: _Connection(cursor))


def _request(client: TestClient, method: str, path: str):
    return client.request(method, path)


@pytest.mark.parametrize(("method", "path"), SENSITIVE_ROUTES)
def test_sensitive_showcase_routes_reject_anonymous(
    client: TestClient, method: str, path: str
) -> None:
    response = _request(client, method, path)
    assert response.status_code == 401


@pytest.mark.parametrize(("method", "path"), SENSITIVE_ROUTES)
def test_sensitive_showcase_routes_reject_non_admin(
    client: TestClient, method: str, path: str
) -> None:
    _as_role("USER")
    response = _request(client, method, path)
    assert response.status_code == 403, response.text


@pytest.mark.parametrize(("method", "path"), SENSITIVE_ROUTES)
def test_admin_can_reach_showcase_handlers(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, method: str, path: str
) -> None:
    _as_role("ADMIN")
    if path == "/api/dbms/isolation-demo":
        monkeypatch.setattr(
            dbms_showcase,
            "run_isolation_demo",
            lambda _connection, level: {
                "level": level,
                "observed_reads": [
                    {"step": "T1: Initial read", "balance": 1000},
                    {"step": "T1: Read after T2 commit", "balance": 1500},
                ],
                "anomaly_detected": True,
                "anomaly_type": "Non-repeatable Read (Fuzzy Read)",
                "timeline": [],
            },
        )
    elif path == "/api/dbms/deadlock-demo":
        monkeypatch.setattr(
            dbms_showcase,
            "run_deadlock_demo",
            lambda _connection: {
                "aborted_transaction": "T2",
                "sqlstate": "40P01",
                "error_message": "synthetic controlled deadlock",
                "details": {},
            },
        )
    else:
        _install_connection(monkeypatch, _Cursor())
    response = _request(client, method, path)
    assert response.status_code == 200


@pytest.mark.parametrize(
    ("method", "path"),
    (("POST", "/api/dbms/deadlock-demo"), ("POST", "/api/dbms/refresh-standings-mv")),
)
@pytest.mark.parametrize("csrf_mode", ["missing", "invalid"])
def test_cookie_authenticated_posts_require_csrf(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    method: str,
    path: str,
    csrf_mode: str,
) -> None:
    monkeypatch.setattr(request_auth, "JWT_SECRET", TEST_SECRET)
    monkeypatch.setattr(request_auth, "JWT_ALGORITHM", "HS256")
    monkeypatch.setattr(app_config, "JWT_SECRET", TEST_SECRET)
    monkeypatch.setattr(app_config, "JWT_ALGORITHM", "HS256")
    monkeypatch.setattr(main_module, "JWT_SECRET", TEST_SECRET)
    monkeypatch.setattr(request_auth, "token_is_revoked", lambda *args, **kwargs: False)
    authenticate = request_auth.authenticate_http_user

    def authenticate_with_synthetic_storage(request, credentials, **kwargs):
        kwargs["_token_is_revoked"] = lambda *args, **options: False
        kwargs["fetch_one"] = lambda *args, **options: {
            "id": "synthetic-cookie-user",
            "email": "cookie@example.invalid",
            "full_name": "Synthetic Cookie User",
            "role": "ADMIN",
        }
        return authenticate(request, credentials, **kwargs)

    monkeypatch.setattr(request_auth, "authenticate_http_user", authenticate_with_synthetic_storage)
    token = jwt.encode(
        {"sub": "synthetic-cookie-user", "jti": SESSION_ID}, TEST_SECRET, algorithm="HS256"
    )
    client.cookies.set("apexgrid_session", token)
    client.headers["origin"] = next(iter(app_config.CORS_ORIGINS))
    if csrf_mode == "invalid":
        client.cookies.set("apexgrid_csrf", "invalid-synthetic-csrf")
        client.headers["x-csrf-token"] = "invalid-synthetic-csrf"
    response = _request(client, method, path)
    assert response.status_code == 403, response.text
    assert response.json()["detail"] == "CSRF validation failed"


@pytest.mark.parametrize(
    ("method", "path"),
    (
        ("GET", "/api/dbms/audit"),
        ("GET", "/api/dbms/views"),
        ("GET", GAPS_URL),
        ("POST", "/api/dbms/refresh-standings-mv"),
    ),
)
def test_database_errors_return_server_errors(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, method: str, path: str
) -> None:
    _as_role("ADMIN")
    _install_connection(monkeypatch, _Cursor(error=RuntimeError("synthetic database failure")))
    response = _request(client, method, path)
    assert 500 <= response.status_code < 600


def test_empty_database_results_do_not_create_sample_rows(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _as_role("ADMIN")
    _install_connection(monkeypatch, _Cursor())
    audit = client.get("/api/dbms/audit")
    views = client.get("/api/dbms/views")
    gaps = client.get(GAPS_URL)
    assert audit.status_code == views.status_code == gaps.status_code == 200
    assert audit.json()["audit_logs"] == []
    assert audit.json()["total"] == 0
    assert views.json()["views"] == []
    assert gaps.json()["gaps"] == []


def test_refresh_reports_success_only_after_refresh_sql_executes(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _as_role("ADMIN")
    cursor = _Cursor()
    _install_connection(monkeypatch, cursor)
    response = client.post("/api/dbms/refresh-standings-mv")
    assert response.status_code == 200
    assert response.json()["refreshed"] is True
    assert any("REFRESH MATERIALIZED VIEW" in sql for sql in cursor.executed)
