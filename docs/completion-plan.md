# ApexGrid completion plan — audited remaining work

Status: READY FOR IMPLEMENTATION ON OWNER START. Written 2026-10-27 against product c7dae0a / repository b22bec8, with three pre-existing T-411 worktree changes. This request creates the plan only; it does not dispatch implementation.

This is the remaining-work schedule for docs/overhaul-plan.md, not a second product specification. The twelve-phase scope, approved light design, API preservation, evaluation weights/thresholds and AGENTS.md safety rules remain authoritative. delivery-workflow.md owns cadence. NEXT_STATE selects at most twelve ready tasks; this document retains the complete dependency map. An accepted old task is reopened only for the concrete missing outcome identified here.

## 1. Evidence and corrected starting position

The audit opened 401 non-secret project files for inventory/mechanical checks, examined 174 frontend and 140 backend files within their review scopes, parsed 142 Python and four JSON files, and syntax-checked 17 shell files. This is not a claim of line-by-line review or passing live integration. Generated dependencies/builds, lockfile contents, credentials, old agent histories and workspace copies were excluded.

Current independent evidence: frontend typecheck and zero-warning lint pass; Ruff check/format pass; strict mypy passes 91 app sources; all four design lints pass; 84 focused backend tests pass. The isolated TestClient probe proves unauthenticated showcase access and synthetic success/sample rows when its database connection is forced to fail. No real database was contacted. Full database, browser, production-build, audit, coverage and release evidence is still required on the final candidate.

| Finding | Evidence | Outcome needed |
|---|---|---|
| P0 showcase access | backend/app/api/dbms_showcase.py:31; router has no auth dependency | Existing admin-only policy enforced on every showcase operation; cookie/CSRF writes preserved |
| P0 misleading database results | dbms_showcase.py:35,122,201,242,362; scripted isolation/deadlock and suppressed errors | Actual SQL operations and provenance; empty stays empty, unavailable stays unavailable; never synthetic success |
| P1 production seed default | config.py:3,8; bootstrap.py:24; Dockerfile startup runs bootstrap | Local demo remains usable; nonlocal startup cannot silently seed demo accounts |
| P1 analytics source mismatch | dbms_showcase.py:239 refers to lap_telemetry, absent from migrations | Windows computed from recorded session lap/elapsed data through a real SQL execution path |
| P1 audit/RLS proof missing | migrations/008_roles_and_rls.sql:30; default owner bypass is allowed but does not prove restricted-role behavior | Real actor attribution, steward scope and restricted-role tests; retain the approved owner DSN default |
| P1 production browser conflict | playwright.config.ts:4; app/%5F_nb/page.tsx:6; nb-primitives.spec.ts:23 | Guide tests execute in their intended environment; actual user journeys execute against production output |
| P1 partial real-stack draft | uncommitted frontend/e2e/real-stack.spec.ts, four tests | All E2E-R01..R16 plus state-changing live/pit/steward/archive journeys verified without mocks |
| P1 weak release enforcement | CI mypy continue-on-error:true; Dockerfile ignores requirements.lock; old full-gates repeats full pytest for coverage | Required types, reproducible locked image install and one coverage/JUnit full-suite execution per candidate gate |
| P2 evidence/state drift | Phase4 marked complete; old integration debt and completed T-410 remain in queue | Evidence-backed statuses, current pending work, current full score |

Keep completed backend/router moves, typography, shell and route redesign. Do not restart those tasks, reclassify the archetype or introduce a framework/state-library migration. Phase 4 is REOPENED; Phase 3 is IMPLEMENTED/PENDING INTEGRATION and its uncovered Docker/CI outcomes; Phase 8 is SCOPED EVIDENCE ONLY pending required motion/visual proof. Phases9–11 remain open. Do not infer a completion percentage from phase counts.

## 2. Execution contract and speed controls

