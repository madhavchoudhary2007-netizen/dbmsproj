```yaml
project: ApexGrid
state_version: 12
phase: verified
services:
  frontend: working
  backend: working
  postgres: working
  mongodb: working
  simulator: working
tests:
  backend: passing (57 passed)
  api_acceptance: passing (isolated seeded acceptance stack)
  frontend_lint_typecheck: passing
  production_images: built and deployed
  e2e: passing
```

## Overall Status

The original scope and follow-up requests are verified against local Compose: generated live races, a unified DBMS workspace with live PostgreSQL and MongoDB views, completed race archives, automatic pit allocation, preserved race records, per-driver sectors, and live incident/lap records. The local `.env` has `SEED_DEMO_DATA=0` and `AUTO_DEMO_RACE=0`; no race is live. Two generated race archives remain. The newest (session `87049420-8e98-4fd6-95a0-cc8de6340d74`) has 8 drivers, 480 completed laps (60 each), 8 official results, 19 completed automatic pit stops, 3 incidents, and 2,784 MongoDB samples. The earlier archive has 9 drivers, 495 laps, 22 completed pit stops, 3 incidents, and 2,916 samples. All four services are healthy, and users can create a live race from the UI.

## Feature Status

| Feature | Status |
|---|---|
| Schema and migrations | VERIFIED |
| Authentication and role-based access | VERIFIED |
| Championships, circuits, events, teams and drivers | VERIFIED |
| Session lifecycle and official results | VERIFIED |
| Steward incident and decision flow | VERIFIED |
| Penalty trigger and race ban | VERIFIED |
| Standings explicit cursor routine | VERIFIED |
| Pit locking and overlap protection | VERIFIED |
| Backend and user management | VERIFIED |
| Frontend | VERIFIED |
| Simulator, MongoDB telemetry and external ingest | VERIFIED |
| WebSocket live timing and pit wall | VERIFIED |
| Driver analytics | VERIFIED |
| DBMS Operations API and UI | VERIFIED |
| End-to-end API acceptance | VERIFIED |
| Browser acceptance | VERIFIED |
| Generated live race creation, cleanup and auto-start | VERIFIED |
| Live DBMS race selector and completed lap archive | VERIFIED |
| EER visualization and role specialization | VERIFIED |
| Availability-based automatic pit allocation and live pit data | VERIFIED |
| Single-step lap progression and 72-lap maximum | VERIFIED |
| Automatic race archive retention, incidents, and every-driver lap records | VERIFIED |
| Independent sector progression by driver pace | VERIFIED |
| Unified DBMS workspace, live summary, and paged SQL table browser | VERIFIED |
| Full resource loading, search and UI paging beyond 200 records | VERIFIED |
| Grouped one-click PostgreSQL and MongoDB teacher-demo navigation | VERIFIED |
| MongoDB collection counts, indexes, filtered paged documents, and raw JSON inspection | VERIFIED |
| DBMS hash deep links and browser Back/Forward navigation | VERIFIED |

## Verification Performed

- `docker compose config --quiet`: passed. `docker compose down -v && docker compose up -d --build`: fresh volumes, migration, seed, and all four services started successfully. `/api/health` reports PostgreSQL and MongoDB up.
- PostgreSQL migration reran on populated data; `backend/tests/test_database.py`: **10 passed**, including constraints, trigger, explicit cursor, and two-connection pit conflict.
- `DATABASE_URL=... MONGODB_URL=... .venv/bin/pytest -q backend/tests`: **22 passed** independently.
- `DATABASE_URL=... MONGODB_URL=... .venv/bin/python scripts/acceptance.py`: passed login, session, simulator, MongoDB, authenticated WebSocket, pit conflict, penalty trigger/ban, results, standings, and DBMS lock demo; temporary test data cleaned up.
- `npm run typecheck`, `npm run lint`, and `npm run build`: passed with Next.js 16.3.8; zero lint warnings after the auth navigation fix.
- Browser after clean build: login, dashboard, scheduled Alpine session start, 10-car simulator, authenticated connected live stream, distinct running order and second-based gaps. Simulator stopped and Alpine session restored to scheduled state.
- Browser before final review repairs: users list/create form and DBMS lock demo verified, including an observed wait and SQLSTATE `23P01`.
- `npm audit --omit=dev`: zero production findings. Full npm audit reported high findings in development tooling; recheck before any shared deployment.

## Current Limits

- The Compose configuration is a local academic demo. Set a strong JWT secret and non-local `APP_ENV`, and configure database authentication and deployment network controls before shared deployment.

## Current Verification Status

