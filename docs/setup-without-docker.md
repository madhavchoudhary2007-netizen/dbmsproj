# Running ApexGrid without Docker

This runs the same four parts that `compose.yaml` starts, directly on your machine: PostgreSQL, MongoDB, the FastAPI backend and the Next.js frontend. It takes about 10 minutes, mostly downloads.

You install four programs, create one database, then start the backend and frontend in two terminals.

| Program | Version |
|---|---|
| PostgreSQL | 16 (15 or newer works) |
| MongoDB Community Server | 7.0, 8.0 or 9.0 |
| Python | 3.12 or newer |
| Node.js | 22 or newer |
| Git | any |

Ports 3000, 8000, 5432 and 27017 must be free. If the Docker stack from the README is running, stop it first with `docker compose down`.

## 1. Install the programs

### macOS

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

### Windows 10/11 (PowerShell)

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

### Linux (Ubuntu 24.04 / Debian 12)

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

## 2. Create the database

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

## 3. Get the code

```bash
git clone -b overhaul/neo-brutal https://github.com/madhavchoudhary2007-netizen/dbmsproj.git
cd dbmsproj
```

## 4. Start the backend (terminal 1)

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

## 5. Start the frontend (terminal 2)

Same on every system, from the repository root:

```bash
cd frontend
npm ci
npm run build
npm start
```

Open **http://localhost:3000** (use `localhost`, not `127.0.0.1`, so the sign-in cookie reaches the API) and sign in with a demo account from the README, for example `admin@apexgrid.test` / `ApexGrid2026!`. The Live timing page should show `Connected · live stream`.

On Windows, `npm ci` prints warnings in red; they are not errors as long as `npm run build` ends with the route list.

For frontend development with hot reload, use `npm run dev` instead of `build` and `start`.

## Stopping and resetting

Stop the backend and frontend with `Ctrl+C`. The databases keep running as services.

To start over with fresh demo data, drop and recreate the database, then run step 4 again:

```bash
psql postgres -c "DROP DATABASE apexgrid;" -c "CREATE DATABASE apexgrid OWNER apexgrid;"   # Linux: sudo -u postgres psql ...
mongosh apexgrid --eval "db.dropDatabase()"
```

## Troubleshooting

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

## Tested on

On 2026-10-28 this guide was run end to end (install, database, backend, frontend, sign-in and live WebSocket telemetry) on Windows 11 ARM64 (Python 3.12, Node 24, PostgreSQL 16, MongoDB 9.0), Kali Linux 2025.2 ARM64 (Python 3.14, Node 22, PostgreSQL 17, MongoDB 8.0). On macOS (Apple silicon) the backend and frontend steps were run; the Homebrew install commands were not.
