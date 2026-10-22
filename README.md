# ApexGrid

A motorsport league and race operations platform with a PostgreSQL authoritative core, MongoDB telemetry, FastAPI, Next.js and WebSocket live timing. The two ApexGrid presentations in the user's Downloads directory define the product and DBMS demonstration scope.

## Start

1. Copy `.env.example` to `.env`. The default `APP_ENV=local` is for the local demo; set a strong `JWT_SECRET` and a non-local `APP_ENV` for any shared environment. Set `CORS_ORIGINS` to the frontend origin if it differs from `http://localhost:3000`.
2. Run `docker compose up --build`.
3. Open [ApexGrid](http://localhost:3000) and [API docs](http://localhost:8000/docs).

The backend bootstrap reapplies the idempotent schema migration and seeds fictional data on startup. Set `SEED_DEMO_DATA=0` in `.env` to skip both SQL demo fixtures and historical lap telemetry while still applying migrations. PostgreSQL data and MongoDB telemetry persist in named Docker volumes. Their host ports bind to loopback for local development.

## Demo accounts

| Role | Email | Password |
|---|---|---|
| Admin | `admin@apexgrid.test` | `ApexGrid2026!` |
| Steward | `steward@apexgrid.test` | `ApexGrid2026!` |
| Team principal | `principal@apexgrid.test` | `ApexGrid2026!` |

These are local demonstration credentials. Replace the seed and JWT secret before any shared deployment.

## Architecture

- `frontend/`: Next.js operational interface
- `backend/app/`: FastAPI API, auth, simulation and database adapters
- `backend/migrations/`: PostgreSQL schema and stored logic
- `backend/db/`: demo seed
- `docs/contracts.md`: shared wire and state contract

PostgreSQL owns official entities and rules. MongoDB stores telemetry documents keyed by shared UUIDs. The WebSocket stream delivers normalized events to the live pit wall.

Live simulation and WebSocket delivery run in one backend process per PostgreSQL database. The supplied Compose service starts one Uvicorn worker; a second backend process using the same database fails startup. If the runtime ownership connection is lost, HTTP returns 503, WebSockets close, and simulators stop. Restart the backend after PostgreSQL recovers. Do not increase the worker or replica count without shared simulation leadership and event delivery.

## Development checks

Run `docker compose config` to check Compose. Backend migration and seed can also be run directly with:

```bash
docker compose exec -T postgres psql -U apexgrid -d apexgrid -v ON_ERROR_STOP=1 -f /dev/stdin < backend/migrations/001_initial.sql
docker compose exec -T postgres psql -U apexgrid -d apexgrid -v ON_ERROR_STOP=1 -f /dev/stdin < backend/db/seed.sql
```

To run the integration suite locally, create a Python virtual environment and install `backend/requirements-dev.txt`, then run:

```bash
DATABASE_URL=postgresql://apexgrid:apexgrid@localhost:5432/apexgrid MONGODB_URL=mongodb://localhost:27017 pytest -q backend/tests
DATABASE_URL=postgresql://apexgrid:apexgrid@localhost:5432/apexgrid MONGODB_URL=mongodb://localhost:27017 python scripts/acceptance.py
cd frontend && npm ci && npm run typecheck && npm run build
```

The acceptance script exercises the API, WebSocket, PostgreSQL trigger and lock conflict, MongoDB telemetry, standings and DBMS operations. For cleanup of acceptance-owned test records, its isolated fixture transaction temporarily disables the production `trg_penalties_immutable` trigger, re-enables it before commit, and checks that it is enabled after cleanup.

## Simulation and external telemetry

Sign in as admin and select or create a live race. Generated races start their simulator immediately; for a manually created session, start the session and simulator from Sessions. Open Live Timing to see MongoDB samples and WebSocket timing. Pause, resume and stop controls for manually simulated sessions are on the session view. The same normalized packet can be posted by an external provider to `POST /api/telemetry/ingest` for an active session with an admin or steward Bearer token; see `docs/contracts.md` and `/docs` for the payload.

## Instant live demo races

With `AUTO_DEMO_RACE=1`, ApexGrid starts a generated live race when the backend boots. Admins and stewards can also click **Create live race** to start one immediately, with a random 8–16 car grid of fictional named drivers, unique licences and car numbers, varied pace, and a race capped at 72 laps. Select a generated race from the list to follow its positions, gaps, per-driver sectors, completed lap times, incidents, pit stops and telemetry. The list also has a **Delete** action that removes only that generated race and its telemetry. When automatic race creation is enabled, completed races remain archived and a new generated session starts. The ordinary seeded championship records remain separate.

For generated races, Pit Wall shows each driver's tire age and wear, recommended stop lap and window, automatic box assignment, and completed stop history. The simulator schedules stops as tires age; operators do not need to request or close them. Allocations and pit states also appear in the Live Timing stream and DBMS race explorer. The manual reservation API remains available for non-generated sessions.

The supplied `.env.example` enables an automatic repeating race. Set `AUTO_DEMO_RACE=0` to start races only when created from the UI. The current local `.env` uses `AUTO_DEMO_RACE=0` and `SEED_DEMO_DATA=0`; it has two completed generated race archives and no live race. The newest archive (session `87049420-8e98-4fd6-95a0-cc8de6340d74`) has 8 drivers, exactly 60 laps per driver (480 total), 8 official results, 3 incidents, 19 completed automatic pit stops, and 2,784 MongoDB samples. The earlier archive has 9 drivers, 495 completed laps, 22 completed pit stops, 3 incidents, and 2,916 MongoDB samples. All four services are healthy. Creating a live race does not require changing the setting.

See `PROJECT_STATE.md` for verified feature and test status.

### Race database explorer

At `/dbms`, grouped one-click navigation opens live PostgreSQL status, running and completed race archives, all 17 actual public base tables, the EER diagram, schema, indexes, query plans, locks, database operations, MongoDB collections, and cross-store results. PostgreSQL table counts and rows come from the database; there are no public SQL `VIEW` objects. MongoDB shows the actual telemetry collection, document counts and index definitions, with filtered, paged documents and a raw JSON inspector. The selected view is encoded in the URL hash, so links open a view directly and browser Back/Forward restores navigation. Status and read-only views refresh automatically; the global Refresh control also refreshes the selected race database view. The SQL table browser hides password hashes. Race records refresh every second while active; completed races retain final classifications, telemetry, incidents, pit stops, a two-driver comparison and every-driver lap/sector history. The two original completed fixtures have explicitly labeled historical demo lap archives; generated completed races retain their actual simulator data across restarts.