1. Antigravity: Gemini 3.8 Flash HIGH orchestrator, LOW W1/W2/W3 workers, at most two workers. Record actual UI/session evidence or UNVERIFIED. Roles remain strict: W1 presentation, W2 runtime/backend, W3 tests/evaluation. Orchestrator owns decisions, metadata, acceptance, root integration and limited cross-task glue.
2. Begin with live ownership and dirty-file reconciliation. Preserve frontend/playwright.config.ts, frontend/e2e/real-stack.spec.ts and .agent/packets/T-411.md. Never restore, stash, overwrite or commit them into another task without resolving their owner. No competing orchestrators.
3. Before normal parallel delivery, repair acceptance scope under T-44615/16. The existing accept.sh uses git add -A, ignores .agent/ in its boundary loop and executes an envelope command before checking PASSED. Until repaired, no unrelated dirty work may be accepted. Planning docs may remain uncommitted while this safe boundary is unavailable.
4. Normal packet: one concern, exact paths, <=3 files/~150 changed lines. A justified mechanical/DI tranche may use <=8 files/800 lines; that ceiling is not permission for a large mixed semantic rewrite. Split a semantic task at a real boundary only if needed; do not create forwarding wrappers or paperwork-sized router tasks.
5. Pair independent lanes: backend corrections W2 with production-browser/fixture tests W3; after backend stabilizes pair W3 backend evidence with W1 route fixes only when a measured visual/state defect exists. Queue overlapping files. Do not keep a lane busy with speculative work.
6. Every packet names exact permitted reads, inline interfaces/schema, preserved copy/hooks/ARIA/classes, exact offline Verify/support commands, root-owned integration and dependency IDs. No open placeholders or broad directory targets at dispatch.
7. Test-first applies to real defects: W3 captures the specific failing behavior, W2 fixes it, then the same tests pass. A red test result remains FAILED/EXPECTED_RED evidence, never a fake PASSED envelope. Accept test and source candidates only after their exact checks are green; record any dependency on a peer candidate until both are accepted. Reuse the tests rather than adding another parallel suite for the same behavior.
8. Worker Verify plus independent accept.sh rerun remain required. Root compares exact command/task identity before execution. This deliberate independent rerun is not removed for speed. Do not run a third identical copy at the same relevant tree/scope/environment.
9. Root owns all browser, Docker, database and network execution. Workers do not start servers or probe real data. Use only guarded apexgrid-test, loopback bindings and owned fixtures. Never read .env/secrets, run recursive removal, reset real data, change thresholds or skip assertions.
10. Keep ADRs and the architecture current before a contract/schema change. Reconcile missing planned ADR-009 (points) and ADR-010 (showcase) from the original requirements before dependent changes; never falsely label prior code approved. Any new path/method/response-shape change requires its own ADR and the applicable owner stop. Prefer existing API shapes, honest existing error responses and additive migrations; never edit an already applied migration checksum to repair a deployed schema.
11. Do not launch a fresh full-project review per packet. Report concern/defect outcomes and evidence, maintain short state once, run budget every five acceptances, and use the existing five-repair/escalation rules. No unmeasured promises about elapsed time.

## 3. Ordered work packages

Each row is a packet-sized concern. Paths are candidate exact targets; root validates current paths, line budget and node IDs before dispatch. Proposed new tests/helpers are explicitly new files. Existing T-411 work must be reconciled before its targets are reassigned. Verify IDs are defined in section4; they are not shell commands and cannot appear unresolved in a dispatched packet.

### Wave A — safe delivery and immediate correctness

