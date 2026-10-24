# NEXT_STATE
updated_at: 2026-10-24
phase: 3 T331 + 7 route redesign; Phases0–2,5–6 COMPLETE; no current score

## Queue
### T-44271 W1 — OPEN
- target_files: frontend/app/login/page.tsx, frontend/app/styles/login.css
- contract: T380 adopt accepted form primitives in login while preserving auth logic and all tested copy.
- verify: bash scripts/eval/lint-spacing.sh && bash scripts/eval/lint-banned.sh && bash scripts/eval/lint-motion.sh && bash scripts/eval/lint-neobrutal.sh && npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0

### T-44270 W2 — OPEN
- target_files: backend/app/main.py
- contract: T331 wire accepted pit write router and remove three old handlers, preserving legacy aliases and late-bound dependencies.
- verify: env APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_contract_snapshot.py backend/tests/test_route_registration.py && .venv/bin/ruff check backend/app backend/tests && .venv/bin/ruff format --check backend/app/main.py

## Blocked
- None currently. Owner5.6/high override2bc94fb verified byfreshsuccessfulworkers.

## Deferred
- T-44132 (W3, before claiming P-3): bundle checker counts only rootMainFiles+page chunk, omitting layout/shared dependency assets; add fixture regression and measure fullinitial asset graph with unchanged170KB threshold.

## Done
- T-44268 accepted6590437; verify0.
- T-44269 accepteded34d9d; verify0.
- Phase6 T370 da5a72d/T3718e498d7;481 browser checks, build/static gates0; details CURRENT_STATE and evidence logs.
- T44266 LoginArt/CSS622aafa staged; T44267 reservation servicee5507c9 staged.
- Session lifecycle wired94a7009; full231 PASS0skip/live PASS.
- Earlier accepted task/evidence history in git and .agent/results; remaining graph docs/overhaul-plan.md.
