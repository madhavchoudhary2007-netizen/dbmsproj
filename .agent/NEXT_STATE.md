# NEXT_STATE
updated_at: 2026-10-27
branch: overhaul/neo-brutal
execution: RUNNING; implementing docs/completion-plan.md
phase: security/DBMS, isolated acceptance, then phases 9–11

Accepted work and commit hashes are in CURRENT_STATE and git log. The real-stack spec is committed; preserve the untracked owner packet T-411.

### T-44662 — Live timing and steward browser coverage
- worker: W3 | priority: P1 | state: ACCEPTED aa1dc05
- target_files: frontend/e2e/real-stack.spec.ts
- verify: npm --prefix frontend run typecheck

### T-44663 — Pit reservation service behavior
- worker: W3 | priority: P1 | state: ACCEPTED 5023715
- target_files: backend/tests/test_pit_reservation_service_cases.py
- verify: APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q -p no:cacheprovider backend/tests/test_pit_reservation_service_cases.py

### T-44664 — Steward decisions and incident behavior
- worker: W3 | priority: P1 | state: ACCEPTED 21cb18d
- target_files: backend/tests/test_steward_cases.py
- verify: APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q -p no:cacheprovider backend/tests/test_steward_cases.py

### T-44665 — Simulation control behavior
- worker: W3 | priority: P1
- target_files: backend/tests/test_simulation_control_cases.py
- verify: APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q -p no:cacheprovider backend/tests/test_simulation_control_cases.py

### T-44666 — Live WebSocket behavior
- worker: W3 | priority: P1
- target_files: backend/tests/test_live_websocket_cases.py
- verify: APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q -p no:cacheprovider backend/tests/test_live_websocket_cases.py

### T-44667 — State and plan checkpoint
- worker: orchestrator | priority: P1
- target_files: .agent/CURRENT_STATE.md, .agent/NEXT_STATE.md, docs/completion-plan.md
- verify: bash scripts/agent/verify-lock.sh && bash scripts/agent/budget.sh && git diff --check -- .agent/CURRENT_STATE.md .agent/NEXT_STATE.md docs/completion-plan.md

## Next
- T-44647–50 accepted; root-run owned acceptance passed and no owned databases remained.
- Full disposable backend gate after T-44664: 478 passed, zero skipped; 76.88% coverage fails required 80%. Browser: 20 passed plus 2 corrected standings and 4 live/steward tests passed; concurrent recalculation yielded 409 once.
- Complete full disposable backend domain/coverage and migration replay (T-44629); do not mark complete on skips.
- T-44662 live timing and steward decision browser checks passed on owned stack. Complete visual, motion, state and viewport matrix T-412–415 and final candidate real-stack run.
- Complete CI parity, security audits and docs T-44632/33, T-420/421; run full evaluation T-430, cleanup T-431 and PR T-432.
- ADR-017: transaction-local role context relies on trusted application code; shared database credentials are not an independent identity boundary.
