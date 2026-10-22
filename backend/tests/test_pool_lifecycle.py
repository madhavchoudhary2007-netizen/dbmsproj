"""Expected-failure regression for the module-global PostgreSQL pool lifecycle."""

from app.main import app
from fastapi.testclient import TestClient


def test_postgres_pool_reopens_across_sequential_lifespans():
    for lifespan_number in (1, 2):
        with TestClient(app) as client:
            response = client.get("/api/health")

        assert response.status_code == 200, response.text
        assert response.json()["services"]["postgres"] == "up", (
            f"PostgreSQL was down during lifespan {lifespan_number}: {response.text}"
        )
