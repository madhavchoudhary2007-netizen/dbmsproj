<!-- LOCK:BEGIN -->
> STATUS: LOCKED
> SHA256: e7722a81b4f2c708f019b3468c0a9630411ea6df88eb85aa37a7aff6ffc523a9
> LOCKED_AT: 2026-10-21T12:15:10Z
> LOCKED_BY: orchestrator
<!-- LOCK:END -->
# ApexGrid architecture — existing system, improvement in place

Evidence: `README.md`, `PROJECT_CONTEXT.md`, `PROJECT_STATE.md`, `DECISIONS.md`, `NEXT_STEPS.md`, `docs/contracts.md`, `docs/demo-guide.md`, source, and the 2026-10-21 baseline. Acceptance IDs below name existing or planned binary checks; `E2E-*` checks do not exist yet. No product source is authorized by this document alone.

## Phase A — discovery

### A.1 Problem, users, outcome

ApexGrid is a motorsport league and race-operations demo. Admins manage competition data and demonstrate PostgreSQL/MongoDB behavior; stewards review incidents and penalties; team principals see pit operations; drivers/readers follow timing and standings; a teacher inspects actual database records. The desired outcome is a coherent, believable live race that persists lap, sector, incident, pit and result records, remains inspectable after completion, and exposes the required DBMS operations. Existing contracts in `docs/contracts.md` and official records in PostgreSQL remain authoritative.

### A.2 Deliverables and acceptance IDs

Each route is an existing `frontend/app/**/page.tsx` file. A route's planned binary acceptance command is `npm --prefix frontend exec -- playwright test e2e/routes.spec.ts --grep 'E2E-Rnn'`; W3 must first add Playwright and the named case. Until then these IDs are UNVERIFIED, not passing checks.