| ID / owner | Targets | Change and binary outcome | Depends / Verify |
|---|---|---|---|
| T-44614 / O | this plan; state/routing docs | Planning checkpoint; preserve all product bytes and pending ownership. No implementation | Current request; DOC |
| T-44615 / W3 | new scripts/eval/test_accept_scope.py | Disposable temporary-Git tests: accept stages only approved task paths, rejects substituted Verify/FAILED envelopes before execution, preserves unrelated dirty and staged files, handles .agent paths and verifies commit scope | None; ACCEPT-SCOPE |
| T-44616 / W2 | scripts/agent/accept.sh | Small orchestration-tool fix satisfying T-44615; exact command preflight, explicit task-path staging/commit, all-path review and no unrelated staged content. Keep independent Verify and required commit behavior. If too large, create a role-approved implementation packet; no bulk root product coding | T-44615; ACCEPT-SCOPE |
| T-44617 / W3 | new backend/tests/test_showcase_security_truth.py | Regression cases for anonymous/wrong-role denial, admin cookie writes/CSRF, empty reads, unavailable DB, real refresh outcome; no test may require fake data to pass | Tooling; SHOWCASE-UNIT |
| T-44618 / W2 | backend/app/api/dbms_showcase.py | Apply existing admin/current-user dependencies to all showcase routes and write CSRF path; no public audit exposure; preserve expected role status codes | T-44617 red cases; SHOWCASE-AUTH |
| T-44619 / W2 | backend/app/api/dbms_showcase.py | Remove sample-row/fake-plan fallbacks from read endpoints and broad exception suppression; genuine empty lists and errors use existing response/error contracts | T-44618; SHOWCASE-TRUTH |
| T-44620 / W2 | backend/app/api/dbms_showcase.py | Refresh returns success only after actual successful database operation. Verify refreshed result and surface DB failure truthfully | T-44619; SHOWCASE-REFRESH |
| T-44621 / W3 | new backend/tests/test_seed_policy.py | Local default, nonlocal default, explicit configuration, startup/no-seed and non-disclosure regression cases using mocks; no external connection | Tooling; SEED |
| T-44622 / W2 | backend/app/config.py; backend/app/bootstrap.py | Safe seeding defaults and explicit nonlocal policy while preserving local demo behavior; never change actual .env or stored users | T-44621 red cases; SEED |

Scheduling: after tooling, W3 can prepare backend red tests while root writes required ADRs; then W2 fixes showcase and W3 tackles browser test configuration/fixtures in disjoint files. Auth/read/refresh target the same file and must run serially. Combine adjacent corrections only if the packet remains one concern within its measured budget and acceptance coverage is retained.

### Wave B — real DBMS behavior and domain closure

| ID / owner | Targets | Change and binary outcome | Depends / Verify |
|---|---|---|---|
| T-44623 / W3 | new backend/tests/test_showcase_concurrency_unit.py; new backend/tests/test_showcase_db.py | Controlled-order/timing tests plus actual two-connection isolation and deadlock integration cases. Assert real observations, SQLSTATE40P01, timeouts, rollback/cleanup and repeatability; schema-only assertions are insufficient | ADR-010; CONCURRENCY-UNIT + DB-SHOWCASE root |
| T-44624 / W2 | backend/app/api/dbms_showcase.py; new backend/app/core/showcase_transactions.py | Implement real two-connection isolation/deadlock demonstrations on owned demo-scoped rows, bounded waits and guaranteed cleanup. Use synchronization rather than long sleeps; preserve response shape | T-44623 red evidence; CONCURRENCY-UNIT + DB-SHOWCASE |
| T-44625 / W3 | backend/tests/test_showcase_db.py; new backend/tests/test_showcase_analytics.py | Recorded-lap windows: position/gap/interval/rolling average, sparse laps, missing telemetry, ties, race/driver separation, actual query execution and explain proof | ADR-010; ANALYTICS-UNIT + DB-SHOWCASE |
| T-44626 / W2 | backend/app/api/dbms_showcase.py; new backend/app/core/showcase_analytics.py | Replace nonexistent lap_telemetry dependency with actual authoritative recorded laps/elapsed values. Prefer a bounded parameterized PostgreSQL CTE over normalized recorded Mongo lap input to avoid a new permanent schema. Do not substitute best-lap times for race elapsed or invent missing laps | T-44625; ANALYTICS-UNIT + DB-SHOWCASE |
| T-44627 / W3 | backend/tests/test_showcase_db.py; new backend/tests/test_showcase_audit.py | Prove real actor attribution, exactly one row for a known steward action, actual view refresh, real metadata/EXPLAIN and restricted-role permissions/RLS. Admin owner access is not proof of restricted-role behavior | Auth/truth; AUDIT-UNIT + DB-SHOWCASE |
| T-44628 / W2 | backend/app/api/dbms_showcase.py; new backend/app/core/showcase_audit.py; next additive migration only if required | Set validated actor/role transaction context, query real rows and enforce approved steward scope on restricted connections. Keep existing owner DSN default; test restricted roles explicitly. If SQL repair needed, add a new migration with ADR, never rewrite 006..008 | T-44627; AUDIT-UNIT + DB-SHOWCASE |
| T-44629 / O | no product edits | Domain close: full disposable backend with zero skips, contract snapshot/goldens, migration replay/checksum, seed/auth/lease/telemetry and real showcase tests; collect coverage/JUnit in the same pytest execution. Reopen Phase4 only until this passes | All backend corrections; BACKEND-DOMAIN |

