# CURRENT_STATE
updated_at: 2026-10-21T12:16:50Z
git_head: 8bde3fe
branch: master
architect_sha256: e7722a81b4f2c708f019b3468c0a9630411ea6df88eb85aa37a7aff6ffc523a9
archetype: enterprise-saas (5 signals); developer-tool secondary (3)
last_eval_score: NOT_RUN (install, full DB tests and browser E2E hard gates unresolved)

## Verified setup and baseline
- Existing ApexGrid product committed as `ccab46d`; kit committed as `79cae60`; architecture locked as `8bde3fe`; `verify-lock.sh` passed.
- `boot.sh --probe` returned OK for `gpt-6-sol` and `gpt-6-luna`; final boot printed `boot OK`. The probe checked IDs, not the worker `high` effort binding.
- `.agent/commands.env` now uses root-runnable npm frontend commands, venv pytest and `E2E_CMD=none`.
- Install exit 1: impossible `httpx2>=0.28,<1` in `backend/requirements-dev.txt`. Typecheck exit 0; lint exit 0; build exit 0.
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

## Known invariants
- `0 <= session.total_laps <= 72`; session state/timestamp transitions enforced in SQL (`backend/migrations/001_initial.sql`).
- One result per session/driver and one classified position; one active reservation per driver/session; overlapping box windows rejected.
- PostgreSQL owns official records; MongoDB owns telemetry; cross-store failure must be visible as partial data, not hidden.

## Orchestrator direct edits
- 2026-10-21: configuration, `.gitignore`, `.agent/ARCHITECT.md`, and state files only; 0 product-source lines.

## Open risks
- No aggregate score or completion claim; install, full integration, E2E and axe hard gates remain unresolved.
- Acceptance requires round 3 of "ApexGrid World Series", which has no events: missing seed data, not a code defect. Existing demo archives were not altered by checks.
- Production frontend image omits source and lint config; typecheck and lint run on the host only. Host Python 3.14 / Node 26 differ from Dockerfile Python 3.12 / Node 22.
- `localStorage` bearer token and local JWT fallback require a deployment-context decision before auth transport changes.
- Worker queue is in `NEXT_STATE.md`; no workers dispatched or accepted.
