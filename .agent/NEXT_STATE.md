# NEXT_STATE
updated_at: 2026-10-24
phase: 3 T331 extraction + 6 shell; Phases0–2 and5 COMPLETE; no current score

## Queue
### T-44234 W1 — OPEN
- target_files: frontend/app/styles/shell.css, frontend/app/layout.tsx
- contract: T370 stage scoped shell stylesheet, preserving legacy route styles until activation.
- verify: bash scripts/eval/lint-spacing.sh && bash scripts/eval/lint-banned.sh && bash scripts/eval/lint-motion.sh && bash scripts/eval/lint-neobrutal.sh && npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0

### T-44233 W2 — OPEN
- target_files: backend/app/main.py
- contract: T331 wire staged lock/recalculate router and remove old endpoint bodies.
- verify: env APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_contract_snapshot.py backend/tests/test_route_registration.py && env APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_api.py -k "decision or incident" && .venv/bin/ruff check backend/app backend/tests && .venv/bin/ruff format --check backend/app/main.py backend/app/api/dbms_lock.py

## Blocked
- None currently. Owner5.6/high override2bc94fb verified byfreshsuccessfulworkers.

## Deferred
- T-44132 (W3, before claiming P-3): bundle checker counts only rootMainFiles+page chunk, omitting layout/shared dependency assets; add fixture regression and measure fullinitial asset graph with unchanged170KB threshold.

## Done
- Phase5 T360–T366 complete; parent d666cf6/b90911f/b18819f, root60 browser PASS, build/lint/types/CSS gates0, production guide hidden.
- T44232 c6787b1 staged lock/recalculate router; T44229 c2616e0 helper wiring full227 PASS/live PASS.
- T44230 fdb63e2 target44px; T44231 e6efcc1 FLIP; T44225 54449f5 and T44226 4b35c7a browser specs accepted.
- Earlier child task history/evidence in git and CURRENT_STATE; remaining task inventory docs/overhaul-plan.md.
