"""Seeded database characterization for auth and user API routes."""

from uuid import UUID, uuid4

import pytest
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def database_api_client():
    with TestClient(app) as client:
        yield client


def login(client, email, *, origin=None):
    headers = {"Origin": origin} if origin else {}
    return client.post(
        "/api/auth/login",
        json={"email": email, "password": "ApexGrid2026!"},
        headers=headers,
    )


def test_seeded_auth_login_me_logout_contract(database_api_client):
    client = database_api_client
    expected_user_keys = {"id", "email", "full_name", "role"}

    bearer_login = login(client, "admin@apexgrid.test")
    assert bearer_login.status_code == 200, bearer_login.text
    bearer_body = bearer_login.json()
    assert set(bearer_body) == {"access_token", "token_type", "user"}
    auth_scheme = bearer_body["token_type"]
    assert auth_scheme == "bearer"
    assert set(bearer_body["user"]) == expected_user_keys
    assert bearer_body["user"]["role"] == "ADMIN"

    bearer = {"Authorization": f"Bearer {bearer_body['access_token']}"}
    me = client.get("/api/auth/me", headers=bearer)
    assert me.status_code == 200
    assert me.json() == bearer_body["user"]
    logout = client.post("/api/auth/logout", headers=bearer)
    assert logout.status_code == 200
    assert logout.json() == {"detail": "Logged out"}

    browser_login = login(client, "driver01@apexgrid.test", origin="http://localhost:3000")
    assert browser_login.status_code == 200, browser_login.text
    browser_body = browser_login.json()
    assert set(browser_body) == {"user"}
    assert set(browser_body["user"]) == expected_user_keys
    assert browser_body["user"]["role"] == "DRIVER"

    client.cookies.clear()
    bad_login = client.post(
        "/api/auth/login",
        json={"email": "admin@apexgrid.test", "password": "wrong-password"},
    )
    assert bad_login.status_code == 401
    assert bad_login.json() == {"detail": "Invalid email or password"}
    anonymous_me = client.get("/api/auth/me")
    assert anonymous_me.status_code == 401
    assert anonymous_me.json() == {"detail": "Authentication required"}
    anonymous_logout = client.post("/api/auth/logout")
    assert anonymous_logout.status_code == 401


def test_user_routes_admin_driver_and_anonymous_contract(database_api_client):
    client = database_api_client
    admin_login = login(client, "admin@apexgrid.test")
    driver_login = login(client, "driver01@apexgrid.test")
    assert admin_login.status_code == driver_login.status_code == 200
    admin = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
    driver = {"Authorization": f"Bearer {driver_login.json()['access_token']}"}
    client.cookies.clear()
    new_id = str(uuid4())
    email = f"router-contract-{new_id}@apexgrid.test"
    authz_path = f"/api/users/{new_id}"
    path = authz_path
    create_body = {
        "email": email,
        "full_name": "Router Contract User",
        "password": "ContractPass2026!",
        "role": "DRIVER",
    }
    update_body = {"full_name": "Updated Router Contract User"}
    read_routes = [("GET", "/api/users", None), ("GET", authz_path, None)]
    write_routes = [
        ("POST", "/api/users", create_body),
        ("PATCH", authz_path, update_body),
        ("DELETE", authz_path, None),
    ]
    path = authz_path
    try:
        for method, route, body in read_routes + write_routes:
            assert client.request(method, route, headers=driver, json=body).status_code == 403
            assert client.request(method, route, json=body).status_code == 401

        created = client.post("/api/users", headers=admin, json=create_body)
        assert created.status_code == 201, created.text
        user = created.json()
        path = f"/api/users/{user['id']}"
        assert set(user) == {"id", "email", "full_name", "role"}
        assert str(UUID(user["id"])) == user["id"]
        assert {key: user[key] for key in ("email", "full_name", "role")} == {
            "email": email,
            "full_name": "Router Contract User",
            "role": "DRIVER",
        }
        listed = client.get("/api/users", headers=admin)
        assert listed.status_code == 200
        assert isinstance(listed.json(), list)
        assert user in listed.json()
        detail = client.get(path, headers=admin)
        assert detail.status_code == 200
        assert detail.json() == user

        updated = client.patch(path, headers=admin, json=update_body)
        assert updated.status_code == 200
        assert updated.json() == {**user, "full_name": update_body["full_name"]}
        deleted = client.delete(path, headers=admin)
        assert deleted.status_code == 204
        assert deleted.content == b""
        missing = client.get(path, headers=admin)
        assert missing.status_code == 404
        assert missing.json() == {"detail": "User not found"}
    finally:
        client.delete(path, headers=admin)
