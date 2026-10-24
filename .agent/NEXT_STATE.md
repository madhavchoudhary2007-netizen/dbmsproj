# NEXT_STATE
updated_at: 2026-10-24
phase: 3 T331 + 7 route redesign; Phases0–2,5–6 COMPLETE; no current score

## Queue
### T-44280 W2 — OPEN
- target_files: backend/app/simulation_restore.py, backend/app/main.py
- contract: T331 extract exact auto-demo resume/create lifecycle into typed helper with late-bound compatibility wrapper.
- verify: env APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_contract_snapshot.py backend/tests/test_route_registration.py && env APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_api.py -k "restore or seeded" && .venv/bin/ruff check backend/app backend/tests && .venv/bin/ruff format --check backend/app/main.py backend/app/simulation_restore.py

### T-44279 W1 — OPEN
- target_files: frontend/app/globals.css, frontend/app/styles/login.css
- contract: T380 remove superseded global desktop login rules and consolidate necessary geometry into scoped login stylesheet.
- verify: bash scripts/eval/lint-spacing.sh && bash scripts/eval/lint-banned.sh && bash scripts/eval/lint-motion.sh && bash scripts/eval/lint-neobrutal.sh && npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0

## Blocked
- None currently. Owner5.6/high override2bc94fb verified byfreshsuccessfulworkers.

## Deferred
- T-44132 (W3, before claiming P-3): bundle checker counts only rootMainFiles+page chunk, omitting layout/shared dependency assets; add fixture regression and measure fullinitial asset graph with unchanged170KB threshold.

## Done
- T-44278 accepted3bade73; verify0.
- T-44277 accepted48bdf7b; verify0.
- T-44276 acceptedb8d5460; verify0.
- T-44275 accepted12449c7; verify0.
- T-44274 accepted7659085; verify0.
- T-44273 accepted1f7a2d7; verify0.
- T-44272 acceptedd7ece24; verify0.
- T-44271 accepteda98c95c; verify0.
- T-44270 accepted298fef5; verify0.
- T-44268 accepted6590437; verify0.
- T-44269 accepteded34d9d; verify0.
- Phase6 T370 da5a72d/T3718e498d7;481 browser checks, build/static gates0; details CURRENT_STATE and evidence logs.
- T44266 LoginArt/CSS622aafa staged; T44267 reservation servicee5507c9 staged.
- Session lifecycle wired94a7009; full231 PASS0skip/live PASS.
- Earlier accepted task/evidence history in git and .agent/results; remaining graph docs/overhaul-plan.md.