- Latest deployed verification: configured backend suite **57 passed**. Frontend lint, typecheck and production build passed; all four services are healthy.
- DBMS Operations UI at `/dbms#operations` rejected an invalid driver number through `drivers_number_check` with SQLSTATE `23514`. The rollback demonstration showed before/during/after connection counts of **1/2/1** and **0 committed effects**.
- Pit locking showed a **4.48 ms** wait; an overlapping reservation was rejected with SQLSTATE `23P01`. Standings recalculation completed for championship `30224bf7-0226-4dd0-965e-94ab0feca260`.
- Driver, pit, result and standings counts remained **27/41/17/17**, and the standings checksum was unchanged.
- Isolated seeded acceptance stack passed the API, WebSocket, telemetry, incident/penalty, pit allocation/conflict, standings and DBMS flows. Its cleanup fixture transaction temporarily disabled production `trg_penalties_immutable` only to remove acceptance-owned records, re-enabled it before commit, and postchecked that it remained enabled.
- Browser verified live race creation, timing, pit data and DBMS views. The newest UI-created race completed with **8 drivers, 480 laps (60 each), 8 official results, 19 completed automatic pit stops, 3 incidents and 2,784 MongoDB samples**. The earlier archive retains **9 drivers, 495 laps, 22 completed pit stops, 3 incidents and 2,916 samples**. Both archives remain; no race is currently live; all four services are healthy.
- DBMS global Refresh reaches the selected Race Database view, and SQL table offsets are clamped. Steward decisions reset decision fields, disable decided incidents and prevent duplicate reports. Session edits submit only writable form fields. Backend decisions always include driver state, including rejected or zero-penalty outcomes; admins/stewards can make manual pit bookings; session timestamps change only through lifecycle actions; generated-race deletion validates guards before stopping/awaiting the simulator.
- PostgreSQL enforces one active pit reservation per driver/session and prevents penalty updates/deletes. The redundant index was removed.

## Historical Review Notes

The following review bullets record earlier passes. Statements about an automatic race remaining live, older archive counts, and earlier test totals describe those historical checks; the current state is recorded above and in the 2026-10-07 pass below.

- Reviewed frontend routes and API contracts across roles. Resource forms now submit writable fields and use selectors for related entities; login redirects after render. Pit reservations can be cancelled or completed from the pit wall, with role checks in the API.
- Reviewed session lifecycle, simulator restart and reset, generated race creation/deletion, pit boxes, official results, telemetry and DBMS race archives. Startup resumes active generated races while preserving completed manual archives. Session deletion and reset guard dependent records and running simulation state.
- The live database explorer polls compact records each second and loads lap history only for comparison. Completed races retain final classification and saved lap data. EER relationships no longer repeat the same link.
- Seed reruns are restricted to the ten fixture drivers, so new drivers retain their own team history. Removed only the test record orphaned by an earlier failed cleanup and stale telemetry for one scheduled fixture session.
- Added focused regression coverage for seed isolation, generated pit infrastructure, and API acceptance of compact archives and pit reservation transitions.
- Browser verified live updates, completed archive records and lap comparison, EER inspection, and four generated-event pit boxes. At that earlier check, the automatic fictional race remained live.
- The allocator finds the earliest free window across all event pit boxes inside a serialized PostgreSQL transaction. The pit wall requests a stop for a team or driver without requiring a manual box or time, and shows the resulting queue. Simulator stops are driven by each driver's tire age and surface pit state and box in WebSocket and MongoDB telemetry. DBMS live and archive views show named pit records.
- Race sessions and external telemetry enforce the 72-lap maximum; simulator laps advance only after a complete three-sector cycle and finish at the configured lap count. An accelerated six-driver race verified automatic pit records in PostgreSQL and MongoDB, scoped telemetry, and lap differences of at most one; its temporary data was removed.
- The repeating demo race previously reused one session and erased its telemetry, stops and results. Completion now retains that session as a permanent archive and creates a separate live race. Backend restart reconstructs active driver state from the latest stored telemetry without wiping laps. Generated races emit reviewable incident reports at selected completed laps; steward decisions remain manual.
- Each driver now reaches sectors on an individual simulated pace clock. MongoDB stores one completed lap measurement with three sector splits per driver and lap, while Live Timing polls a per-session lap/incident/pit endpoint. DBMS shows an every-driver lap table, independent current sectors, named incidents and retained pit records.
- The DBMS page now groups race records, every public SQL table, the EER model, schema, indexes, plans, locks, MongoDB telemetry, cross-store results, and database operations in one navigation. The summary and read-only views auto-refresh; SQL rows are paged and password hashes are excluded. A session-scoped driver list keeps names and teams correct in live timing even as archived race drivers exceed the global listing limit. Generated grids reuse distinct two-digit car numbers across races so archive growth does not exhaust numbers.
- The detailed flow audit found client listings capped at 200 even when the database held more than 800 drivers and users. Shared paginated loading now covers resource pages, selectors, stewardship, sessions, pit wall, live race lists, and analytics. Resource and lap tables page their rendered rows; the live page starts with recent archives. Pit record polling no longer reloads all directory data every five seconds. Keyboard access and focus were improved for table rows and dialogs. Generated-race incident reports now enforce entered drivers and valid lap numbers; historical result teams are resolved on the session date.
- Follow-up deployed and verified: FastAPI lifespan management awaits cancelled simulator tasks before closing MongoDB and PostgreSQL. Modals trap focus and lock body scrolling, SearchBox has an accessible input label and focus cue, and API validation errors are readable. Stale-response guards and completion-scheduled polling protect live views. Live Timing uses the session snapshot for its initial packet list and WebSocket for new packets, retains final completion data, preserves manually selected archives, and reports record-fetch recovery separately. Analytics prompts before its first query and displays named columns, averages, and seconds. The race workspace synchronizes selected props, supports self-comparison with identical A/B series and zero delta, uses named penalties and clearer state labels; mobile navigation has accessible labels and Escape handling. Compose services use `restart: unless-stopped`.
- MongoDB returns BSON datetimes as naive UTC values. JSON conversion now attaches UTC to naive datetime values before encoding while preserving aware offsets. A BSON regression verifies the nested timestamp retains its instant and ends in `Z`; deployed browser proof confirmed all 100 snapshot packet timestamps end in `Z` and restored the completed race's 12-car timing.
- Final backend/database suite: **39 passed**. API acceptance and frontend typecheck, lint and production build passed. An accelerated deployed 25-lap race produced 150 recorded laps for six drivers, two incidents, five completed pit stops, and 106 ticks with differing driver sector states; the DBMS API retained those and six classified results. The temporary smoke race was removed. Browser verified a completed automatic race with 1,008 saved laps, 16 results, an incident and named pit stops. The unified workspace browser check verified live counts, all navigation views, and user-table redaction.

