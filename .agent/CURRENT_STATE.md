# CURRENT_STATE
updated_at: 2026-10-21T13:04:06Z
git_head: 8d26347
branch: master
architect_sha256: e7722a81b4f2c708f019b3468c0a9630411ea6df88eb85aa37a7aff6ffc523a9
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
- Official PostgreSQL schema and API wire fields remain unchanged; `docs/contracts.md` is the existing cross-store contract.
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
- T-029 accepted: keyboard audit now checks document.activeElement rather than counting `:focus` matches; browser rerun pending after UI fixes.
- T-007 orchestrator desktop browser check failed 16/16 after offline acceptance. Real findings: footer #56616c on #0b0e12 has 3.05 contrast; `.state` notices lack status semantics. Test defect: `:focus` locator counted two elements on login. T-029/T-030/T-031 queued; do not claim axe gate passed.
- T-007 accepted as an offline-discoverable accessibility audit; 16 route cases × five viewports. Orchestrator browser result pending. The test uses fake auth and aborts non-GET requests.
- T-006 blocked after two W3 failures. Retry generated 100 discovered cases but reported missing states using generic assertions not applicable to every screen; no test source committed. Draft retained only at `.agent/results/T-006.raw.failed.spec.ts`.
- T-006 first W3 result FAILED with no target diff: route wrappers hide implementation in `frontend/components/special-pages.tsx`, omitted from read list. `accept.sh` found 0 tests and exited 1. Retry packet widens read-only context; no assertion weakened.
- T-025 accepted: apiRead is now GET-only, removing the HEAD empty-body path; typecheck passed. No caller uses it yet.
- T-011 accepted at 3d0f6dc: opt-in cancellable GET/HEAD retry helper typechecks; code review found HEAD 200 wrongly attempts JSON parsing. T-025 is P1 and must land before any caller adopts the helper.
- T-003 accepted at 5584461 after explicit-config retry: offline discovery found 80 cases (16 routes × 5 viewports), and orchestrator desktop Chromium smoke passed 16/16. Auth redirects are allowed by those smoke assertions; deeper authenticated state coverage remains queued.
- T-003 first attempt reported PASSED, but its verify command discovered 16 tests without loading the five-project config; target files were removed and W3 will retry once with explicit `--config`, which must discover 80.
- T-005 accepted at 889de7b: accessible partial-state notice added; typecheck passed. Taste check: existing ui.tsx exceeds 300 lines and the new component is not yet used by a screen; integration remains queued.
- 2026-10-21 queue preparation: installed frontend devDependencies `@playwright/test` ^1.64.1 for route/state/accessibility/responsive E2E and `@axe-core/playwright` ^4.14.0 for accessibility assertions using `npm --prefix frontend install --save-dev @playwright/test @axe-core/playwright`; Chromium install requested with `npm --prefix frontend exec -- playwright install chromium`. No other dependency added.
- No aggregate score or completion claim; acceptance, E2E and axe hard gates remain unresolved.
- Acceptance requires round 3 of "ApexGrid World Series", which has no events: missing seed data, not a code defect. Existing demo archives were not altered by checks.
- Production frontend image omits source and lint config; typecheck and lint run on the host only. Host Python 3.14 / Node 26 differ from Dockerfile Python 3.12 / Node 22.
- T-001 accepted at `7fefa04`; T-010 accepted at `f2d7054` after offline motion lint passed. The old build gate hit a Turbopack port restriction.
- Updated kit lint baseline: motion 0, banned 0, spacing 1 (real off-scale CSS plus border-width false positives). Workspace write check passed.
- `localStorage` bearer token and local JWT fallback require a deployment-context decision before auth transport changes.
- Worker queue is in `NEXT_STATE.md`; T-001, T-010 and T-004 are accepted.
