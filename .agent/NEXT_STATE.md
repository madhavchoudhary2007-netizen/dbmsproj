# NEXT_STATE
updated_at: 2026-10-23
phase: 1 honest green baseline

## Queue
### T-443 — T-311 typed performance fixture and tooling lint
- worker: W3 | priority: P1 | origin: missing atomic subdivision of T-311 (>3 files/150 lines)
- target_files: frontend/e2e/perf-fps.spec.ts, scripts/eval/verify-bundle-size.py
- contract: replace two explicit-any casts with precise browser memory types; Ruff-clean bundle checker; preserve every assertion/threshold
- verify: .venv/bin/ruff check scripts/eval/verify-bundle-size.py && .venv/bin/ruff format --check scripts/eval/verify-bundle-size.py && npm --prefix frontend run lint -- --max-warnings 0

## Blocked
- T-310/T-311 remain open until full parent Ruff/format/frontend-lint commands exit0; no intermediate count is a parent pass.
- T-440 (O, before motion packets): align plan2.3/2.7 with owner100–300ms and display>=48px leading limits; those conflicting catalogue specifications are missing a correction task.
- T-441 (W3, before T-360 palette change): add heading-contrast regression for real contrast<=1, preserving4.5 threshold and excluding aria-hidden decorative duplicates only; current >1 filter omits failures.

## Done
- T-302 accepted59a180e; explicit owner approval recorded and lock verified.
- T-442 accepted7bdbf4c; three files Ruff/format green, disposable full gate running.
- T-300 accepted e465e89; boot exit0, lock/budgets pass, boot OK.
- T-301 accepted13e6100; ADR-007 proposed, focused five-lens review, lock80f8ab50 verified; no product/gate edits.
### T-301 — completed architecture amendment; state checkpoint
- target_files: .agent/ARCHITECT.md, .agent/adr/ADR-007-neo-brutal-motorsport-light-overhaul.md
- verify: bash scripts/agent/verify-lock.sh
- status: ACCEPTED13e6100; retain target declaration for accept.sh-only state checkpoint.
