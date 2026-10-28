# ApexGrid

A motorsport league and race operations platform with a PostgreSQL authoritative core, MongoDB telemetry, FastAPI, Next.js and WebSocket live timing. The interface uses a light Neo-brutalist design system (cream, paper, ink, yellow and red tokens, hard shadows, motion limited to transform and opacity with reduced-motion support). Overhaul scope and acceptance are in `docs/overhaul-plan.md`, `docs/completion-plan.md` and the ADRs in `.agent/adr/`.

## Setup

The supported way to run ApexGrid is Docker Compose. It starts four services from `compose.yaml`: PostgreSQL 16, MongoDB 7, the FastAPI backend (Python 3.12) and the Next.js frontend (Node 22). You do not need Python, Node, PostgreSQL or MongoDB on your machine unless you want to run tests or develop outside containers.

### What you need

| | Required to run | Required to develop and test |
|---|---|---|
| Git | yes | yes |
| Docker with Compose v2 (`docker compose`, not `docker-compose`) | yes | yes |
| Node.js 22 and npm | no | yes (frontend, Playwright) |
| Python 3.12 | no | yes (backend tests, lint, type checks) |

Docker needs about 4 GB of memory and 5 GB of free disk for the images and volumes. Ports `3000`, `8000`, `5432` and `27017` must be free (the database ports bind to `127.0.0.1` only).

### macOS (Apple silicon or Intel)

1. Install the Xcode command line tools, which provide Git:
   ```bash
   xcode-select --install
   ```
2. Install Docker Desktop from <https://www.docker.com/products/docker-desktop/>, or with Homebrew:
   ```bash
   brew install --cask docker
   ```
   Open Docker Desktop once and wait until it reports that the engine is running. In **Settings → Resources**, give it at least 4 GB of memory.
3. Clone and start:
   ```bash
   git clone https://github.com/madhavchoudhary2007-netizen/dbmsproj.git
   cd dbmsproj
   cp .env.example .env
   docker compose up --build
   ```
4. For development tools (optional):
   ```bash
   brew install node@22 python@3.12
   ```

If port 5432 or 27017 is taken by a Homebrew PostgreSQL or MongoDB, stop it with `brew services stop postgresql@16` / `brew services stop mongodb-community`, or change the left-hand port in `compose.yaml`.

### Windows 10/11

ApexGrid runs on Windows through Docker Desktop with the WSL 2 backend. Running the commands inside a WSL Ubuntu shell is recommended: it avoids line-ending problems in the shell scripts and gives much faster file access.

1. In an **administrator PowerShell**, install WSL 2 with Ubuntu, then restart:
   ```powershell
   wsl --install -d Ubuntu
   ```
2. Install Docker Desktop from <https://www.docker.com/products/docker-desktop/> (or `winget install -e --id Docker.DockerDesktop`). In **Settings → General**, keep **Use the WSL 2 based engine** on; in **Settings → Resources → WSL integration**, enable your Ubuntu distribution.
3. Open the **Ubuntu** terminal and clone into the Linux file system (for example your home directory, not `/mnt/c/...`):
   ```bash
   sudo apt update && sudo apt install -y git
   git clone https://github.com/madhavchoudhary2007-netizen/dbmsproj.git
   cd dbmsproj
   cp .env.example .env
   docker compose up --build
   ```
4. Open <http://localhost:3000> in your Windows browser; WSL forwards localhost automatically.

If you prefer plain PowerShell instead of WSL, install Git for Windows (`winget install -e --id Git.Git`) and run, from the cloned folder:
```powershell
git config core.autocrlf input
Copy-Item .env.example .env
docker compose up --build
```
Set `core.autocrlf input` before cloning (or re-clone after setting it globally with `git config --global core.autocrlf input`); Windows line endings break the container start scripts. The `scripts/eval/*.sh` quality gates need bash, so run them from WSL or Git Bash.

If a port is in use, find the process with `netstat -ano | findstr :5432` and stop it, or change the left-hand port in `compose.yaml`.

### Linux (Ubuntu/Debian; Fedora notes below)

1. Install Docker Engine and the Compose plugin from Docker's repository (the distribution's `docker.io` package often lacks Compose v2). Follow <https://docs.docker.com/engine/install/> for your distribution; on Ubuntu:
   ```bash
   sudo apt update && sudo apt install -y ca-certificates curl git
   sudo install -m 0755 -d /etc/apt/keyrings
   sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
   echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list
   sudo apt update && sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
   ```
   On Fedora: `sudo dnf install -y dnf-plugins-core git && sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo && sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin && sudo systemctl enable --now docker`.