The proposed analytics bridge is a design option, not permission for a shape/schema change. Validate existing archive APIs and actual telemetry semantics first; record the final choice in ADR-010. A blocking provenance gap is a finding, not a reason for placeholder values. Integration fixture reuse may reduce setup time only when it preserves isolation and cleanup.

### Wave C — production browser harness and real race journeys

| ID / owner | Targets | Change and binary outcome | Depends / Verify |
|---|---|---|---|
| T-44630 / W3 | frontend/playwright.config.ts; new frontend/e2e/runtime/playwright-selection.test.mjs | Correct project ownership/config: production user routes; development-only primitive guide in a dedicated guide project. No existing test is deleted, skipped or silently unselected. Verify total spec/project assignment, both real-stack viewports and API URL18000. Reconcile current T-411 owner first | Tooling; BROWSER-SELECTION + root GUIDE |
| T-44631 / W3 | frontend/e2e/accessibility.spec.ts; frontend/e2e/mock-platform.ts only if needed | Model actual root redirect in accessibility assertions and role fixtures; keep root journey, keyboard and axe coverage rather than suppressing it | T-44630; offline TS + root A11Y-FOCUS |
| T-021 / W3 | scripts/acceptance.py; new backend/tests/test_acceptance_fixtures.py | Self-owned named championship and required events, recorded ownership, cleanup on success/failure; retain every behavior assertion. Complete the fixture safety plan below before dispatch; root alone executes acceptance | Tooling + fixture plan; FIXTURE-UNIT + root ACCEPTANCE |
| T-411 / W3 | frontend/e2e/real-stack.spec.ts; new frontend/e2e/real-stack-fixtures.ts; frontend/playwright.config.ts only if still necessary | Extend existing draft: all16 route jobs plus actual race create/start/WS changes/one-lap increments/cap72/auto pits/incidents/complete/archive/driver-lap comparisons, steward approval and persisted recalculation. Use deterministic controls and owned fixtures, no page.route mocks. Assert changed persisted values, not mere visibility | Backend domain + T-021 + harness; offline TS + root REAL-STACK |
| T-412 / W3 | new frontend/e2e/visual-regression.spec.ts; exact committed snapshot paths | Deterministic screenshots for 16 routes at375/1440, mask only changing values, animations disabled, existing0.01 diff threshold. Capture baselines after fixes and human/root review, never regenerate to conceal a defect | Stable production routes; offline TS + root VISUAL |
| T-413 / W3 | frontend/e2e/motion-hooks.spec.ts; frontend/e2e/perf-fps.spec.ts | Test actual production motion/scene: reduced motion zero running animations, allowed properties, FLIP<=350ms,20 drivers at4Hz and600-frame p95<=16.7ms/heap<1MB. A static page measurement does not prove streaming performance | Harness + actual live feed; offline TS + root MOTION |
| T-414 / W3 | exact existing route/state/axe/overflow specs only when a measured gap needs repair | Run required route/state/keyboard/touch/palette/data-primary/axe/edge matrix at all5 widths. Reuse existing specifications and repair fixtures/assertions only for correctness; preserve coverage | Stable routes; root UI-MATRIX |
| T-415 / W3 | backend/tests/test_points_system.py; new backend/tests/test_standings_tiebreak.py | Prove standings tie ordering, unclassified/bonus/configured points behavior and existing-championship before/after equality; do not add tests mirroring type definitions. Full backend coverage>=80% is measured at its full gate | ADR-009 + points implementation; POINTS + BACKEND-DOMAIN/RELEASE coverage |

