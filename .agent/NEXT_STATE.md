# NEXT_STATE
updated_at: 2026-10-23T06:45:00Z
loop_iteration: 0 of 8

## Queue (owner override; top-down; <=3 target files and <=150 changed lines per task)
### T-166 — F-DOM-05 replay seed reproduction
- worker: W3 | priority: P2 | after: T-165
- target_files: backend/tests/test_simulation_replay.py
- contract: strict expected-failure seeded replay/persistence test; deterministic generated lap, gap and pit outputs after restart
- verify: APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_simulation_replay.py
### T-167 — F-DOM-05 persisted simulation seed
- worker: W2 | priority: P2 | after: T-166
- target_files: backend/app/demo_race_repository.py, backend/migrations/003_simulation_seed.sql
- contract: additive nullable seed persistence; generated grid choices use dedicated seeded RNG, legacy rows untouched
- verify: APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q --runxfail backend/tests/test_simulation_replay.py
### T-175 — F-DOM-05 seeded simulator and restore
- worker: W2 | priority: P2 | after: T-167
- target_files: backend/app/main.py, backend/app/simulation_core.py
- contract: new generated race passes/persists seed, restore loads seed, sector RNG stable by seed+driver+progress; explicit RNG wins
- verify: APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q --runxfail backend/tests/test_simulation_replay.py

## Blocked
- T-006: twice FAILED. Initial packet omitted `special-pages.tsx`; retry asserted empty/partial states without a screen-specific filter/list contract. No test accepted; requires a route-specific applicability matrix before new work.
- T-026/T-027/T-028: depend on blocked T-006 state matrix.
- T-019: frontend runner lacks source; test in builder stage.
- T-014: split into ADR-002 backend/frontend/browser/acceptance packets T-050..055; implementation follows reproducing tests.

## Done this iteration (recent; older accepted evidence in git/LOOP.md)
- T-174 ✓ ca06899; exact older retry now 202 same ID, focused --runxfail 5/5; full rerun pending.
- T-173 ✓ fe8aabd; 4 pass/1 strict xfail, --runxfail proves older exact retry 409.
- T-172 ✓ 3051e13; seeded fixture derives forward packet from latest telemetry; Ruff passes, disposable rerun pending.
- T-165 ✓ f4c3e6e; focused --runxfail 4/4, Ruff 543/mypy 222; full isolated 130 pass/1 old fixture failure, T-172 queued.
- T-164 ✓ 80a2bc9; 1 ordinary pass/3 strict xfails; --runxfail 3 failures on old code.
- T-171 ✓ safe npm audit fix: Next/eslint 16.4.2; critical 0, high 7/moderate 2 deferred major-only; typecheck/build and isolated 127/0/0 pass.
- T-170 ✓ 8573293; mypy strict 222 baseline restored; Ruff 543, login 6/6.
- T-169 ✓ 4e88ceb; focused 6/6; full isolated backend 127/0/0 and live acceptance; mypy +1 repair T-170.
- T-168 ✓ 098a9c2; 4 pass/2 strict xfail, --runxfail exposed successful-login 429.
- T-163 ✓ 2bb95f8; focused 4/4, full isolated 90 pass/35 fail from counting successful logins; repair T-168/169.
- T-162 ✓ 6963b4f; 1 pass/3 strict xfails; --runxfail proved 3 missing-429 failures.
- T-161 ✓ 97c7268; session action characterization passed.
- T-160 ✓ 8b60194; membership router/repository split accepted, full isolated backend 120/0/0.
