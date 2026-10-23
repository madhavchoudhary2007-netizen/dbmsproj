<!-- LOCK:BEGIN -->
> STATUS: LOCKED
> SHA256: 80f8ab5074bfe238e9467f3eabde3df685f801fce2a1f667c8bd6f3d533ed421
> LOCKED_AT: 2026-10-23T14:51:57Z
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

Enterprise SaaS / Analytics: **5** matching signals (tables, dashboards, filters, roles, KPIs). Developer / Technical Tool: **3** (API documentation, DBMS/query-plan tooling, telemetry observability). Consumer: **0**; Editorial: **0**. Interaction density remains Enterprise SaaS/Analytics with a technical DBMS sub-area. ADR-007 proposes the owner-selected **Neo-Brutal Motorsport (light)** identity: cream/paper, ink borders and zero-blur hard shadows, red primary action, domain colours, Space Grotesk/Space Mono. This replaces the dark-identity constraint only after explicit owner approval at T-302; no product change is enacted by this lock.

### A.5 Non-goals

No wholesale rewrite of working race flows, SQL rules, public API routes or persisted IDs. ADR-001 permits reasoned fonts, coordinated auth, additive disposable-stack migrations without dropping/rewriting data, and individually justified API ADRs. ADR-007 proposes lifting the visual-redesign restriction for the frontend only, subject to T-302 approval; retain every feature, chart, modal, tested copy, hook, aria name, state class and DBMS hash route. Backend security/structure and existing-capability DBMS additions follow the plan; any API path/method/response change still requires its own ADR and owner approval. No new service split, external telemetry provider, fixture reset, unrelated product area or production deployment. Phase0 changes architecture/configuration only.

### A.6 Assumptions and unknowns