Required real-stack journey inventory (T-411 owns tests; existing API/setup helpers may prepare owned fixtures, but UI actions under test must actually run through the UI):

| ID / route | Minimum observable proof |
|---|---|
| R01 / | Anonymous redirect to login and authenticated redirect to dashboard |
| R02 /login | Invalid credentials, valid cookie login, reload persistence and logout rejection; never log passwords/tokens |
| R03 /dashboard | Fixture-backed counts, next event and actual service health; no fabricated zero on failure |
| R04 /live | Create/select own race; observe changing per-driver timing/sectors and newly persisted lap; delete only owned generated race |
| R05 /sessions | Start/pause/resume/finish short owned race; official results persist and match its archive |
| R06 /stewards | Decide own incident once; sanctioned points/eligibility/standings effects agree; duplicate decision rejected |
| R07 /pit-wall | Automatic allocation reflects box availability; collision/no-box state and recorded completed stop visible in race/DBMS |
| R08 /championships | Owned create/edit/list/delete plus referenced-record protection |
| R09 /events | Owned event CRUD and round uniqueness/relationship validation |
| R10 /circuits | Owned circuit CRUD and safe referenced-delete behavior |
| R11 /standings | Explicit recalculation persists expected fixture ranks/points; no fabricated prior-rank delta |
| R12 /teams | Owned team and membership flow; principal visibility/authorization matches existing role contract |
| R13 /drivers | Owned driver/membership flow; invalid/overlapping assignment rejected; official eligibility cannot be bypassed |
| R14 /users | Admin-owned account CRUD with role boundaries and no password/hash leakage; clean up owned account |
| R15 /analytics | Apply real fixture filters, paging and empty outcome; displayed values match recorded data |
| R16 /dbms | Actual SQL/Mongo metadata, real showcase operations, live-to-completed archive, per-driver laps/sectors/EER and cross-store partial recovery |

Run these on both declared real-stack viewports with isolated run/project ownership. Combine shared setup, not assertions: one short race can support its lifecycle/pit/steward/archive journey when order is explicit and failures remain attributable. Read-only route smoke may run in parallel; mutation journeys sharing a fixture run serially. Existing mocked edge/state/accessibility tests provide exhaustive fault injection and are not duplicated as every real-stack happy-path permutation.

Fixture safety plan to show before T-021 dispatch: verify apexgrid-test project/loopback endpoints; choose unique run ownership/name; create only the owned championship/events/related records; snapshot required existing references without changing them; track all created SQL/Mongo IDs; isolate each mutation journey and always clean up in finally. Existing official penalties are immutable. Before approving a row-cleanup strategy, prove it neither changes unrelated penalty totals nor disables guards during assertions. If immutable rows cannot be removed safely, use a fresh run-owned disposable database/collection within the test stack and destroy only that run-owned fixture database after stopping its owned API connection; record the exact names and teardown bounds. Do not force-delete official rows or weaken triggers as a shortcut. No real database/volume is touched. Resolve this constraint before writing mutation browser tests that depend on it.

