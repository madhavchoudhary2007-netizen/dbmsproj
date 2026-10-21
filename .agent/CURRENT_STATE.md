# CURRENT_STATE
updated_at: 2026-10-21T18:48:00Z
git_head: 8da6ff7
branch: perfection-loop
architect_sha256: 4cd5bc0272d02c031ca5ea833f1f07b200444efa866448f4549a5f68dab7ca73
archetype: enterprise-saas (5 signals); developer-tool secondary (3)
last_eval_score: NOT_RUN (acceptance and browser E2E hard gates unresolved)

## Verified setup and baseline
- Existing ApexGrid product committed as `ccab46d`; kit committed as `79cae60`; architecture locked as `8bde3fe`; `verify-lock.sh` passed.
- `boot.sh --probe` returned OK for `gpt-6-sol` and `gpt-6-luna`; final boot printed `boot OK`. The probe checked IDs, not the worker `high` effort binding.
- `.agent/commands.env` now uses root-runnable npm frontend commands, venv pytest and `E2E_CMD=none`.
- Initial install failed on `httpx2`; T-001 corrected it and passed offline `accept.sh` plus host pip dry-run. Typecheck, lint and build previously exited 0.
- Isolated `apexgrid-test` stack and T-002 baseline passed: 57 backend tests, 0 skipped, then live acceptance passed through PostgreSQL, MongoDB, WebSocket, pits, standings, DBMS, and generated races. Acceptance now paginates the seeded event lookup.
- Host venv Python 3.14.7 / Node 26.10.0; running backend Python 3.12.15 / frontend Node 22.23.3. The production frontend container serves `/live` (HTTP 200); its runner image omits source/config, so in-container typecheck/lint do not run as gates.

## Active contracts
- Official PostgreSQL schema and API wire fields remain unchanged; `docs/contracts.md` is the existing cross-store contract. ADR-001 authorizes future additive disposable-stack migrations and finding-backed API changes with separate ADRs.
- MongoDB telemetry uses shared UUID strings; server emits authenticated WebSocket session events; frontend reads API via `frontend/lib/api.ts`.
- Generated race lap cap is 72; lap advances only after sector three. SQL controls pit overlap, immutable penalties and persisted standings.

## Component status
| Component | Owner | Status | States | Verified by |
|---|---|---|---|---|
| Existing 16 routes | W1/W2 | IN_REVIEW | 5-state matrix incomplete | static survey; E2E pending |
| Backend/API and schema | W2 | IN_REVIEW | n/a | 57 pass/0 skip; acceptance fixture blocked |
| DBMS teacher views | W1/W2 | IN_REVIEW | partial needs test | historical manual checks; new E2E pending |
| Evaluation harness | W3 | PLANNED | n/a | `E2E_CMD=none`; no score |
| `ViewState<T>` boundary | W2 | VERIFIED | five variants typed | typecheck, T-004 |

## Known invariants
- `0 <= session.total_laps <= 72`; session state/timestamp transitions enforced in SQL (`backend/migrations/001_initial.sql`).
- One result per session/driver and one classified position; one active reservation per driver/session; overlapping box windows rejected.
- PostgreSQL owns official records; MongoDB owns telemetry; cross-store failure must be visible as partial data, not hidden.

## Orchestrator direct edits
- 2026-10-21: configuration, `.gitignore`, `.agent/ARCHITECT.md`, and state files only; 0 product-source lines.
- 2026-10-21: `frontend/package.json` build script, 1 line: switched to Next's webpack mode because Turbopack cannot bind its internal port here; normal `npm run build` now exits 0.
- 2026-10-21: removed the F-E01 xfail marker and now-unused pytest import from the accepted security test (2 test lines); logged fix-protocol cleanup, no product-source lines.