2. Let your user run Docker without `sudo`, then log out and back in:
   ```bash
   sudo usermod -aG docker "$USER"
   ```
3. Clone and start:
   ```bash
   git clone https://github.com/madhavchoudhary2007-netizen/dbmsproj.git
   cd dbmsproj
   cp .env.example .env
   docker compose up --build
   ```
4. For development tools (optional), install Node 22 (for example from <https://nodejs.org> or `nvm install 22`) and Python 3.12 (`sudo apt install python3.12 python3.12-venv`, or `pyenv`).

If a system PostgreSQL or MongoDB already holds the port, stop it (`sudo systemctl stop postgresql mongod`) or change the left-hand port in `compose.yaml`.

### After the containers start

- App: <http://localhost:3000> · API docs: <http://localhost:8000/docs> · health: <http://localhost:8000/api/health>
- Sign in with a demo account below.
- Run detached with `docker compose up --build -d`; follow logs with `docker compose logs -f backend`.
- Stop with `docker compose down`. Add `-v` to also delete the database volumes and start fresh.

`.env` controls the stack. The default `APP_ENV=local` is for the local demo; set a strong `JWT_SECRET` and a non-local `APP_ENV` for any shared environment. Set `CORS_ORIGINS` to the frontend origin if it differs from `http://localhost:3000`, and `NEXT_PUBLIC_API_URL` if the API is not at `http://localhost:8000` (it is baked into the frontend image, so rebuild after changing it).

The backend bootstrap reapplies the idempotent schema migration and seeds fictional data on startup. Set `SEED_DEMO_DATA=0` in `.env` to skip both SQL demo fixtures and historical lap telemetry while still applying migrations. PostgreSQL data and MongoDB telemetry persist in named Docker volumes.

### Development environment (all platforms)

On macOS and Linux use the commands as written; on Windows run them in WSL.

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r backend/requirements-dev.txt
cd frontend && npm ci && npx playwright install --with-deps chromium && cd ..
```

Run backend tests as `.venv/bin/python -m pytest` (not the bare `pytest` script) so the package-identity guard in `backend/app/__init__.py` passes. Stop any local API that uses the same database first: the backend holds a single runtime-ownership lease per database.

### Troubleshooting

| Symptom | Fix |
|---|---|
| `docker: 'compose' is not a docker command` | Install the Compose v2 plugin (`docker-compose-plugin`) or update Docker Desktop. |
| `port is already allocated` | Another service holds 3000, 8000, 5432 or 27017; stop it or change the host port in `compose.yaml`. |
| Backend restarts with a runtime ownership error | A second backend is using the same database. Stop the other one (only one backend process per database is supported). |
| Login succeeds but pages show signed-out | The browser and API must share a host name: open `http://localhost:3000` (not `127.0.0.1`) while `NEXT_PUBLIC_API_URL` is `http://localhost:8000`. |
| `exec ... no such file or directory` in a container on Windows | The repository was checked out with CRLF line endings; set `core.autocrlf input` and re-clone. |
| Frontend build fails after changing `.env` | Rebuild the image: `docker compose build --no-cache frontend`. |

## Routes

Sixteen routes: `/` (landing), `/login`, `/dashboard`, `/live`, `/sessions`, `/stewards`, `/pit-wall`, `/championships`, `/events`, `/circuits`, `/standings`, `/teams`, `/drivers`, `/users`, `/analytics` and `/dbms` (DBMS operations and the PostgreSQL/MongoDB showcase). `/%5F_nb` is the design-primitives guide used by guide-mode tests.

## Demo accounts

| Role | Email | Password |
|---|---|---|
| Admin | `admin@apexgrid.test` | `ApexGrid2026!` |
| Steward | `steward@apexgrid.test` | `ApexGrid2026!` |
| Team principal | `principal@apexgrid.test` | `ApexGrid2026!` |

These are local demonstration credentials. Replace the seed and JWT secret before any shared deployment.

## Quality gates

| Gate | Command |
|---|---|
| Disposable stack (Postgres 15432, Mongo 27018) | `bash scripts/eval/test-stack.sh up` / `down` |
| Backend suite, coverage (80% minimum), owned live acceptance | `bash scripts/eval/db-baseline.sh` |
| Frontend typecheck, lint, build | `cd frontend && npm run typecheck && npm run build` |
| Browser matrix (5 viewports) | `cd frontend && npx --no-install playwright test` |
| Visual baselines (375 and 1440) | `cd frontend && PLAYWRIGHT_MODE=visual CI=1 npx --no-install playwright test e2e/visual-regression.spec.ts` |
| Real-stack journeys | `PLAYWRIGHT_MODE=real-stack PLAYWRIGHT_REAL_STACK_API_URL=http://localhost:18000 APEXGRID_E2E_OWNED_DISPOSABLE=1 npx --no-install playwright test` with the API on port 18000 (use `localhost`, not `127.0.0.1`, so the session cookie is same-site) |
| Design lints | `scripts/eval/lint-*.sh` |

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
DATABASE_URL=postgresql://apexgrid:apexgrid@localhost:5432/apexgrid MONGODB_URL=mongodb://localhost:27017 .venv/bin/python -m pytest -q backend/tests
DATABASE_URL=postgresql://apexgrid:apexgrid@localhost:5432/apexgrid MONGODB_URL=mongodb://localhost:27017 python scripts/acceptance.py
cd frontend && npm ci && npm run typecheck && npm run build
```

The acceptance script exercises the API, WebSocket, PostgreSQL trigger and lock conflict, MongoDB telemetry, standings and DBMS operations. For cleanup of acceptance-owned test records, its isolated fixture transaction temporarily disables the production `trg_penalties_immutable` trigger, re-enables it before commit, and checks that it is enabled after cleanup.

## Simulation and external telemetry

Sign in as admin and select or create a live race. Generated races start their simulator immediately; for a manually created session, start the session and simulator from Sessions. Open Live Timing to see MongoDB samples and WebSocket timing. Pause, resume and stop controls for manually simulated sessions are on the session view. The same normalized packet can be posted by an external provider to `POST /api/telemetry/ingest` for an active session with an admin or steward Bearer token; see `docs/contracts.md` and `/docs` for the payload.

## Instant live demo races

With `AUTO_DEMO_RACE=1`, ApexGrid starts a generated live race when the backend boots. Admins and stewards can also click **Create live race** to start one immediately, with a random 8–16 car grid of fictional named drivers, unique licences and car numbers, varied pace, and a race capped at 72 laps. Select a generated race from the list to follow its positions, gaps, per-driver sectors, completed lap times, incidents, pit stops and telemetry. The list also has a **Delete** action that removes only that generated race and its telemetry. When automatic race creation is enabled, completed races remain archived and a new generated session starts. The ordinary seeded championship records remain separate.

For generated races, Pit Wall shows each driver's tire age and wear, recommended stop lap and window, automatic box assignment, and completed stop history. The simulator schedules stops as tires age; operators do not need to request or close them. Allocations and pit states also appear in the Live Timing stream and DBMS race explorer. The manual reservation API remains available for non-generated sessions.

The supplied `.env.example` enables an automatic repeating race. Set `AUTO_DEMO_RACE=0` to start races only when created from the UI. Creating a live race does not require changing the setting.

### Race database explorer

At `/dbms`, grouped one-click navigation opens live PostgreSQL status, running and completed race archives, all 17 actual public base tables, the EER diagram, schema, indexes, query plans, locks, database operations, MongoDB collections, and cross-store results. PostgreSQL table counts and rows come from the database; there are no public SQL `VIEW` objects. MongoDB shows the actual telemetry collection, document counts and index definitions, with filtered, paged documents and a raw JSON inspector. The selected view is encoded in the URL hash, so links open a view directly and browser Back/Forward restores navigation. Status and read-only views refresh automatically; the global Refresh control also refreshes the selected race database view. The SQL table browser hides password hashes. Race records refresh every second while active; completed races retain final classifications, telemetry, incidents, pit stops, a two-driver comparison and every-driver lap/sector history. The two original completed fixtures have explicitly labeled historical demo lap archives; generated completed races retain their actual simulator data across restarts.


## Engineering workflow

The active overhaul scope is [the twelve-phase plan](docs/overhaul-plan.md). Current verified status and execution permission live in [.agent/CURRENT_STATE.md](.agent/CURRENT_STATE.md) and [.agent/NEXT_STATE.md](.agent/NEXT_STATE.md). Follow [AGENTS.md](AGENTS.md) and the [delivery workflow](.agent/protocol/delivery-workflow.md); historical project snapshots and loop logs are not current completion evidence.

Antigravity execution contract: [.agent/protocol/antigravity.md](.agent/protocol/antigravity.md) — Gemini 3.8 Flash HIGH orchestrator / LOW workers, maximum two workers. Record observed UI settings or UNVERIFIED; declarations do not prove model binding. Current permission and evidence remain in the state files and latest owner instruction.

Document roles and retired instructions: [.agent/DOC_AUTHORITY.md](.agent/DOC_AUTHORITY.md). Operator commands here are not authorization for an agent to write real databases or restart setup.
