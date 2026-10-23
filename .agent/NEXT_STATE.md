# NEXT_STATE
updated_at: 2026-10-23T08:05:00Z
loop_iteration: 0 of 8

## Queue (owner override; top-down; <=3 target files and <=150 changed lines per task)
### T-186 — type NavItem and NavGroup in frontend/components/shell.tsx
- worker: W1 | priority: P1 | origin: frontend typecheck gate
- target_files: frontend/components/shell.tsx
- contract: define NavItem tuple and NavGroup interface to resolve Link and span props
- verify: bash -c "cd frontend && npx eslint components/shell.tsx"
### T-187 — type snapshot and table rows in frontend/components/race-database.tsx
- worker: W1 | priority: P1 | origin: frontend typecheck gate
- target_files: frontend/components/race-database.tsx
- contract: type RaceSnapshot, selectedState, and asArray rows for DataTable
- verify: bash -c "cd frontend && npx eslint components/race-database.tsx"
### T-188 — type tableData and plan nodes in frontend/components/dbms-workspace.tsx
- worker: W1 | priority: P1 | origin: frontend typecheck gate
- target_files: frontend/components/dbms-workspace.tsx
- contract: resolve remaining TS types for overview, tableData, and readData
- verify: bash -c "cd frontend && npx eslint components/dbms-workspace.tsx"

## Blocked
- T-006: twice FAILED. Initial packet omitted `special-pages.tsx`; retry asserted empty/partial states without a screen-specific filter/list contract. No test accepted; requires a route-specific applicability matrix before new work.
- T-026/T-027/T-028: depend on blocked T-006 state matrix.
- T-019: frontend runner lacks source; test in builder stage.
- T-014: split into ADR-002 backend/frontend/browser/acceptance packets T-050..055; implementation follows reproducing tests.

## Done this iteration (recent; older accepted evidence in git/LOOP.md)
- T-185 ✓ 74b9811; added APP_ENV='local' to backend coverage invocation; 136/136 tests pass at 82% coverage.
- T-184 ✓ 0218106; eliminated 25 explicit any in special-pages.tsx; zero eslint errors/warnings.
- T-183 ✓ 6aa0756; eliminated 9 explicit any in dbms-workspace.tsx.
- T-182 ✓ 8f5f73e; eliminated 6 explicit any in shell.tsx and race-database.tsx.
- T-181 ✓ 63e1125; eliminated 5 explicit any in lib/api.ts.
- T-180 ✓ c7f2d45; scored edge dimension E-1..E-5; responsive 320/5120 passes, other checks open.
- T-179 ✓ 5a9941a; scored performance dimension P-1..P-6; Lighthouse not installed (NOT_RUN), bundle/invariants/axe open.
- T-178 ✓ d1e4d57; scored aesthetic dimension A-1..A-7; spacing lint 154 hits, banned/motion clean, palette/focal/motion open.
- T-177 ✓ d7e7385; recorded functional F-1..F-6 results; typecheck and build pass, lint and coverage replay open.
- T-176 ✓ 03e4839; focused 4/4, Ruff restored 540, mypy 222.
- T-175 ✓ 43b8914; engine/create/restore focused 4/4, mypy 222, Ruff +2 S311 repair T-176.
- T-167 ✓ a992b66; migration/repository focused 2/2, Ruff 540/mypy 222.
- T-166 ✓ 9a5aca1; 4 strict xfails; --runxfail 4 old-code failures, no DB/server.
- T-174 ✓ ca06899; exact older retry now 202 same ID, focused --runxfail 5/5; full rerun pending.
- T-173 ✓ fe8aabd; 4 pass/1 strict xfail, --runxfail proves older exact retry 409.
- T-172 ✓ 3051e13; seeded fixture derives forward packet from latest telemetry; Ruff passes, disposable rerun pending.
- T-165 ✓ f4c3e6e; focused --runxfail 4/4, Ruff 543/mypy 222; full isolated 130 pass/1 old fixture failure, T-172 queued.
- T-164 ✓ 80a2bc9; 1 ordinary pass/3 strict xfails; --runxfail 3 failures on old code.
- T-171 ✓ safe npm audit fix: Next/eslint 16.4.2; critical 0, high 7/moderate 2 deferred major-only; typecheck/build and isolated 127/0/0 pass.
- T-170 ✓ 8573293; mypy strict 222 baseline restored; Ruff 543, login 6/6.
- T-169 ✓ 4e88ceb; focused 6/6; full isolated backend 127/0/0 and live acceptance; mypy +1 repair T-170.