Build/server fixture contract: set NEXT_PUBLIC_API_URL for the disposable API before creating production output; use a consistent loopback hostname for frontend, API and cookies, and an explicit credentialed CORS/WS Origin allow-list containing the assigned frontend port. Never edit .env to achieve this. Reuse that build only while its source/config/environment digest matches. Put 0/1/72/73-lap boundary proof in deterministic backend tests; browser lifecycle uses a short owned race through existing permitted setup/control paths and must still prove real stream-to-archive persistence. No new acceleration endpoint, wall-clock sleep per lap or 72-lap browser repeat per route.

Guide configuration may use a second root-managed dev server for guide-only cases. Actual user-route tests stay on production output. Every original primitive case still runs at its required widths; a project assignment is not a waiver. Root validates test listing and recorded collection counts before relying on the split. Workers start neither server.

### Wave D — release tooling and accurate handoff

| ID / owner | Targets | Change and binary outcome | Depends / Verify |
|---|---|---|---|
| T-44632 / W3 | scripts/eval/full-gates.sh; scripts/eval/db-baseline.sh; new scripts/eval/test_release_runner.py | One full pytest execution per candidate gate emits coverage>=80%, JUnit and zero-skip proof; db-baseline then performs acceptance without triggering another full pytest from full-gates. Keep all assertions/checks and failures fatal; test orchestration with offline stub commands | Tooling; RUNNER-UNIT |
| T-44633 / W2 | backend/Dockerfile; frontend/Dockerfile only for a proven parity gap; compose.yaml only with applicable approval | Actually install the already required hashed backend lock with --require-hashes, preserve nonroot/health and verify standalone frontend. Root owns lock regeneration/network. No new dependency or default-port/production-data change | Contract/Compose boundaries honored; offline Docker/lock checks + root IMAGE |
| T-420 / W3 | .github/workflows/ci.yml; exact CI helper config files, <=3 per packet | Required strict mypy, full backend+coverage+zero-skips, production mocked journeys, real-stack API fixture job, reviewed visual job, audits, Lighthouse all16, bundle check. Reuse artifacts/jobs on the same candidate instead of rerunning everything for each dimension. Must have actual green PR run | Stable runners/tests/image; CI schema/static + root green CI |
| T-421 / O | README.md; docs/architecture.md; docs/demo-guide.md | Accurate fresh-start/demo instructions, current diagrams, live and completed race/database showcase flow, local-only demo guidance and safe operator boundaries. Copy evidence/URLs from observed runs; no secrets | Actual working stack; DOC-LINKS + root demo walkthrough |
| T-431 / W1 | frontend/app/globals.css; exact remaining style modules only if needed | Reconcile legacy CSS reset<=50 lines with actual imports; remove obsolete selectors only after proving unused. Preserve every approved feature and palette/motion rule; no gratuitous route redesign | Stable routes + measured inventory; CSS-FOCUS + impacted routes |
| T-430 / O | .agent/eval/*.json; .agent/FINAL_REPORT.md; state | Full final candidate gate set, fresh evidence bindings, A-5/A-6 root judgment and score.sh. Aggregate>=95, all six hard gates and no NOT_RUN/skipped DB checks. No success from old score files | All code/test fixes, docs and cleanup; RELEASE |
| T-432 / O | PR artifact, no merge | PR overhaul/neo-brutal -> perfection-loop with current score, command exits/counts, risks and demo instructions; wait for owner merge decision | T-430 passes and clean intended tree |

T-431 runs before final scoring so cleanup cannot invalidate a claimed release score. T-420 may be split by independent jobs only if its three-file budget requires it. W1 is used only for measured presentation defects; W3 must not edit product code to make a test pass.

## 4. Exact verification policy and command families

Before dispatch replace every family below with literal commands and actual existing test node IDs. New test paths above become executable only after W3 creates them. Missing or zero collected tests is a failure. Verify commands run from the project root. No wildcard selection across unrelated backend domains and no global pytest -k that deselects a required snapshot/replay module.

- Offline pytest pattern: env -u DATABASE_URL -u MONGODB_URL -u APEXGRID_TEST_STACK APP_ENV=local PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=backend:. .venv/bin/pytest -q -p no:cacheprovider <exact module/node IDs>. This intentionally is not the full integration gate.
- ACCEPT-SCOPE: .venv/bin/pytest -q scripts/eval/test_accept_scope.py (isolated temporary Git fixtures; no writes to the project checkout).
- SHOWCASE-UNIT/AUTH/TRUTH/REFRESH: exact relevant cases in backend/tests/test_showcase_security_truth.py plus existing snapshot/route-registration cases when wiring changes. Include only the applicable subset once; no testing type validation repeatedly for a behavior fix.
- CONCURRENCY-UNIT: backend/tests/test_showcase_concurrency_unit.py; ANALYTICS-UNIT: backend/tests/test_showcase_analytics.py; AUDIT-UNIT: backend/tests/test_showcase_audit.py; SEED: backend/tests/test_seed_policy.py; FIXTURE-UNIT: backend/tests/test_acceptance_fixtures.py; RUNNER-UNIT: scripts/eval/test_release_runner.py. Use the offline pattern and scoped lint/types for changed Python.
- POINTS: backend/tests/test_points_system.py and test_standings_tiebreak.py offline cases; DB-backed before/after equality is root-owned and cannot be claimed by a SQL-text inspection.
- Offline frontend task check: npm --prefix frontend run typecheck; relevant runtime tests with node --experimental-vm-modules --test frontend/e2e/runtime/<exact test>. Use the actual module-import runner conventions. Root still owns browser runs.
- Scoped Python static check: .venv/bin/ruff check <exact changed files> && .venv/bin/ruff format --check <exact changed files>; strict mypy on the affected supported module scope. Shared provider/type changes expand dependent scope for a recorded reason.
- BROWSER-SELECTION: targeted Node config/selection tests plus root Playwright --list; collection proves assignment only, never browser success. GUIDE/A11Y-FOCUS/REAL-STACK/VISUAL/MOTION/UI-MATRIX run with root-managed servers, explicit projects/specs and fixtures; never an implicit all-project sweep per task.
- CSS-FOCUS: typecheck, relevant style lints and affected route assertions. Full design lints at route/milestone boundaries; no production build after a test-only assertion change unless compiled artifact/environment changed.
- BACKEND-DOMAIN: root bootstraps/guards apexgrid-test once, provides its explicit fixture URLs, runs the entire backend suite with --cov=backend/app --cov-fail-under=80 --junitxml=<owned report> and zero-skip junit_gate.py; then acceptance once. Record migration replay, auth/lease/persistence and showcase coverage. Do not print credential values.
- IMAGE: root build/test disposable production images once per changed Docker/lock/build input; readiness and nonroot checks, Node22/Python3.12 parity. Host typecheck/lint remain valid source checks; do not demand source/config from a minimal runtime image. Do not substitute lint for a missing runtime check.
- DOC/DOC-LINKS: git diff --check, relative links, protected design/DoD/rubric/task inventory, state budgets/lock and preserved pending-work hashes. No application suite for prose-only edits.

## 5. When to run focused, domain and full checks

| Trigger | Run | Avoid |
|---|---|---|
| New failing behavior | One focused reproducer, root records red output | New whole-project baseline/audit |
| Worker implementation candidate | Approved focused tests + affected lint/types; root accept.sh independently repeats exact Verify | A third identical run; worker DB/browser/network/server |
| Auth/provider/persistence/SQL change | Relevant root disposable integration before marking verified | Calling static-only acceptance domain-complete |
| Completed backend domain (Wave B) | Full backend once with coverage/JUnit/zero-skips + acceptance; one kept test stack | Running coverage as a second full pytest invocation |
| Route/harness milestone | One production build for its input digest, all affected route/state/keyboard/axe/viewport checks; focused Taste | Whole mocked browser matrix after every tiny test edit |
| Runtime/image/lock change | Root disposable image/runtime parity and relevant journeys | Host-version results labelled container proof |
| Final code/test candidate frozen | Complete RELEASE matrix below once, using current artifacts | Four identical full suites to populate four score dimensions |
| A failure is repaired | Reproducer plus affected dependencies; complete invalidated release gates | Restarting unaffected green gates without a dependency/fixture change |

Evidence key: product/test content digest or tested revision, exact command/options, fixture version, browser/runtime/environment and counts. Shared CSS invalidates all consuming route visuals/axe; shared providers invalidate relevant integrations; a test change invalidates that test evidence; a docs-only commit does not invalidate product evidence. Never reuse an old green against changed inputs. Reuse exact current evidence across score dimensions; an existing full-suite/coverage result may satisfy multiple gates without another invocation. Preserve complete final candidate proof even when it is assembled from identical-input artifacts. Record why any rerun is necessary.

Final RELEASE matrix: backend full+coverage>=80%+zero-skips+acceptance; strict mypy/Ruff; frontend typecheck/zero-warning lint/runtime suite; four design lints; production build and gzip170KB-per-route gate; mocked production route/state/keyboard/axe/edge tests at five widths; guide cases in the declared guide environment; all16 real-stack journeys at375/1440; reviewed visual snapshots; reduced-motion/live600-frame performance; mobile Lighthouse>=90 plus LCP<=2.5s/CLS<=0.05/TBT<=200ms; dependency audits; container parity; current A-5/A-6 judgment; real green CI; then score.sh. The declared thresholds and hard gates are exactly evaluation.md; this list never grants a waiver.

## 6. Completion and escalation

Before final scoring, maintain a requirement-to-evidence ledger for every unclosed original plan row and finding: implementation paths, exact test IDs, actual command/result and evidence identity. A passing test list is not completion evidence; missing original behavior becomes a focused repair, not a new redesign or whole-codebase audit.

Do not call the project done because screens exist, mock tests pass, main.py is short or the historical score is high. Completion requires every reopened finding closed with proof, all original plan requirements mapped to current evidence, no misleading success data, protected showcase operations, real race lifecycle/archive consistency, full release score>=95 and hard gates F-1/F-2/F-3/F-4/F-5/P-6 passing with no NOT_RUN or skipped DB checks. Then update FINAL_REPORT with exact outputs/counts and open the required PR; do not merge.

After a failure, use one concrete hypothesis and the same owner role. At most five repair iterations; identical failing sets without new evidence escalate per evaluation.md. Ordinary blocked tooling is recorded and independent ready work continues. Stop for credentials/paid services, destructive or production action, forbidden contract/threshold decisions or exhausted repair limits. Never hide a blocker by changing a test.

## 7. Handoff to a fresh or lower-thinking model

Read AGENTS.md -> CURRENT_STATE/NEXT_STATE -> DOC_AUTHORITY -> this plan's next wave/rows -> the triggering protocols and relevant original plan sections. Verify branch/lock, record model settings and inspect in-flight ownership once. Do not reread every result/archived plan or repeat setup. Select only a ready packet with exact targets and literal Verify. State records TASK_VERIFIED/PARTIALLY_VERIFIED/DOMAIN_VERIFIED accurately; a completed implementation is not automatically verified.

At each milestone report closed finding/task IDs, actual command exits/counts, integration debt, elapsed worker/root-check time if observable and the next two ready tasks. Measure speed with fewer redundant invocations/idle handoffs and accepted outcomes; do not lower tests/thresholds to improve a timing metric.


**T-44635 (W3):** Preserve existing showcase assertions with authenticated, deterministic offline database fixtures after T-44618; the legacy tests assumed anonymous access and fallback data. No assertion may be deleted or weakened. Verify: `.venv/bin/pytest -q -p no:cacheprovider backend/tests/test_dbms_showcase.py`.
