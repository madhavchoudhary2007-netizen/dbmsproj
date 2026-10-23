import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


@pytest.fixture
def app_client(monkeypatch):
    monkeypatch.setenv("APP_ENV", "local")
    from backend.app import main

    monkeypatch.setattr(main.app.state, "runtime_lease", None, raising=False)
    return TestClient(main.app)


@pytest.mark.parametrize("path", ["/docs", "/redoc", "/docs/oauth2-redirect"])
def test_documentation_html_keeps_legacy_security_headers(app_client, path):
    response = app_client.get(path)

    assert response.status_code == 200
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert "content-security-policy" not in response.headers, (
        "AssertionError: documentation HTML must not carry the API CSP"
    )


def test_api_json_keeps_strict_content_security_policy(app_client):
    response = app_client.get("/api/missing-security-test")

    assert response.status_code == 404
    assert response.headers.get("content-security-policy") == (
        "default-src 'none'; frame-ancestors 'none'"
    )
