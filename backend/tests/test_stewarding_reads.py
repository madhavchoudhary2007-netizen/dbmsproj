from datetime import UTC, datetime
from uuid import uuid4

import pytest
from app.core.request_auth import current_user
from app.core.request_database import get_database
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

PENALTY = ("id", "incident_id", "driver_id", "driver_name", "session_id", "lap") + (
    "points",
    "time_seconds",
    "grid_places",
    "created_at",
)
LICENCE = ("driver_id", "driver_name", "licence_number", "eligibility", "season", "points")


def row(fields, *values):
    return dict(zip(fields, values, strict=True))


class FakeDatabase:
    def __init__(self, rows=(), error=None):
        self.rows, self.error, self.calls = list(rows), error, []

    def fetch_all(self, sql, params):
        self.calls.append((sql, params))
        if self.error:
            raise self.error
        return self.rows


@pytest.fixture
def client_factory():
    apps = []

    def make(database):
        from app.api.stewarding_reads import router

        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[current_user] = lambda: {"id": "viewer", "role": "steward"}
        app.dependency_overrides[get_database] = lambda: database
        apps.append(app)
        return TestClient(app)

    yield make
    for app in apps:
        app.dependency_overrides.clear()


def test_penalties_contract_pagination_and_select_order(client_factory):
    ids = tuple(uuid4() for _ in range(4))
    created = datetime(2026, 4, 3, 12, 5, tzinfo=UTC)
    database = FakeDatabase([row(PENALTY, *ids[:3], None, ids[3], 7, 2, 3, 1, created)])
    with client_factory(database) as client:
        response = client.get("/api/stewarding/penalties?limit=17&offset=4")
    assert response.status_code == 200
    item = response.json()[0]
    assert item == row(
        PENALTY,
        *(str(value) for value in ids[:3]),
        None,
        str(ids[3]),
        7,
        2,
        3,
        1,
        "2026-04-03T12:05:00Z",
    )
    assert isinstance(item["points"], int) and isinstance(item["time_seconds"], int)
    sql, params = database.calls[0]
    assert params == (17, 4) and sql.lstrip().upper().startswith("SELECT")
    assert all(term in sql.upper() for term in ("ORDER BY", "CREATED_AT DESC", "ID DESC"))
    assert not any(word in sql.upper() for word in ("INSERT ", "UPDATE ", "DELETE ", "UPSERT "))


def test_licences_season_points_eligibility_and_bound_defaults(client_factory):
    driver_id, year = uuid4(), datetime.now(UTC).year
    database = FakeDatabase([row(LICENCE, driver_id, None, "L-7", "eligible", year, 13)])
    with client_factory(database) as client:
        response = client.get("/api/stewarding/licences?limit=17&offset=4")
    assert response.status_code == 200
    item = response.json()[0]
    assert item == row(LICENCE, str(driver_id), None, "L-7", "eligible", year, 13)
    assert isinstance(item["points"], int) and database.calls[0][1] == (year, year, 17, 4)
    sql = database.calls[0][0].upper()
    assert sql.lstrip().startswith("SELECT") and "D.ID ASC" in sql
    assert not any(word in sql for word in ("INSERT ", "UPDATE ", "DELETE ", "UPSERT "))

    database = FakeDatabase([row(LICENCE, driver_id, "Driver", "L-7", "suspended", 2021, 0)])
    with client_factory(database) as client:
        history = client.get("/api/stewarding/licences?season=2021")
    assert history.status_code == 200
    assert history.json() == [row(LICENCE, str(driver_id), "Driver", "L-7", "suspended", 2021, 0)]
    assert database.calls[0][1] == (2021, 2021, 50, 0)


def test_empty_reads_return_arrays_with_default_pagination(client_factory):
    database = FakeDatabase()
    with client_factory(database) as client:
        penalties = client.get("/api/stewarding/penalties")
        licences = client.get("/api/stewarding/licences")
    assert penalties.status_code == licences.status_code == 200
    assert penalties.json() == licences.json() == []
    assert all(params[-2:] == (50, 0) for _, params in database.calls)


@pytest.mark.parametrize("path", ["penalties", "licences"])
@pytest.mark.parametrize("query", ["limit=0", "limit=201", "offset=-1"])
def test_invalid_pagination_is_422_without_query(client_factory, path, query):
    database = FakeDatabase()
    with client_factory(database) as client:
        response = client.get(f"/api/stewarding/{path}?{query}")
    assert response.status_code == 422 and database.calls == []


@pytest.mark.parametrize("season", [0, 10000])
def test_invalid_season_is_422_without_query(client_factory, season):
    database = FakeDatabase()
    with client_factory(database) as client:
        response = client.get(f"/api/stewarding/licences?season={season}")
    assert response.status_code == 422 and database.calls == []


def test_auth_and_provider_failures(client_factory):
    database = FakeDatabase()
    client = client_factory(database)
    client.app.dependency_overrides[current_user] = lambda: (_ for _ in ()).throw(
        HTTPException(401)
    )
    with client:
        for path in ("penalties", "licences"):
            response = client.get(f"/api/stewarding/{path}")
            assert response.status_code == 401
    assert database.calls == []
    unavailable = FakeDatabase(error=HTTPException(503))
    with client_factory(unavailable) as client:
        response = client.get("/api/stewarding/licences")
    assert response.status_code == 503 and len(unavailable.calls) == 1
