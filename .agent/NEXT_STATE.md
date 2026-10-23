# NEXT_STATE
updated_at: 2026-10-23
phase: 1 honest green baseline

## Queue
### T-451 — test imports and unused loop variable
- worker: W3 | priority: P1 | origin: T-311 subdivision
- target_files: backend/tests/test_api.py
- contract: import sorting and unused tick rename only; no assertions or fixture changes
- verify: .venv/bin/ruff check --select I,B007 backend/tests/test_api.py
### T-448 — bounded Phase1 cleanup
- worker: W2 | priority: P1 | origin: T-310/311 atomic subdivision
- target_files: backend/app/pit_repository.py, backend/app/telemetry_repository.py, backend/app/race_archive.py
- contract: Atomic T-310 subdivision: Ruff-clean and format these three files without behavior changes, <=150 changed lines. Preserve every SQL/JSON/archive shape. Split long SQL/string literals with implicit concatenation preserving exact runtime strings. race_archive random.Random is intentionally deterministic non-security race simulation; a single inline noqa:S311 with that specific justification is permitted, never blanket suppression. No other rule suppression.
- verify: .venv/bin/ruff check backend/app/pit_repository.py backend/app/telemetry_repository.py backend/app/race_archive.py && .venv/bin/ruff format --check backend/app/pit_repository.py backend/app/telemetry_repository.py backend/app/race_archive.py

## Blocked
- T-310/T-311 remain open until full parent Ruff/format/frontend-lint commands exit0; no intermediate count is a parent pass.
- T-440 (O, before motion packets): align plan2.3/2.7 with owner100–300ms and display>=48px leading limits; those conflicting catalogue specifications are missing a correction task.
- T-441 (W3, before T-360 palette change): add heading-contrast regression for real contrast<=1, preserving4.5 threshold and excluding aria-hidden decorative duplicates only; current >1 filter omits failures.

## Done
- T-449 acceptedc728e2a; AST preserved, range200-300 format0 after one scope repair.
- T-447 accepted9731af5; range-format0/exact AST unchanged.
- T-446 acceptedc9ab8a1; three routers Ruff/format0 and unchanged OpenAPI.
- T-445 accepted2c4ffd3; SQL exception assertions narrowed, selected eight lint hits removed.
- T-444 accepted87025ef; routers Ruff/format0, OpenAPI unchanged; full batch gate next.
- T-443 accepted6cca3aa; frontend lint/typecheck+three existing scripts green; neo lint not yet present.
- T-302 accepted59a180e; explicit owner approval recorded and lock verified.
- T-442 accepted7bdbf4c; three files Ruff/format green, disposable full gate running.
- T-300 accepted e465e89; boot exit0, lock/budgets pass, boot OK.
- T-301 accepted13e6100; ADR-007 proposed, focused five-lens review, lock80f8ab50 verified; no product/gate edits.
### T-301 — completed architecture amendment; state checkpoint
- target_files: .agent/ARCHITECT.md, .agent/adr/ADR-007-neo-brutal-motorsport-light-overhaul.md
- verify: bash scripts/agent/verify-lock.sh
- status: ACCEPTED13e6100; retain target declaration for accept.sh-only state checkpoint.
