# NEXT_STATE
updated_at: 2026-10-23
phase: 3 T331 extraction; Phase5 T360–T363verified, T364/T365inprogress (Phases0–2 complete; baseline51.2974)

## Queue
### T-44212 W2 — OPEN
- target_files: backend/app/main.py
- contract: T331 wire staged pure simulation tick into main and remove duplicate implementation.
- verify: env APP_ENV=local PYTHONPATH=backend .venv/bin/python -c 'import ast,importlib; source=ast.parse(open("backend/app/main.py").read()); assert not any(isinstance(n,ast.FunctionDef) and n.name=="advance_simulation_tick" for n in source.body); m=importlib.import_module("backend.app.main"); c=importlib.import_module("backend.app.core.simulation_tick"); assert m.advance_simulation_tick is c.advance_simulation_tick; assert hasattr(m,"Decision") and hasattr(m,"IncidentIn"); print("PASS direct tick alias, oldbody removed, model exports retained")' && env APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_contract_snapshot.py backend/tests/test_route_registration.py backend/tests/test_simulation_replay.py && env APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_api.py -k 'incident_decisions_always_return_current_driver_state or unsupported_sanction_fields_are_rejected_with_guidance or unsupported_sanction_zero_and_points_only_decisions_remain_valid' && .venv/bin/ruff check backend/app/main.py backend/app/core/simulation_tick.py && .venv/bin/ruff format --check backend/app/main.py backend/app/core/simulation_tick.py

### T-44215 W1 — OPEN
- target_files: frontend/components/nb/skeleton.tsx, frontend/components/nb/state.tsx
- contract: T365 delayed dimension-reserving skeleton and exhaustive five-state presentation boundary.
- verify: bash scripts/eval/lint-spacing.sh && bash scripts/eval/lint-banned.sh && bash scripts/eval/lint-motion.sh && bash scripts/eval/lint-neobrutal.sh && npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0

## Blocked
- Previous6Luna usage-limit blocker superseded byowner5.6/high authorization; availability pendingfirstdispatch.

## Deferred
- T-44132 (W3, before claiming P-3): bundle checker counts only rootMainFiles+page chunk, omitting layout/shared dependency assets; add fixture regression and measure fullinitial asset graph with unchanged170KB threshold.

## Done
- T-44211 accepted8275aab; verify0.
- T-44213 accepted471cb56; verify0.
- T-44210 accepted8ba857e; verify0.
- T-44214 accepted5ee4710; verify0.
- T-44208 accepted72a5b82; verify0.
- T-44209 accepted89c82af; verify0.
- T-44204 acceptede4a3f6c; verify0.
- T-44205 accepted65bd176; verify0.
- T-44203 accepted6eefdaa; verify0.
- T-44207 accepted2bc94fb; verify0.
- T-44206 accepted35ba591; verify0.
- T-44200 accepted47c0408; verify0.
- T-363 accepted13f614a; verify0.
- Recentaccepted tasks andevidence in CURRENT_STATE andgit history; earlierqueue fullyretained in docs/overhaul-plan.md.