## Open risks
- T-037 isolated Compose stack was accepted in commit `70fc6b5`; use `apexgrid-test` only for database checks and verify Docker access before starting it.
- Phase 0 started on `perfection-loop`; Docker access currently denied by sandbox, to be retried with scoped escalation. `scripts/agent/run-loop.sh` has a pre-existing user edit that must be preserved.
- T-035 fixed the `/login` audit fixture's authenticated redirect; desktop browser rerun reached all 16 routes and keyboard checks. New finding F-A11: `/login` copyright text contrast 3.88:1 (axe serious, required 4.5:1); T-038/T-039 queued.
- F-A11 fixed by T-039; marker removed. T-040 desktop accessibility sweep passed 16/16. T-041 and T-042 made all five Chromium Playwright projects pass 640/640 cases. Full-gates baseline initially had 6 failed gates; browser gate is now green. Remaining reds: ruff, format, mypy, strict lint, dependency audit.
- T-043 pinned auth login/me/JWT/WebSocket wire behavior: 7 focused tests pass, 0 skipped; Ruff violations fell from 641 to 639. F-E01 dependency replacement now has a behavior safety net.
- T-044 added a strict xfail invariant for runtime requirements; normal run reports 1 xfail, `--runxfail` reproduces F-E01. PyJWT 2.15.1 is installed in the project venv for the replacement verify.
- T-045 replaced python-jose with PyJWT 2.15.1, preserving HS256 decoding and auth behavior. Focused 8/8 pass; pip-audit reports no known backend runtime vulnerabilities. Marker removed; isolated DB suite 65 passed/0 failed/0 skipped and live acceptance passed.
- T-046 reproduced G07 at 375px: 51 undersized targets over dashboard/live/dbms/login, collapsing to shared nav links, menu/close/sign-out/refresh buttons, two selects, and login fields/button. RUN_XFAIL=1 mobile-375 fails as expected.
- T-009 fixed those shared controls; RUN_XFAIL=1 touch audit and build pass. After marker removal, full browser run: 644 pass/1 fail from injected Next.js Dev Tools button. T-047 narrows only that external control; product target assertion stays strict.
- T-008 responsive desktop audit was interrupted after R01 timed out at 30s and R02 began; full matrix remains unverified. T-036 queued to bound per-width cases.
- Latest safe quality checks: frontend typecheck 0, lint 0, build 0; in-memory simulation pytest 2 pass/0 skip (35 deselected); motion/banned lint 0, spacing lint 1.
- T-006 blocked after two W3 failures: generic five-state fixture overasserted states without route-specific applicability; failed draft at `.agent/results/T-006.raw.failed.spec.ts`. T-026..028 depend on it.
- T-002 baseline passed on isolated stack; fixture event was beyond the first `/events` page, not absent from seed data.
- T-003 route smoke: 80 cases discovered, desktop Chromium 16/16 pass; auth redirects allowed, so deeper states remain unverified.
- T-007 desktop accessibility: baseline 0/16, repair round 1 11/16. T-029/030/031 and T-032/033 accepted; second browser rerun pending. No axe gate claim.
- T-008 responsive test discovered offline; browser run interrupted after initial 30s timeout. Test design likely needs per-width cases or explicit bounded timing.
- T-005 partial notice exists but is not wired to screens. Taste bloat tasks T-023 (ui.tsx) and T-034 (special-pages.tsx) queued.
- Added only `@playwright/test` ^1.64.1 and `@axe-core/playwright` ^4.14.0 as frontend devDependencies via npm; Chromium installed with `npm --prefix frontend exec -- playwright install chromium`.
- Production frontend runner omits source/config; host typecheck/lint only. Host Python 3.14/Node 26 versus Docker Python 3.12/Node 22.
- Spacing lint fails on off-scale CSS plus border-width false positives; motion/banned lint pass.
- ADR-001 authorizes font/type choice and cookie/CSRF token migration with backend tests; neither is implemented. JWT fallback and deployment target remain evaluation risks. No aggregate score; E2E/axe/acceptance gates unresolved.
