# CURRENT_STATE
updated_at: 2026-10-21T14:20:00Z
git_head: 70fc6b5
branch: perfection-loop
architect_sha256: 4cd5bc0272d02c031ca5ea833f1f07b200444efa866448f4549a5f68dab7ca73
archetype: enterprise-saas (5 signals); developer-tool secondary (3)
last_eval_score: NOT_RUN (acceptance and browser E2E hard gates unresolved)

## Verified setup and baseline
- Existing ApexGrid product committed as `ccab46d`; kit committed as `79cae60`; architecture locked as `8bde3fe`; `verify-lock.sh` passed.
- `boot.sh --probe` returned OK for `gpt-6-sol` and `gpt-6-luna`; final boot printed `boot OK`. The probe checked IDs, not the worker `high` effort binding.
- `.agent/commands.env` now uses root-runnable npm frontend commands, venv pytest and `E2E_CMD=none`.
- Initial install failed on `httpx2`; T-001 corrected it and passed offline `accept.sh` plus host pip dry-run. Typecheck, lint and build previously exited 0.
- With Docker running, the database-backed suite exited 0: 57 passed, 0 skipped. Acceptance exited 1 before creating a session: it assumes ApexGrid World Series round 3, but that championship has zero events in the current database. Pre/post counts and driver eligibility digest matched.
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

## Open risks
- T-037 isolated Compose stack was accepted in commit `70fc6b5`; use `apexgrid-test` only for database checks and verify Docker access before starting it.
- Phase 0 started on `perfection-loop`; Docker access currently denied by sandbox, to be retried with scoped escalation. `scripts/agent/run-loop.sh` has a pre-existing user edit that must be preserved.
- STOP D (2026-10-21): T-007 desktop accessibility audit still fails only on `/login` keyboard reachability after two repair rounds: 15 pass, 1 fail. Assertion at `frontend/e2e/accessibility.spec.ts:49` retained. T-035 queued, no further workers dispatched.
- T-008 responsive desktop audit was interrupted after R01 timed out at 30s and R02 began; full matrix remains unverified. T-036 queued to bound per-width cases.
- Latest safe quality checks: frontend typecheck 0, lint 0, build 0; in-memory simulation pytest 2 pass/0 skip (35 deselected); motion/banned lint 0, spacing lint 1.
- T-006 blocked after two W3 failures: generic five-state fixture overasserted states without route-specific applicability; failed draft at `.agent/results/T-006.raw.failed.spec.ts`. T-026..028 depend on it.
- T-002 acceptance fixture assumes nonexistent World Series round 3; DB data/schema untouched. Full DB-backed suite previously 57 pass/0 skip.
- T-003 route smoke: 80 cases discovered, desktop Chromium 16/16 pass; auth redirects allowed, so deeper states remain unverified.
- T-007 desktop accessibility: baseline 0/16, repair round 1 11/16. T-029/030/031 and T-032/033 accepted; second browser rerun pending. No axe gate claim.
- T-008 responsive test discovered offline; browser run interrupted after initial 30s timeout. Test design likely needs per-width cases or explicit bounded timing.
- T-005 partial notice exists but is not wired to screens. Taste bloat tasks T-023 (ui.tsx) and T-034 (special-pages.tsx) queued.
- Added only `@playwright/test` ^1.64.1 and `@axe-core/playwright` ^4.14.0 as frontend devDependencies via npm; Chromium installed with `npm --prefix frontend exec -- playwright install chromium`.
- Production frontend runner omits source/config; host typecheck/lint only. Host Python 3.14/Node 26 versus Docker Python 3.12/Node 22.
- Spacing lint fails on off-scale CSS plus border-width false positives; motion/banned lint pass.
- ADR-001 authorizes font/type choice and cookie/CSRF token migration with backend tests; neither is implemented. JWT fallback and deployment target remain evaluation risks. No aggregate score; E2E/axe/acceptance gates unresolved.
