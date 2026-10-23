# NEXT_STATE
updated_at: 2026-10-23T08:00:00Z
loop_iteration: 0 of 8

## Queue (owner override; top-down; <=3 target files and <=150 changed lines per task)
### T-177 — first evaluation functional dimension
- worker: W3 | priority: P1 | origin: EVAL first full-gates
- target_files: .agent/eval/functional.json
- contract: score F-1..F-6 from first full-gates and browser coverage evidence, mark unproven as false, NOT_RUN only unavailable tool
- verify: jq -e '([.checks[].id] | sort)==(["F-1","F-2","F-3","F-4","F-5","F-6"] | sort)' .agent/eval/functional.json
### T-178 — first evaluation aesthetic dimension
- worker: W3 | priority: P1 | origin: EVAL first full-gates
- target_files: .agent/eval/aesthetic.json
- contract: score A-1..A-7 from three lint scripts and browser evidence; A-5/A-6 false pending orchestrator Taste review
- verify: jq -e '([.checks[].id] | sort)==(["A-1","A-2","A-3","A-4","A-5","A-6","A-7"] | sort)' .agent/eval/aesthetic.json
### T-179 — first evaluation performance dimension
- worker: W3 | priority: P1 | origin: EVAL first full-gates
- target_files: .agent/eval/performance.json
- contract: score P-1..P-6; Lighthouse missing tool may be NOT_RUN, axe matrix from browser gate
- verify: jq -e '([.checks[].id] | sort)==(["P-1","P-2","P-3","P-4","P-5","P-6"] | sort)' .agent/eval/performance.json
### T-180 — first evaluation edge dimension
- worker: W3 | priority: P1 | origin: EVAL first full-gates
- target_files: .agent/eval/edge.json
- contract: score E-1..E-5 from state/viewport/journey tests and actual gate results
- verify: jq -e '([.checks[].id] | sort)==(["E-1","E-2","E-3","E-4","E-5"] | sort)' .agent/eval/edge.json

## Blocked
- T-006: twice FAILED. Initial packet omitted `special-pages.tsx`; retry asserted empty/partial states without a screen-specific filter/list contract. No test accepted; requires a route-specific applicability matrix before new work.
- T-026/T-027/T-028: depend on blocked T-006 state matrix.
- T-019: frontend runner lacks source; test in builder stage.
- T-014: split into ADR-002 backend/frontend/browser/acceptance packets T-050..055; implementation follows reproducing tests.

## Done this iteration (recent; older accepted evidence in git/LOOP.md)
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
- T-168 ✓ 098a9c2; 4 pass/2 strict xfail, --runxfail exposed successful-login 429.
- T-163 ✓ 2bb95f8; focused 4/4, full isolated 90 pass/35 fail from counting successful logins; repair T-168/169.
- T-162 ✓ 6963b4f; 1 pass/3 strict xfails; --runxfail proved 3 missing-429 failures.
- T-161 ✓ 97c7268; session action characterization passed.
- T-160 ✓ 8b60194; membership router/repository split accepted, full isolated backend 120/0/0.