## Active Work

No active work. Local services are healthy, with two completed generated race archives and no live race.

## 2026-10-07 Improvement Pass

- Pit Wall presents automatic tire-stint decisions, recommended stop windows, assigned boxes, and completed stop history. It clears the previous race's strategy and allocations immediately when the event or session selection changes.
- DBMS lap history polling uses the selected race snapshot's latest state, so it stops polling the growing archive promptly after completion.
- Historical fixture backfill preserves recorded telemetry and fills only missing completed driver laps, with cumulative elapsed time retained across recorded and synthetic laps. Partial sector packets do not suppress missing completed laps.
- Deleting a completed generated race now rebuilds standings for its own championship after removing its results; standings in another championship still block deletion. The full configured backend suite passed **43 tests**. A failed test's two temporary races were deleted through the API; the retained completed race has 2,916 MongoDB telemetry documents.
- This was the earlier 2026-10-07 verification. The next pass superseded its 43-test count with 51 tests; the follow-up below records the latest 53-test result.

## 2026-10-07 Live Race Flow Follow-up

- A real race created through the UI completed end to end: session `87049420-8e98-4fd6-95a0-cc8de6340d74`, 8 drivers, exactly 60 laps per driver (480 total), 8 official results, 3 incidents, 19 completed automatic pit stops, and 2,784 MongoDB samples. It remains archived alongside the earlier 9-driver archive (495 laps, 22 stops, 3 incidents, 2,916 samples); no race is active.
- At that pass, the configured backend suite had **53 passed**. Frontend lint, typecheck and production build passed; all four Compose services were healthy.
- Simulator restart now restores generated-race incident state. Live Timing handles the WebSocket end event and displays zero pit stops correctly. Database incident lap constraints match the session lap limit.

## 2026-10-07 Teacher Demo Views

- The DBMS workspace has grouped one-click navigation for all 17 actual PostgreSQL public base tables, race archives, EER, schema, indexes, query plans, locks, database operations, MongoDB collections, and cross-store results. It presents no public SQL `VIEW` objects.
- MongoDB collection views show actual collection counts and index definitions, with filtered paged documents and a raw JSON inspector. The admin-only API exposes `GET /api/dbms/mongo/collections` and `GET /api/dbms/mongo/collections/{collection_name}`; no extra MongoDB collections are assumed or created.
- View selection is represented in the URL hash; direct links and browser Back/Forward restore the view.
- Earlier teacher-demo verification: configured backend suite **54 passed**; frontend lint, typecheck and production build passed. Superseded by the 2026-10-07 DBMS Operations verification above.