| ID | Route / deliverable | Primary job | API prerequisite |
|---|---|---|---|
| E2E-R01 | `/` | authenticated landing redirect | auth/me |
| E2E-R02 | `/login` | sign in and show validation failure | auth/login |
| E2E-R03 | `/dashboard` | operational counts and active race | dashboard, health |
| E2E-R04 | `/live` | create/select/delete generated race; live timing, sectors and laps | demo-races, sessions/live/laps, WebSocket |
| E2E-R05 | `/sessions` | lifecycle, simulator and official results | sessions/action/simulate/results |
| E2E-R06 | `/stewards` | incident review and penalty decision | incidents/decision |
| E2E-R07 | `/pit-wall` | automatic strategy, assignment and stop history | pit-strategy, pit-reservations |
| E2E-R08 | `/championships` | competition CRUD | championships |
| E2E-R09 | `/events` | race calendar CRUD | events |
| E2E-R10 | `/circuits` | venue CRUD | circuits |
| E2E-R11 | `/standings` | persisted ranks and recalculation | championships/standings/recalculate |
| E2E-R12 | `/teams` | team CRUD and membership | teams, team-memberships |
| E2E-R13 | `/drivers` | driver CRUD and eligibility display | drivers, memberships |
| E2E-R14 | `/users` | admin user management | users |
| E2E-R15 | `/analytics` | paged/filterable driver statistics | analytics/drivers |
| E2E-R16 | `/dbms` | SQL/Mongo views, archive, EER and write demonstrations | dbms/* |

API groups live in `backend/app/main.py`. Existing test commands shown here are binary, but database cases skip without a reachable seeded PostgreSQL/MongoDB; W3 owns closing that verification gap. `API-*` is the acceptance inventory, not a claim of current coverage.

| ID | API group | Binary command / intended test |
|---|---|---|
| API-01 | `/api/auth/*`, roles, users | `.venv/bin/pytest -q backend/tests/test_api.py -k 'admin_user_management or jwt_secret'` |
| API-02 | CRUD: championships, circuits, teams, drivers, events, sessions, memberships | `.venv/bin/pytest -q backend/tests/test_api.py -k 'contract_routes or protected_driver_session_fields'` |
| API-03 | session lifecycle, results, standings | `.venv/bin/pytest -q backend/tests/test_database.py -k 'session_state_guards or standings'` |
| API-04 | simulator, live snapshot, lap progression | `.venv/bin/pytest -q backend/tests/test_api.py -k 'simulation or sector_lap_elapsed'` |
| API-05 | incidents, decisions, penalties | `.venv/bin/pytest -q backend/tests/test_database.py -k 'penalty or incident'` |
| API-06 | pit boxes, manual/auto reservations and strategy | `.venv/bin/pytest -q backend/tests/test_database.py -k 'pit or reservation'` |
| API-07 | telemetry ingest/query and authenticated WebSocket | `.venv/bin/pytest -q backend/tests/test_api.py -k 'telemetry or websocket'` |
| API-08 | generated race create/list/delete/auto-repeat | `.venv/bin/pytest -q backend/tests/test_api.py -k 'demo_race or demo_delete'` |
| API-09 | dashboard, analytics and health | `.venv/bin/pytest -q backend/tests/test_api.py -k 'contract_routes'` (dedicated cases needed) |
| API-10 | DBMS SQL schema/tables/races/EER/indexes/plans/locks | `.venv/bin/pytest -q backend/tests/test_api.py -k 'dbms_workspace or admin_lock_demo'` |
| API-11 | DBMS Mongo collections/documents and cross-store | `.venv/bin/pytest -q backend/tests/test_api.py -k 'dbms_mongo'` (cross-store case needed) |
| API-12 | DBMS constraint, transaction, lock, recalculate | `.venv/bin/pytest -q backend/tests/test_api.py -k 'constraint_demo or admin_lock_demo'` (transaction/recalculate cases needed) |

Core gates: `bash scripts/agent/verify-lock.sh`; `npm --prefix frontend run typecheck`; `npm --prefix frontend run lint`; `.venv/bin/pytest -q backend/tests` with database URLs configured; `npm --prefix frontend run build`; `E2E_CMD=none` until W3 adds browser tests. A check passes only at exit 0 with required tests collected, not when database cases are skipped.

### A.3 Expert baseline versus current gaps

| Amateur outcome | Required baseline | Current evidence |
|---|---|---|
| Spinner on each fetch | Stable skeleton; CLS <= 0.05 | Shared loading message; CLS unmeasured |
| Console-only failure | Visible cause, retry and retained useful data | Mixed error notices; partial-data contract absent |
| Desktop-only check | 320, 375, 768, 1440, 2560, 5120 checks | Some mobile browser evidence; full matrix absent |
| Mouse-first controls | Keyboard, focus and screen-reader path | Some dialogs/rows improved; route audit absent |
| Duplicate requests | Cancellation and keyed stale-response guards | Some live guards; not unified |
| Mutation without recovery | Disable/retry/idempotency and rollback where optimistic | Mixed flows; no systematic gate |
| One-off spacing | 4/8/12/16/24/32/48/64px tokens | CSS contains many literal values |
| Machine-specific green | Reproducible install/test/build in CI | `httpx2` install failure; no CI/E2E |

### A.4 Archetype score

Enterprise SaaS / Analytics: **5** matching signals (tables, dashboards, filters, roles, KPIs). Developer / Technical Tool: **3** (API documentation, DBMS/query-plan tooling, telemetry observability). Consumer: **0**; Editorial: **0**. Primary archetype is **Enterprise SaaS / Analytics** with a technical DBMS sub-area. Keep the current dark motorsport identity; do not rebrand the product to match a template.

### A.5 Non-goals

No rewrite of working race flows, schema, SQL rules, public API routes or persisted IDs. No new service split, third-party telemetry provider, fixture reset, new championship product, or visual redesign. No production deployment in this phase.

### A.6 Assumptions and unknowns

**Required assumption:** keep ApexGrid and its existing PostgreSQL schema and API contracts; improve it in place. Treat historical local-demo records as valuable and do not erase them. Browser E2E is not configured; planned IDs above are a task backlog. Local Compose is the acceptance environment; Docker was unavailable during this baseline. Architecture-changing unknowns: whether shared/public deployment is intended, whether authentication must move away from browser localStorage, and whether the evaluator requires actual browser automation or only a teacher demonstration. Use the reversible local-demo path until answered.

## Phase B — system as built

### B.1 Stack and reasons

`frontend/`: Next.js 16/React 19/TypeScript, npm lockfile, Tailwind/CSS variables; existing routed operational UI. `backend/`: FastAPI/Pydantic on Python 3.12 container; one service owns validation, auth, simulation and DBMS endpoints. PostgreSQL 16 stores official state and enforces constraints, triggers, explicit-cursor standings and pit overlap. MongoDB 7 stores high-volume telemetry keyed by PostgreSQL UUIDs. Auth uses bcrypt/JWT; WebSocket transports live events. Docker Compose is the local deployment. Host Node 26 and venv Python 3.14 differ from Node 22/Python 3.12 images; verify in container before claiming parity. Test stack is pytest plus `scripts/acceptance.py`; no configured browser E2E.

### B.2 Module map and ownership

| Directory/file | Responsibility | Owner for future packets |
|---|---|---|
| `frontend/app/**/page.tsx`, `frontend/components/*.tsx`, `frontend/app/globals.css`, `frontend/tailwind.config.ts` | routed views, layout, five visual states, design tokens | W1 for markup/styles only |
| `frontend/lib/api.ts`; future `frontend/lib/*` hooks/state | HTTP normalization, cancellation, client state contracts | W2 |
| `frontend/components/auth.tsx`, `frontend/components/special-pages.tsx`, `frontend/components/dbms-workspace.tsx` | currently mix markup and effects; preserve behavior while extracting boundaries | W2 extracts logic to new files; W1 updates presentation in separate packets |
| `backend/app/main.py`, `database.py`, `bootstrap.py`, `race_archive.py`, `config.py` | REST/WS, simulation, stores, startup | W2 |
| `backend/migrations/`, `backend/db/` | SQL schema, functions, seeds | W2, with W3 database tests |
| `backend/tests/`, future `e2e/`, `scripts/eval/` | API/database/browser checks and scoring | W3 |
| `docs/`, `.agent/`, `DECISIONS.md`, Git | contracts, architecture/state, decisions and integration | orchestrator |

The large mixed files are a risk, not permission for W1 to edit fetch/state or W2 to edit markup. Each packet has <=3 target files and <=150 changed lines.

### B.3 Cross-module contracts (existing wire shapes; tighter types are planned)

```ts
type UUID = string; type UTC = string; // ISO 8601 with Z
type Role = "ADMIN" | "STEWARD" | "PRINCIPAL" | "DRIVER";
type SessionState = "SCHEDULED" | "ACTIVE" | "PAUSED" | "COMPLETED" | "CANCELLED";
type ReservationStatus = "RESERVED" | "COMPLETED" | "CANCELLED";
type ApiError = { detail: string };
type ListResult<T> = T[]; // ordinary CRUD lists; DBMS table/document browsers return their own paged metadata
type LoginRequest = { email: string; password: string };
type LoginReply = { access_token: string; token_type: "bearer"; user: { id: UUID; email: string; full_name: string; role: Role } };
type Session = { id: UUID; event_id: UUID; session_type: "PRACTICE" | "QUALIFYING" | "RACE"; state: SessionState; total_laps: number; scheduled_at: UTC; started_at: UTC | null; ended_at: UTC | null };
type SessionAction = { action: "start" | "pause" | "resume" | "finish" | "reset" };
type DemoRaceCreate = { cars?: number }; // omitted 8..16 random; explicit 6..20
type PitAutoRequest = { session_id: UUID; team_id: UUID; driver_id?: UUID };
type PitReservation = { id: UUID; pit_box_id: UUID; session_id: UUID; team_id: UUID; driver_id: UUID | null; allocation_source: "MANUAL" | "AUTOMATIC"; starts_at: UTC; ends_at: UTC; status: ReservationStatus; box_number: number };
type Telemetry = { session_id: UUID; driver_id: UUID; ts: UTC; lap: number; sector: number; elapsed_ms: number; lap_time_ms?: number | null; sector_ms: number[]; position?: number | null; speed_kph: number; throttle_pct: number; brake_pct: number; tire_compound: "SOFT" | "MEDIUM" | "HARD" | "INTERMEDIATE" | "WET"; tire_age_laps: number; tire_wear_pct: number; tire_temp_c: number[]; pit_state: string; pit_reservation_id?: UUID | null; pit_box_number?: number | null };
type LiveEvent = { type: "session.state" | "timing.update" | "telemetry.sample" | "pit.update" | "incident.update"; ts: UTC; session_id: UUID; data: unknown };
type RaceArchive = { session: Session; results: unknown[]; incidents: unknown[]; pit_reservations: PitReservation[]; laps?: Telemetry[]; laps_included?: boolean; completed_driver_laps?: number; telemetry_count: number; updated_at: UTC };
type DataState<T> = { kind: "empty" } | { kind: "loading"; previous?: T } | { kind: "populated"; data: T } | { kind: "error"; message: string; retry: () => void } | { kind: "partial"; data: T; message: string; retry: () => void };
```

Pydantic inputs already in `backend/app/main.py`: `Login`, `Action`, `IncidentIn`, `Decision`, `ReservationIn`, `AutoReservationIn`, `Telemetry`, `ResultIn`, `DemoRaceCreate`, `SimulationControl`. SQL row ownership and invariants are in `backend/migrations/001_initial.sql`; full route fields remain in `docs/contracts.md`. Future W2 packets should replace untyped frontend `Row`/`any` boundaries incrementally without changing wire names.

PostgreSQL's 17 existing tables are `users`, `teams`, `drivers`, `team_memberships`, `championships`, `circuits`, `race_events`, `race_sessions`, `incident_reports`, `demo_races`, `demo_race_entries`, `penalties`, `penalty_points`, `session_results`, `driver_standings`, `pit_boxes`, and `pit_reservations`. MongoDB currently owns the `telemetry` collection. Neither store is being redesigned.

### B.4 State machines and legal transitions

| Flow | States and legal transitions | Persistence / guardrail |
|---|---|---|
| Login | anonymous -> authenticating -> authenticated or error; authenticated -> refreshing/me -> authenticated or anonymous; authenticated -> signed out | `auth/login`, `auth/me`; JWT role checked server-side; localStorage token is current risk |
| Session | SCHEDULED -> ACTIVE or CANCELLED; ACTIVE <-> PAUSED; ACTIVE/PAUSED -> COMPLETED/CANCELLED/SCHEDULED(reset); COMPLETED/CANCELLED -> SCHEDULED(reset) where API permits | PostgreSQL trigger and timestamp checks; `POST /sessions/{id}/action`; lap 0..72 |
| Simulation | absent -> running <-> paused -> stopped; stopped/reset -> running after clean start; generated completion -> archived + optionally new auto race | in-memory `simulations`, SQL session and Mongo telemetry; restore from stored packets on restart |
| Pit reservation | requested -> locked/allocation -> RESERVED or conflict/no-box error; RESERVED -> COMPLETED/CANCELLED; terminal states cannot reopen | SQL row lock, exclusion/unique constraints; auto chooses earliest free event box/window; Mongo/WS reflect assigned driver |
| Telemetry | produced -> Pydantic validated -> Mongo persisted -> WS published -> client snapshot/stream; WS disconnect -> reconnect + snapshot | reject invalid lap/driver/session; SQL and Mongo may be briefly out of sync, show partial state |
| Incident/standing | OPEN -> APPROVED or REJECTED; approval -> immutable penalty/points/eligibility; completed result -> recalculated standings | SQL transaction/trigger and explicit-cursor routine; repeat decision must be rejected |

### B.5 Layout contract by screen

Columns mean 375px / 768px / 1440px. The first item is content priority; the listed action is the intended single primary action, subject to E2E verification. At 320px avoid clipping; at 5120px constrain reading width and tables.

| Screen | 375 / 768 / 1440 arrangement | Primary action |
|---|---|---|
| `/` | redirect status / redirect status / redirect status | sign in |
| `/login` | one form / centered form / centered form | sign in |
| `/dashboard` | counts stacked / 2-column / summary grid | open live race |
| `/live` | race selector then timing / timing then records / timing + records | create live race |
| `/sessions` | selector then lifecycle/results / split panels / list + detail | start/resume session |
| `/stewards` | incident list then decision / 2-column / queue + detail | decide incident |
| `/pit-wall` | race selector then strategy / panels / strategy + boxes | select race |
| `/championships` | paged list / table / table | add championship |
| `/events` | calendar list / table / table | add event |
| `/circuits` | venue list / table / table | add circuit |
| `/standings` | selector then ranks / table / table | select championship |
| `/teams` | paged list / table / table | add team |
| `/drivers` | paged list / table / table | add driver |
| `/users` | paged list / table / table | add user |
| `/analytics` | filters then result / wider table / filters + results | run analysis |
| `/dbms` | group nav then view / nav + view / nav + wide data view | select view |

### B.6 Three critical data flows

1. Admin creates a generated race -> API transaction creates event/session/entries/boxes -> simulator advances each driver's sector and lap -> Mongo stores packet -> WS/live UI updates -> auto pit/incident records persist in SQL -> session finishes -> results and lap archive remain selectable in DBMS. Verify E2E-R04/R07/R16 and API-04/06/07/08/10.
2. Steward selects incident -> decision writes official penalty once -> SQL trigger updates seasonal points and eligibility -> standings recalculate from classified results -> Steward/Standings/DBMS display one consistent record. Verify E2E-R06/R11/R16 and API-03/05/12.
3. Admin opens DBMS -> authenticated SQL/Mongo metadata and race archive queries -> selector and polling update while live -> completed archive freezes final records -> explicit demonstrations return actual DB outcomes with cleanup. Verify E2E-R16 and API-10/11/12.

### B.7 Performance targets (unverified)

Mid-tier mobile LCP <=2.5s, INP <=200ms, CLS <=0.05; route initial JS <=170 KB gzip; animation frames <=16.7ms. Keep visible DOM rows bounded (current 50/100-row paging), dedupe polling, cap stream history and avoid loading full lap archives during live ticks. Measure in W3 browser gates before claiming targets.

## Gap list against protocol

Severity P0 blocks reproducible verification/security; P1 blocks a protocol gate or important user path; P2 is improvement. Evidence-based gaps are tasks, not assertions that all current UI behavior is broken.

| Gap | Severity | Evidence / required acceptance |
|---|---|---|
| G01 install typo | P0 | `backend/requirements-dev.txt` says `httpx2>=0.28,<1`; pip finds no matching distribution. Correct and rerun install. |
| G02 integration baseline | P0 | Docker daemon unavailable; 26 DB tests skipped. Run seeded Compose and require all tests collected/passing, plus acceptance script. |
| G03 browser E2E | P1 | No Playwright project or real E2E command. Add route/flow tests E2E-R01..R16 with 5-state fixtures. |
| G04 five visual states | P1 | `StateMessage` has empty/loading/error; populated renders separately and partial is not a shared contract. Audit each row below, then test all applicable states. |
| G05 keyboard/a11y | P1 | Some modal/table fixes documented, but all 16 routes need tab order, labels, focus return, screen-reader status and error tests. |
| G06 responsive widths | P1 | Test 320, 375, 768, 1440, 2560 and 5120px; no horizontal overflow or hidden primary controls. |
| G07 touch targets | P1 | Audit clickable targets against >=44x44px, especially dense tables, sidebar and DBMS tabs. |
| G08 spacing scale | P2 | `globals.css` has many literal dimensions; constrain future W1 changes to 4/8/12/16/24/32/48/64 tokens and audit existing exceptions. |
| G09 reduced motion | P1 | Verify `prefers-reduced-motion` covers spinners, transitions and live changes; add browser assertion. |
| G10 font choice | P2 | Arial/Helvetica and generic mono are the only current faces; choose and test a deliberate accessible type system without rebranding. |
| G11 auth token storage | P1 | Bearer token in `localStorage` (`auth.tsx`/`api.ts`); evaluate HttpOnly cookie migration without changing existing API contract until decision. |
| G12 JWT secret | P1 | Backend fails closed outside local mode, but local demo secret/Compose fallback must be excluded from shared deployment and tested. |
| G13 giant mixed modules | P1 | `special-pages.tsx` ~1720 lines, `main.py` ~2175, `globals.css` ~1416; W1/W2 boundaries and reviewability need small extractions. |
| G14 request/stream race conditions | P1 | Different polling/WS paths use local guards; verify navigation cancellation, reconnect snapshot, duplicate ticks and Mongo partial failures. |
| G15 deterministic simulation | P1 | Existing tests check lap/sector bounds, but fixed-step/restart reproducibility and simultaneous pit conflicts need a deterministic test harness. |
| G16 runtime mismatch | P2 | Host Node 26/Python 3.14 vs Docker Node 22/Python 3.12; run matching-container checks in CI. |
| G17 CI and scoring | P1 | No CI workflow; score >=95/all hard gates cannot be claimed yet. Add reproducible gates and score report. |
| G18 documentation drift | P2 | Historical docs mention E2E passing while no browser E2E setup exists; distinguish prior manual browser checks from automated E2E. |

Five-state screen inventory (`Y` = evident static code path, `?` = needs test, `N/A` = non-data screen; order E/L/P/X/R = empty/loading/populated/error/partial):

| Routes | E/L/P/X/R | Missing proof |
|---|---|---|
| `/`, `/login` | N/A/Y/N/A/Y/N/A | auth navigation, retry/focus E2E |
| `/dashboard` | ?/Y/Y/Y/? | empty/partial |
| `/live` | Y/Y/Y/Y/? | partial stream/database failure |
| `/sessions` | Y/Y/Y/Y/? | partial dependent data |
| `/stewards` | Y/Y/Y/Y/? | partial incident/driver data |
| `/pit-wall` | Y/Y/Y/Y/? | partial strategy/box data |
| `/championships`, `/events`, `/circuits` | Y/Y/Y/Y/? | partial related selector data |
| `/standings` | Y/Y/Y/Y/? | partial recalculation/read data |
| `/teams`, `/drivers`, `/users` | Y/Y/Y/Y/? | partial membership/account data |
| `/analytics` | Y/Y/Y/Y/? | partial page/filter data |
| `/dbms` | Y/Y/Y/Y/? | SQL available/Mongo unavailable state |

## Phase C — five-lens stress test

Pass 1 findings and amendments: goal lens assigned all route/API IDs and prerequisite owners; expert lens replaced generic Vitest commands with pytest and marked missing E2E; taste lens preserved existing identity while flagging crowded mixed files, literal spacing and unverified focal actions; technical lens added SQL/Mongo, timing and concurrency guardrails; edge lens added explicit boundary tests. Pass 2 checked each amendment against existing contracts and added the cross-store partial state and runtime mismatch. Pass 3 produced no further document amendment. The unresolved implementation gaps remain above and under Risks; none is described as passing.

| Lens 1 deliverables | Cold-start steps / prerequisite | Owner task | Test IDs |
|---|---|---|---|
| Core routes R01-R03, R08-R15 | install -> Compose/seed -> login -> selected page | T-001, T-002, T-003 | E2E-R01..R03,R08..R15; API-01..03,09 |
| Live/operations routes R04-R07 | same -> create/start race -> Mongo/WS -> pit/incident/results | T-002, T-004, T-005 | E2E-R04..R07; API-04..08 |
| DBMS route R16 | same -> admin -> SQL/Mongo views -> demonstrations | T-002, T-006 | E2E-R16; API-10..12 |
| Shared quality | install -> typecheck/lint/build -> browser matrix -> score | T-001, T-003, T-007..T-012 | gates in A.2 |

Lens 2 binary criteria: zero type errors/warnings; all configured pytest cases collected (no silent DB skip); acceptance script exit 0 on an isolated seeded stack; each planned E2E ID exits 0 when implemented; build exit 0; measured budgets in B.7. Current baseline is 31 passed/26 skipped, typecheck/lint/build pass, install fails. No score is claimed. Simulation tests must control time and seed randomness rather than sleep for a race to finish.

Lens 3 Taste review: one primary action per viewport is unverified (G03/G05); palette is dark neutral with lime action accent and red status, but 60/30/10 balance is unmeasured; single-use abstractions and decorative gradients in CSS need review (G08/G13); Recharts is justified by lap comparison, while any new dependency needs explicit benefit. Large files violate the taste file-size target and are queued for extraction rather than rewritten.

Lens 4 hard areas: lap increments only after three sectors and stops at `min(configured_laps,72)` (API-04); pit choice is earliest free event box/window under SQL serialization, and overlap is rejected by exclusion/unique guards (API-06); telemetric `elapsed_ms` is monotone per driver and UTC timestamps remain explicit (API-07); Mongo failure must preserve SQL data with a visible partial state (API-10/11); standings recalculation must be repeatable and scoped to one championship (API-03/12); active polling must discard stale responses; lists remain paged/virtualized above 200 visible rows; mutation/authorization paths reject duplicates and cross-team access.

Lens 5 boundary matrix: 0/1/72/73 laps and sector three boundary (API-04); duplicate simultaneous auto pit requests and zero available boxes (API-06); incident lap beyond session and repeated decision (API-05); WS disconnect/reconnect and Mongo offline/online (API-07, E2E-R04/R16); navigation during fetch and 20 rapid submit taps (E2E-R04/R06); 0 and 10,000 rows, 120-character IDs, RTL, and 320/5120px layouts (E2E-R08..R16); token expiry/role mismatch and missing JWT secret outside local mode (API-01). W3 must make these automated where applicable.

## Risks

- R01: Install and full DB acceptance are red/unverified until G01 and Docker availability are resolved; no completed product claim or score >=95 is possible now.
- R02: `E2E_CMD=none` and planned route IDs cannot pass until W3 adds Playwright; historical “E2E passing” means prior manual/API checks, not current automated browser coverage.
- R03: The exact security target for token storage/shared deployment needs a product decision before changing auth transport; current API and local demo must keep working.
- R04: Large mixed UI/API files make the strict W1/W2 packet boundaries costly. Extract in small behavior-preserving steps with one focused verify each.
- R05: Runtime and Compose availability differ from historical verification. Any result measured on host Python 3.14/Node 26 needs container parity before final evaluation.
