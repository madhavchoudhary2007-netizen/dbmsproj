# Demo flow

Operator guide for the local demo only (never point it at a shared database). Not an autonomous-agent task list. Do not execute these writes/deletes/seeds against real databases. Agent verification uses only guarded disposable apexgrid-test with explicit fixture/cleanup scope. Demo availability must be observed, not assumed.

1. Run `docker compose up --build`, open `http://localhost:3000`, and sign in as `admin@apexgrid.test` with `ApexGrid2026!`.
2. Open Live Timing. A generated race is already running in the local Compose setup. Inspect the fictional driver names, licences, car numbers, positions, lap pace and telemetry. Click **Create live race** to start another random 8–16 car race; select it from the generated-race list. Delete a generated race from that list when finished. The automatically started race repeats after its configured lap count. The seeded 2026 championship, 10 drivers, four teams, three circuits and three events remain available; you can also start the scheduled Alpine race manually from Sessions.
3. In DBMS Operations, run Schema and Indexes to inspect PostgreSQL metadata. Run both Query Plan controls for actual PostgreSQL `EXPLAIN (FORMAT JSON)` output. The session/lap query corresponds to the composite B-tree index. Run the Constraint Demo and see PostgreSQL reject an invalid driver number in a savepoint.
4. Run Transaction Demo to see a temporary write rolled back inside a real PostgreSQL transaction. Run Lock Demo: one connection reserves a pit box, the second waits on its row lock, then PostgreSQL rejects the overlapping request with SQLSTATE `23P01`. The demo cleans its temporary reservation. `GET /api/dbms/locks` shows current lock rows.
5. In Steward Desk, create or select an incident and approve a penalty. The `penalties` insert fires the PostgreSQL trigger, updates `penalty_points`, and sets eligibility to `RACE_BANNED` at 12. The seeded approved incident demonstrates the ordinary decision path; use the automated DB test for an exact threshold check without altering demo data.
6. Stop simulation, finish the session, record classified results, and recalculate standings. The PostgreSQL `recalculate_standings(uuid)` function uses an explicit cursor and persists ranked totals.
7. In DBMS Operations, inspect the MongoDB telemetry store and Polyglot Data. The latter links PostgreSQL official rows to MongoDB telemetry by session and driver UUID.

For a repeatable command-line acceptance run with automatic cleanup, execute `scripts/acceptance.py` as documented in the README. It exercises the trigger threshold, WebSocket, concurrency, standings and DBMS endpoints.

Use `.agent/CURRENT_STATE.md` and named test evidence for current verification.


### Live database and completed race archive
Open **DBMS operations** as admin. At the top, select a race. Active races refresh telemetry counts, timing rows and stored completed laps every second. Select **Redwood Grand Prix** or the other completed fixture for saved final results. Choose **Lap-by-lap comparison**, then select two drivers to compare times, deltas and sector splits. Historical fixture laps are clearly labeled seeded simulation data; completed manual generated races retain their actual simulator measurements.

The EER diagram is directly below the race explorer. Click an entity for its actual PK columns and foreign keys; it covers the shared model used for both active and completed races. Existing SQL transaction, locks, query-plan and constraint demonstrations remain below.
