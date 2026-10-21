# CURRENT_STATE
updated_at: 2026-10-21T20:00:00Z
git_head: e01ac86
branch: perfection-loop
architect_sha256: 8753bfed50769fe28099f5f400bf3f7a42223fc98bebddda0db16eb7d0ece31b
archetype: enterprise-saas (5 signals); developer-tool secondary (3)
last_eval_score: NOT_RUN (quality gates and journey coverage remain open)

## Verified setup and contracts
- Boot and architecture lock pass. The branch is `perfection-loop`; isolated databases use only Compose project `apexgrid-test`, ports 15432/27018. Do not touch regular databases or secrets.
- Existing PostgreSQL schema and API wire fields remain authoritative (`docs/contracts.md`). MongoDB owns telemetry; PostgreSQL owns official race records. ADR-001 permits additive migrations and finding-backed contract changes with separate ADRs.
- Generated race lap cap 72; lap increments after sector three. SQL guards state transitions, pit overlap, results, and penalties.
- Host venv Python 3.14/Node 26 versus backend container Python 3.12/frontend container Node 22; frontend runner image lacks source/config for in-container typecheck/lint.

## Verified gates and components
- Isolated backend suite: 65 passed, 0 failed, 0 skipped after PyJWT replacement; live acceptance passed PostgreSQL/MongoDB/WebSocket/pits/standings/DBMS/generated races. Backend runtime `pip-audit -r backend/requirements.txt`: no known vulnerabilities.
- Browser suite: 715/715 passed across five Chromium projects after all-route 375px touch-target audit. Desktop axe/keyboard sweep 16/16. Typecheck and webpack production build pass.
- Phase 0 CI/full-gates harness accepted in T-016. Remaining red quality gates: Ruff 639 violations, format 7 files, mypy strict 311 errors, frontend strict lint 45 explicit-any errors, frontend npm audit 7 high/2 moderate dev-tool findings. Backend coverage target and full route journeys remain unverified.
- `.agent/commands.env` now names the real Playwright E2E command and zero-warning frontend lint; CI already runs all gates through `full-gates.sh`.
- Existing 16 routes and DBMS views remain IN_REVIEW for five UI states and role journeys. `ViewState<T>` typed boundary is VERIFIED; shared partial notice is not wired to screens.

## Ratchet and open risks
- Ruff baseline 641→639; mypy 311; strict lint 45. Quality metrics may only stay or improve. Spacing lint has off-scale CSS and border-width false positives; motion/banned lint pass.
- T-006 twice failed: generic five-state fixtures overasserted empty/partial states without a route-specific applicability matrix. T-026..028 depend on it. T-014 cookie/CSRF migration (ADR-001) needs separate backend/frontend/test packets.
- Frontend dev-tool advisories need a safe upgrade path; `npm audit fix --dry-run` offers only in-range `eslint-config-next` and selector-parser updates, and Tailwind 4 is major.
- Runtime parity, permissions matrix, simulator invariants, role journeys, full evaluation score, and docs audit remain open. `NEXT_STATE.md` is the queue.
- T-012 simulation boundaries passed 6 focused tests with Ruff steady at 639; T-013 deployment-secret gate passed 5 subprocess cases. ADR-002 plans browser cookie/CSRF migration; architecture relocked at 8753bfed after focused five-lens review, implementation unstarted.

## Orchestrator direct edits and Taste review
- Product source: one `frontend/package.json` build-script line switched Next build to webpack due Turbopack bind failure (logged at e854d9b). No other product-source edits.
- Removed accepted strict xfail markers and unused pytest import from security/touch tests (6 test lines total), then reran full suites. T-009/T-049 CSS changes added no dependency, abstraction, palette, or new focal action; no new Taste defect in their diff. Existing large-file/spacing debt remains queued.
