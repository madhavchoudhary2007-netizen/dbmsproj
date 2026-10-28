# ApexGrid

ApexGrid is a motorsport league and race operations platform. It manages championships, teams, drivers, events and sessions; shows live timing and car telemetry during a race; and handles steward penalties, pit-lane bookings, results and championship standings. PostgreSQL holds the official record and enforces the rules with constraints, triggers and stored functions, MongoDB stores high-rate telemetry, a FastAPI backend runs the race simulator and streams updates over WebSockets, and a Next.js frontend presents it all. An admin-only DBMS workspace inspects both databases live.

How it works, who uses it and why it is built this way: [ARCHITECTURE.md](ARCHITECTURE.md).

## Contents

- [Setup option A: Docker (recommended)](#setup-option-a-docker-recommended)
- [Setup option B: without Docker](#setup-option-b-without-docker)
- [Development environment](#development-environment-all-platforms)
- [Demo accounts](#demo-accounts)
- [Routes](#routes)
- [Quality gates](#quality-gates)

## Setup option A: Docker (recommended)

Docker Compose starts four services from `compose.yaml`: PostgreSQL 16, MongoDB 7, the FastAPI backend (Python 3.12) and the Next.js frontend (Node 22). You need only Git and Docker; Python, Node, PostgreSQL and MongoDB stay inside the containers.

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
   git clone -b overhaul/neo-brutal https://github.com/madhavchoudhary2007-netizen/dbmsproj.git
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
   git clone -b overhaul/neo-brutal https://github.com/madhavchoudhary2007-netizen/dbmsproj.git
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
   git clone -b overhaul/neo-brutal https://github.com/madhavchoudhary2007-netizen/dbmsproj.git
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

### Troubleshooting (Docker)

| Symptom | Fix |
|---|---|
| `docker: 'compose' is not a docker command` | Install the Compose v2 plugin (`docker-compose-plugin`) or update Docker Desktop. |
| `port is already allocated` | Another service holds 3000, 8000, 5432 or 27017; stop it or change the host port in `compose.yaml`. |
| Backend restarts with a runtime ownership error | A second backend is using the same database. Stop the other one (only one backend process per database is supported). |
| Login succeeds but pages show signed-out | The browser and API must share a host name: open `http://localhost:3000` (not `127.0.0.1`) while `NEXT_PUBLIC_API_URL` is `http://localhost:8000`. |
| `exec ... no such file or directory` in a container on Windows | The repository was checked out with CRLF line endings; set `core.autocrlf input` and re-clone. |
| Frontend build fails after changing `.env` | Rebuild the image: `docker compose build --no-cache frontend`. |

## Setup option B: without Docker

This runs the same four parts that `compose.yaml` starts, directly on your machine: PostgreSQL, MongoDB, the FastAPI backend and the Next.js frontend. It takes about 10 minutes, mostly downloads.

You install four programs, create one database, then start the backend and frontend in two terminals.

| Program | Version |
|---|---|
| PostgreSQL | 16 (15 or newer works) |
| MongoDB Community Server | 7.0, 8.0 or 9.0 |
| Python | 3.12 or newer |
| Node.js | 22 or newer |
| Git | any |

Ports 3000, 8000, 5432 and 27017 must be free. If the Docker stack from option A is running, stop it first with `docker compose down`.

### Step 1: Install the programs

#### macOS

Install [Homebrew](https://brew.sh) if you do not have it, then:

```bash
brew install git postgresql@16 python@3.12 node@22
brew tap mongodb/brew
brew install mongodb-community@7.0
brew services start postgresql@16
brew services start mongodb/brew/mongodb-community@7.0
```

`postgresql@16` and `node@22` are keg-only, so put them on your `PATH` (Intel Macs use `/usr/local` instead of `/opt/homebrew`):

```bash
echo 'export PATH="/opt/homebrew/opt/postgresql@16/bin:/opt/homebrew/opt/node@22/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

#### Windows 10/11 (PowerShell)

Open PowerShell and run:

```powershell
winget install --id Git.Git -e
winget install --id MongoDB.Server -e
winget install --id Python.Python.3.12 -e
winget install --id OpenJS.NodeJS.LTS -e
```

Click **Yes** on each administrator prompt.

PostgreSQL is not installed with winget: its download server rejects winget with `403 Forbidden`. Download the PostgreSQL 16 Windows installer from [enterprisedb.com/downloads/postgres-postgresql-downloads](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads) and run it with the defaults (Stack Builder and pgAdmin can be unticked). It asks you to choose a password for the `postgres` superuser; remember it for step 2.

PostgreSQL and MongoDB are installed as Windows services and start automatically. Close and reopen PowerShell so the new programs are on `PATH`.

If script execution is blocked when you activate anything later, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.

#### Linux (Ubuntu 24.04 / Debian 12)

```bash
sudo apt-get update
sudo apt-get install -y git curl gnupg postgresql python3 python3-venv
# Node.js 22
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs
# MongoDB 8.0 (official repository; use "jammy" on Ubuntu 22.04, "bookworm" on Debian 12)
curl -fsSL https://www.mongodb.org/static/pgp/server-8.0.asc | sudo gpg -o /usr/share/keyrings/mongodb-server-8.0.gpg --dearmor
sudo chmod 644 /usr/share/keyrings/mongodb-server-8.0.gpg
echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-8.0.gpg ] https://repo.mongodb.org/apt/ubuntu noble/mongodb-org/8.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-8.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org
sudo systemctl enable --now postgresql mongod
```

Ubuntu 24.04 ships PostgreSQL 16 and Python 3.12. On Debian 12, which ships Python 3.11, install Python 3.12 or newer first (for example with `uv python install 3.12`). For the Debian repository line use `https://repo.mongodb.org/apt/debian bookworm/mongodb-org/8.0 main` on x86-64. MongoDB publishes no ARM64 Debian packages, so on ARM64 Debian (for example a VM on an Apple silicon Mac) keep the Ubuntu `noble` line above; it installs and runs there.

Fedora: `sudo dnf install git postgresql-server python3 nodejs`, then `sudo postgresql-setup --initdb && sudo systemctl enable --now postgresql`, and install MongoDB from its [RHEL repository](https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-red-hat/).

### Step 2: Create the database

The backend expects a PostgreSQL login `apexgrid` with password `apexgrid` and a database `apexgrid`, exactly as in Docker. The login must be a superuser because the first start creates the `pgcrypto` and `btree_gist` extensions and two application roles. Use this only on your own machine.

macOS:

```bash
psql postgres -c "CREATE ROLE apexgrid LOGIN SUPERUSER PASSWORD 'apexgrid';" -c "CREATE DATABASE apexgrid OWNER apexgrid;"
```

Linux:

```bash
sudo -u postgres psql -c "CREATE ROLE apexgrid LOGIN SUPERUSER PASSWORD 'apexgrid';" -c "CREATE DATABASE apexgrid OWNER apexgrid;"
```

Windows (enter the `postgres` password from step 1 when asked):

```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -c "CREATE ROLE apexgrid LOGIN SUPERUSER PASSWORD 'apexgrid';" -c "CREATE DATABASE apexgrid OWNER apexgrid;"
```

MongoDB needs no setup; the backend creates its collections.

### Step 3: Get the code

```bash
git clone -b overhaul/neo-brutal https://github.com/madhavchoudhary2007-netizen/dbmsproj.git
cd dbmsproj
```

### Step 4: Start the backend (terminal 1)

The backend reads its settings from environment variables. The defaults already point at `localhost:5432` and `localhost:27017`; `APP_ENV=local` enables the demo data, the local sign-in secret and the auto-started demo race.

macOS and Linux:

```bash
cd backend
python3.12 -m venv .venv          # on Linux "python3 -m venv .venv" if python3 is 3.12+
.venv/bin/python -m pip install --require-hashes -r requirements.lock
export APP_ENV=local AUTO_DEMO_RACE=1
.venv/bin/python -m app.bootstrap
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Windows (PowerShell):

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\python -m pip install --require-hashes -r requirements.lock
$env:APP_ENV = "local"; $env:AUTO_DEMO_RACE = "1"
.\.venv\Scripts\python -m app.bootstrap
.\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

`app.bootstrap` prints `Database migration complete and seed complete`. Leave uvicorn running; `http://localhost:8000/health/ready` should report every service `up`.

Next time, only the last line is needed (after `cd backend` and setting the two variables). Bootstrap is safe to rerun.

### Step 5: Start the frontend (terminal 2)

Same on every system, from the repository root:

```bash
cd frontend
npm ci
npm run build
npm start
```

Open **http://localhost:3000** (use `localhost`, not `127.0.0.1`, so the sign-in cookie reaches the API) and sign in with a demo account in the demo accounts table below, for example `admin@apexgrid.test` / `ApexGrid2026!`. The Live timing page should show `Connected · live stream`.

On Windows, `npm ci` prints warnings in red; they are not errors as long as `npm run build` ends with the route list.

For frontend development with hot reload, use `npm run dev` instead of `build` and `start`.

### Stopping and resetting (without Docker)

Stop the backend and frontend with `Ctrl+C`. The databases keep running as services.

To start over with fresh demo data, drop and recreate the database, then run step 4 again:

```bash
psql postgres -c "DROP DATABASE apexgrid;" -c "CREATE DATABASE apexgrid OWNER apexgrid;"   # Linux: sudo -u postgres psql ...
mongosh apexgrid --eval "db.dropDatabase()"
```

### Troubleshooting (without Docker)

| Symptom | Fix |
|---|---|
| `connection refused` on 5432 or 27017 | The database service is not running: `brew services list` (macOS), `sudo systemctl status postgresql mongod` (Linux), or `Get-Service postgresql*, MongoDB` (Windows). |
| `password authentication failed for user "apexgrid"` | Step 2 was skipped or used a different password. Rerun it. |
| `permission denied to create extension` | The `apexgrid` login is not a superuser: `ALTER ROLE apexgrid SUPERUSER;` as the `postgres` user. |
| Backend exits with a runtime ownership error | Another backend (for example the Docker one) is using the same database. Stop it; only one backend per database is supported. |
| `Address already in use` / `EADDRINUSE` | Something else holds 8000 or 3000. Stop it, or stop the Docker stack with `docker compose down`. |
| `python3.12: command not found` | Use the Python 3.12+ command your system has (`python3`, or `py -3.12` on Windows) and check it with `--version`. |
| `template database "template1" has a collation version mismatch` (rolling distributions such as Kali or Arch) | As the `postgres` user run `ALTER DATABASE template1 REFRESH COLLATION VERSION;` and the same for `postgres`, then repeat step 2. |
| `The repository ... mongodb-org ... is not signed` | The key file is not readable by apt: `sudo chmod 644 /usr/share/keyrings/mongodb-server-8.0.gpg`, then `sudo apt-get update`. |
| `ERROR: In --require-hashes mode` on install | Your copy of `requirements.lock` is out of date; run `git pull`. |

### Tested on

On 2026-10-28 this guide was run end to end (install, database, backend, frontend, sign-in and live WebSocket telemetry) on Windows 11 x64 (GitHub Actions, every push that changes this README), Windows 11 ARM64 (Python 3.12, Node 24, PostgreSQL 16, MongoDB 9.0), Kali Linux 2025.2 ARM64 (Python 3.14, Node 22, PostgreSQL 17, MongoDB 8.0). On macOS (Apple silicon) the backend and frontend steps were run; the Homebrew install commands were not.

## Development environment (all platforms)

On macOS and Linux use the commands as written; on Windows run them in WSL.

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r backend/requirements-dev.txt
cd frontend && npm ci && npx playwright install --with-deps chromium && cd ..
```

Run backend tests as `.venv/bin/python -m pytest` (not the bare `pytest` script) so the package-identity guard in `backend/app/__init__.py` passes. Stop any local API that uses the same database first: the backend holds a single runtime-ownership lease per database.

## Demo accounts

| Role | Email | Password |
|---|---|---|
| Admin | `admin@apexgrid.test` | `ApexGrid2026!` |
| Steward | `steward@apexgrid.test` | `ApexGrid2026!` |
| Team principal | `principal@apexgrid.test` | `ApexGrid2026!` |

These are local demonstration credentials. Replace the seed and JWT secret before any shared deployment.

## Routes

Sixteen routes: `/` (landing), `/login`, `/dashboard`, `/live`, `/sessions`, `/stewards`, `/pit-wall`, `/championships`, `/events`, `/circuits`, `/standings`, `/teams`, `/drivers`, `/users`, `/analytics` and `/dbms` (DBMS operations and the PostgreSQL/MongoDB showcase). `/%5F_nb` is the design-primitives guide used by guide-mode tests.

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

## Engineering workflow

The active overhaul scope is [the twelve-phase plan](docs/overhaul-plan.md). Current verified status and execution permission live in [.agent/CURRENT_STATE.md](.agent/CURRENT_STATE.md) and [.agent/NEXT_STATE.md](.agent/NEXT_STATE.md). Follow [AGENTS.md](AGENTS.md) and the [delivery workflow](.agent/protocol/delivery-workflow.md); historical project snapshots and loop logs are not current completion evidence.

Antigravity execution contract: [.agent/protocol/antigravity.md](.agent/protocol/antigravity.md) — Gemini 3.8 Flash HIGH orchestrator / LOW workers, maximum two workers. Record observed UI settings or UNVERIFIED; declarations do not prove model binding. Current permission and evidence remain in the state files and latest owner instruction.

Document roles and retired instructions: [.agent/DOC_AUTHORITY.md](.agent/DOC_AUTHORITY.md). Operator commands here are not authorization for an agent to write real databases or restart setup.