**Required assumption:** keep ApexGrid and improve it in place, preserving its existing PostgreSQL schema and API contracts until an individually justified change is implemented. ADR-001 authorizes the specific font, cookie/CSRF auth, additive schema, and finding-backed API paths in A.5; it does not enact them. Treat historical local-demo records as valuable and do not erase them. Browser E2E is not configured; planned IDs above are a task backlog. Local Compose is the acceptance environment; Docker was unavailable during this baseline. Remaining unknowns: whether shared/public deployment is intended and whether the evaluator requires actual browser automation or only a teacher demonstration. Use the reversible local-demo path until answered.

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
// Planned by ADR-002, not yet implemented: browser login returns {user}, sets
// host-only HttpOnly SameSite=Lax session cookie and signed session-bound CSRF cookie;
// writes send X-CSRF-Token, fetch includes credentials, WebSocket sends cookies.
type Session = { id: UUID; event_id: UUID; session_type: "PRACTICE" | "QUALIFYING" | "RACE"; state: SessionState; total_laps: number; scheduled_at: UTC; started_at: UTC | null; ended_at: UTC | null };
type SessionAction = { action: "start" | "pause" | "resume" | "finish" | "reset" };
type DemoRaceCreate = { cars?: number }; // omitted 8..16 random; explicit 6..20
// ADR-006 internal contract: demo_races.simulation_seed is bigint|null; new
// generated races persist a nonnegative seed and restore it with the roster.
type PitAutoRequest = { session_id: UUID; team_id: UUID; driver_id?: UUID };
type PitReservation = { id: UUID; pit_box_id: UUID; session_id: UUID; team_id: UUID; driver_id: UUID | null; allocation_source: "MANUAL" | "AUTOMATIC"; starts_at: UTC; ends_at: UTC; status: ReservationStatus; box_number: number };
type Telemetry = { session_id: UUID; driver_id: UUID; ts: UTC; lap: number; sector: number; elapsed_ms: number; lap_time_ms?: number | null; sector_ms: number[]; position?: number | null; speed_kph: number; throttle_pct: number; brake_pct: number; tire_compound: "SOFT" | "MEDIUM" | "HARD" | "INTERMEDIATE" | "WET"; tire_age_laps: number; tire_wear_pct: number; tire_temp_c: number[]; pit_state: string; pit_reservation_id?: UUID | null; pit_box_number?: number | null };
type LiveEvent = { type: "session.state" | "timing.update" | "telemetry.sample" | "pit.update" | "incident.update"; ts: UTC; session_id: UUID; data: unknown };
type RaceArchive = { session: Session; results: unknown[]; incidents: unknown[]; pit_reservations: PitReservation[]; laps?: Telemetry[]; laps_included?: boolean; completed_driver_laps?: number; telemetry_count: number; updated_at: UTC };
type DataState<T> = { kind: "empty" } | { kind: "loading"; previous?: T } | { kind: "populated"; data: T } | { kind: "error"; message: string; retry: () => void } | { kind: "partial"; data: T; message: string; retry: () => void };
```

ADR-005 authorizes one API-07 ingest error-contract addition for F-DOM-04: nonidentical or older telemetry returns HTTP 409. An exact retry keeps the existing HTTP 202 response shape and packet ID without another write or live event. This is approved work, not a claim that the current ingest path enforces it.

Pydantic inputs already in `backend/app/main.py`: `Login`, `Action`, `IncidentIn`, `Decision`, `ReservationIn`, `AutoReservationIn`, `Telemetry`, `ResultIn`, `DemoRaceCreate`, `SimulationControl`. ADR-003 specifies HTTP 422 for new positive time/grid sanction decisions until official race elapsed and starting-grid rules exist; historical rows remain and affected results must be labelled provisional. SQL row ownership and invariants are in `backend/migrations/001_initial.sql`; full route fields remain in `docs/contracts.md`. Future W2 packets should replace untyped frontend `Row`/`any` boundaries incrementally while preserving wire names unless an ADR-001 finding/change proposal justifies a contract change and a separate ADR records it.

PostgreSQL's 17 existing tables are `users`, `teams`, `drivers`, `team_memberships`, `championships`, `circuits`, `race_events`, `race_sessions`, `incident_reports`, `demo_races`, `demo_race_entries`, `penalties`, `penalty_points`, `session_results`, `driver_standings`, `pit_boxes`, and `pit_reservations`. MongoDB currently owns the `telemetry` collection. Neither store is being redesigned.

### B.4 State machines and legal transitions

| Flow | States and legal transitions | Persistence / guardrail |
|---|---|---|
| Login | anonymous -> authenticating -> authenticated or error; authenticated -> refreshing/me -> authenticated or anonymous; authenticated -> signed out | `auth/login`, `auth/me`; JWT role checked server-side; localStorage token is current risk. ADR-002 specifies the planned HttpOnly session cookie, signed CSRF cookie/header, credentialed fetch, explicit logout and cookie-authenticated WebSocket; implementation remains pending. |
| Session | SCHEDULED -> ACTIVE or CANCELLED; ACTIVE <-> PAUSED; ACTIVE/PAUSED -> COMPLETED/CANCELLED/SCHEDULED(reset); COMPLETED/CANCELLED -> SCHEDULED(reset) where API permits | PostgreSQL trigger and timestamp checks; `POST /sessions/{id}/action`; lap 0..72 |
| Simulation | absent -> running <-> paused -> stopped; stopped/reset -> running after clean start; generated completion -> archived + optionally new auto race | in-memory `simulations`, SQL session and Mongo telemetry; restore from stored packets on restart. ADR-004 requires one active backend process per PostgreSQL database, enforced by a lifespan advisory lock; lock loss fails closed. ADR-006 permits additive nullable `demo_races.simulation_seed`; new generated races persist a seed and derive deterministic sector values from seed, roster and progress, with explicit external inputs for replay. Legacy null-seed races remain valid. |
| Pit reservation | requested -> locked/allocation -> RESERVED or conflict/no-box error; RESERVED -> COMPLETED/CANCELLED; terminal states cannot reopen | SQL row lock, exclusion/unique constraints; auto chooses earliest free event box/window; Mongo/WS reflect assigned driver |
| Telemetry | produced -> Pydantic validated -> ordered/idempotent check -> Mongo persisted -> WS published -> client snapshot/stream; exact retry -> existing 202 without new publish; older/conflicting packet -> 409; WS disconnect -> reconnect + snapshot | ADR-005 applies per session/driver lap, sector and elapsed ordering to API ingest; reject invalid lap/driver/session; SQL and Mongo may be briefly out of sync, show partial state |
| Incident/standing | OPEN -> APPROVED or REJECTED; approval -> immutable penalty/points/eligibility; completed result -> recalculated standings | SQL transaction/trigger and explicit-cursor routine; repeat decision must be rejected. ADR-003 rejects new unsupported time/grid sanctions before state transition and labels historical affected outputs provisional. |

### B.5 Layout contract by screen

ADR-007 proposes the following frontend layout contract after T-302 approval, with all existing features/copy/hooks preserved. Columns mean 375px / 768px / 1440px; also verify 320/5120. Shared shell: drawer below1000, sidebar above1000, one primary per viewport. Space Grotesk/Mono, 0/4/8/12/16/24/32/48/64 spacing, >=44px targets, zero-blur shadows/radius0 or9999, all five states. Body palette light>=0.85, heading contrast>=4.5, A-3 roles cream/paper/red with unchanged50–70/20–40/5–15 bands. No gate is modified by this document.

| Screen | 375 / 768 / 1440 arrangement | Primary action |
|---|---|---|
| `/` | redirect status / redirect status / redirect status | sign in |
| `/login` | art240px then form / stacked art+form / art60%+form40% | sign in |
| `/dashboard` | hero/health/KPIs stacked / 2-column KPIs / hero60%+health40%, four KPI tiles, events/incidents | open live timing |
| `/live` | demo selector, timing POS/DRIVER/GAP/TYRE, expandable detail / timing+records / tower+driver charts/laps/incidents/pits | create live race |
| `/sessions` | list then lifecycle/results / split panels / list40%+detail60%, simulator and result modal | start/resume session |
| `/stewards` | case queue then decision / 2-column / case cards+sanctions/licence meter | decide incident |
| `/pit-wall` | strategy then boxes, internal queue scroll / panels / strategy+box grid+allocation timeline/history | select race |
| `/championships` | paged list / table / table | add championship |
| `/events` | calendar list / table / table | add event |
| `/circuits` | venue list / table / table | add circuit |
| `/standings` | selector/podium/table / podium+table / stepped podium+table+ticker | recalculate standings |
| `/teams` | paged list / table / table | add team |
| `/drivers` | paged list / table / table | add driver |
| `/users` | paged list / table / table | add user |
| `/analytics` | filters then result/charts / wider table / sticky filters40%+results/charts60% | apply analysis |
| `/dbms` | hash tabs then view, internal table/EER scroll / tabs+view / overview, SQL/Mongo/actions/archive/EER, approved showcase panels | overview |

Resource routes retain paged CRUD, search, edit/delete confirmation, membership/eligibility/role details and all state classes. Every route keeps existing chart/modal/copy contracts. Motion is transform/opacity/background-color only at100–300ms with reduced-motion fallback; static plinth shadows never animate. Display leading1.0 only at computed>=48px. T-440 aligns conflicting catalogue values before motion packets; T-441 proves real-heading contrast coverage. Route verification includes states, responsive, targets, axe, data-primary and the four lints; final evaluation includes real-stack journeys and visual regression.

### B.6 Three critical data flows

1. Admin creates a generated race -> API transaction creates event/session/entries/boxes -> simulator advances each driver's sector and lap -> Mongo stores packet -> WS/live UI updates -> auto pit/incident records persist in SQL -> session finishes -> results and lap archive remain selectable in DBMS. Verify E2E-R04/R07/R16 and API-04/06/07/08/10.
2. Steward selects incident -> decision writes official penalty once -> SQL trigger updates seasonal points and eligibility -> standings recalculate from classified results -> Steward/Standings/DBMS display one consistent record. Verify E2E-R06/R11/R16 and API-03/05/12.
3. Admin opens DBMS -> authenticated SQL/Mongo metadata and race archive queries -> selector and polling update while live -> completed archive freezes final records -> explicit demonstrations return actual DB outcomes with cleanup. Verify E2E-R16 and API-10/11/12.

The live simulator and WebSocket event bus are process-local. ADR-004 keeps a single process until shared simulator leadership and fan-out exist; a second backend process must fail startup instead of serving a divergent live view.

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
| G10 font choice | P2 | Arial/Helvetica and generic mono are the only current faces; ADR-001 authorizes an accessible font family and type scale chosen from the archetype table with a written reason, without rebranding. |
| G11 auth token storage | P1 | Bearer token remains in `localStorage` (`auth.tsx`/`api.ts`); ADR-002 specifies the cookie/CSRF and login response change, with matching backend/frontend/WS/acceptance tests before closing this finding. |
| G12 JWT secret | P1 | Backend fails closed outside local mode, but local demo secret/Compose fallback must be excluded from shared deployment and tested. |
| G13 giant mixed modules | P1 | `special-pages.tsx` ~1720 lines, `main.py` ~2175, `globals.css` ~1416; W1/W2 boundaries and reviewability need small extractions. |
| G14 request/stream race conditions | P1 | Different polling/WS paths use local guards; verify navigation cancellation, reconnect snapshot, duplicate ticks and Mongo partial failures. ADR-005 adds an ordered/idempotent ingest test and fix for F-DOM-04. |
| G15 deterministic simulation | P1 | Existing tests check lap/sector bounds, but fixed-step/restart reproducibility and simultaneous pit conflicts need a deterministic test harness. ADR-006 adds a persisted seed for generated-race replay without changing wire shapes; W3 proves fixed-input reproducibility before W2 implementation. |
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

ADR-001 focused Phase C, pass 1 on A.5/A.6, B.3/B.4, G10/G11 and R03: goal lens retained all existing route/API deliverables and required a finding before any contract change; expert lens required cookie/CSRF backend tests and disposable-stack migration proof; taste lens required an archetype-based typography reason without rebranding; technical lens retained JWT roles, CSRF checks and non-destructive SQL invariants; edge lens identified login expiry/CSRF rejection, old-client compatibility and migration replay as future tests. These are implementation gaps, not completed checks. Pass 2 found zero further architecture amendments; no lens finding was rejected.

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
- R03: ADR-002 specifies cookie/CSRF auth transport, credentialed CORS, local HTTP exception, and legacy bearer compatibility. Implementation and proof remain open; the current API and local demo must keep working until the migration is accepted.
- R04: Large mixed UI/API files make the strict W1/W2 packet boundaries costly. Extract in small behavior-preserving steps with one focused verify each.
- R05: Runtime and Compose availability differ from historical verification. Any result measured on host Python 3.14/Node 26 needs container parity before final evaluation.
- R06: Process-local simulator and EventBus cannot serve concurrent backend processes coherently. ADR-004's PostgreSQL advisory lock and lock-loss fail-closed path require isolated acceptance and documentation before Phase 2 closes.
- R07: ADR-005 manual-ingest ordering and exact retry passed T-164..174 plus the 132-test disposable backend and live acceptance gates. Simulator writes still use their own path and external packets may interleave; preserve historical Mongo rows and keep this concurrency risk visible.
- R08: ADR-006 seed alone cannot reproduce wall-clock timestamps, manual interventions, safety-car changes or pit assignments. Replay requires the stored roster and those explicit inputs; legacy null-seed rows remain nondeterministic. Migration and tests are pending.

## ADR-002 focused Phase C: auth transport

Pass 1 checked the affected A.2 login/live and API-01/07 paths. Lens 1 traced anonymous login -> cookies -> reload `/me` -> protected write -> live WebSocket -> logout; owners T-050 (backend reproducer), T-051/T-052 (backend runtime), T-053 (frontend API/provider), T-054 (WebSocket client), T-055 (browser and acceptance fixtures). Lens 2 requires explicit cookie flags, login shape, CSRF rejection, Origin rejection, refresh, logout, and isolated acceptance commands; these are pending tests, not claimed passing. Lens 3 found no new dependency or abstraction; the existing JWT and standard-library HMAC suffice. Lens 4 required session-bound signed CSRF, constant-time comparisons, credentialed allow-listed CORS, and WebSocket Origin checks; ADR-002 records each. Lens 5 added expired/invalid JWT, missing/mismatched/planted CSRF, old bearer client compatibility, local HTTP cookie behavior, and logout/reload boundaries to T-050/T-055. Pass 2 found zero further architecture amendments; implementation and checks remain in the queue.

## ADR-003 focused Phase C: ineffective sanctions

Pass 1, Lens 1 traced steward decision -> penalty record -> official result/standings and found no race elapsed or starting-grid data to apply time/grid sanctions; ADR-003 keeps those fields and historical rows while rejecting new ineffective values. Lens 2 assigns binary rejection/no-write, points-only compatibility, provisional historical display, browser and isolated acceptance checks to Phase 1 packets. Lens 3 keeps the current steward interface and adds an explanation instead of a new dependency or screen. Lens 4 forbids using best-lap time as race elapsed and requires the full enforcement change proposal to define timing, grid order and data migration. Lens 5 covers positive/zero time/grid values, rejected decisions, seeded legacy five-second sanction and duplicate decisions. Pass 2 found no further amendment. API-05 and E2E-R06/R11 remain open until the tests and affected screens pass.

## ADR-004 focused Phase C: one process for live race state

Pass 1, Lens 1 traced live creation/control, telemetry fan-out and reconnect across API-04/07/08 and found that process-local simulations and subscribers would diverge under two backend processes; one database-wide owner is required. Lens 2 assigns a binary dual-owner/release/lost-connection test on apexgrid-test, plus a full backend and live acceptance rerun. Lens 3 adds no dependency or new service; the guard is small and directly protects the existing capability. Lens 4 uses a PostgreSQL session advisory lock held across the FastAPI lifespan, acquired before restoring simulations and checked while serving; ownership loss fails closed. Lens 5 covers second-process startup refusal, normal release/reacquire, database disconnect and process restart. Pass 2 found zero further architecture amendments. The guard and docs are pending tasks, not passing claims.

## ADR-005 focused Phase C: telemetry ordering

Pass 1, Lens 1 traced API-07 ingest -> Mongo -> WebSocket/live/DBMS and retained all existing outputs while making exact retry safe. Lens 2 requires strict pre-fix failures, then offline focused tests and the full disposable backend/live gate, owned by T-164/T-165. Lens 3 adds no dependency or screen; the 409 message must state the cause plainly. Lens 4 requires a process-local serialized read/check/insert against persisted per-driver telemetry under ADR-004's single-process guard; no historical rewrite. Lens 5 covers exact retry, same-position conflicting payload, older lap/sector/elapsed, independent drivers and restart with existing Mongo data. Pass 2 found zero further architecture amendments; these tests and runtime changes remain pending.

## ADR-006 focused Phase C: generated-race replay

Pass 1, Lens 1 traced generated race create -> SQL demo_races/entries -> simulator tick -> Mongo telemetry -> active-race restore and found the roster and seed must both survive restart. Lens 2 requires strict pre-fix failure for fixed-seed repeatability plus seed create/restore carry-through, migration 003 applied on apexgrid-test, then full backend/live acceptance. Lens 3 adds no dependency or screen; an internal seed is the smallest in-place change. Lens 4 uses a stable per-driver/progress RNG so a resumed race does not depend on process-global random draw count; nonseeded legacy races preserve current behavior. Lens 5 covers null legacy seed, 0 and maximum 63-bit seed, multiple drivers, restart with the same roster and external inputs, and the 72-lap cap. Pass 2 found zero further architecture amendments; explicit wall-clock and pit/safety-car inputs remain a replay precondition, recorded in ADR-006 and Risks R08.

## ADR-007 focused Phase C: proposed light overhaul

Owner plan docs/overhaul-plan.md sections0,1,3–6 replaces the prior perfection-loop execution queue. ADR-007 records a proposal pending T-302 explicit approval. A.4/A.5/B.5 are amended only for that future scope. Lens1 retains R01–R16/API01–12 and separately approves additions; Lens2 preserves palette bands/contrast, adds F-7/8/9 and hard F-2 with collected-test proof; Lens3 narrows the light-font/hard-shadow/texture exceptions with one red primary and max3 accents; Lens4 preserves storage/contracts, atomic W1/W2/W3 ownership and accept-only commits; Lens5 found motion durations/display minimum conflicts (T-440) and the real-heading contrast filter gap (T-441). Pass1 amended those conditions; Pass2 produced zero additional architecture amendments. Full lens trace and binary owners are in ADR-007. No gate, frontend/backend file or migration is changed by this amendment.

Risks: T-302 approval is pending; no product dispatch before it. Longer catalogue animations and display text below48px must satisfy owner duration/leading rules through T-440. Palette role coverage may require layout changes, never wider bands. Historical score100 excludes new quality gates and is not a verified overhaul score. scripts/agent/lock.sh commits directly, so its canonical lock-banner operation is reproduced without its Git tail and verified before accept.sh commits, honoring the owner's commit-only-through-accept instruction.
