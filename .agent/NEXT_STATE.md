# NEXT_STATE
updated_at: 2026-10-23
phase: 1 honest green baseline

## Queue
### T-446 — T-310 remaining small router lint
- worker: W2 | priority: P1 | origin: bounded subdivision T-310
- target_files: backend/app/user_router.py, backend/app/membership_router.py, backend/app/telemetry_router.py
- contract: dependency-default cleanup and equivalent error map to meet C901, formatting; no wire/API changes
- verify: .venv/bin/ruff check backend/app/user_router.py backend/app/membership_router.py backend/app/telemetry_router.py && .venv/bin/ruff format --check backend/app/user_router.py backend/app/membership_router.py backend/app/telemetry_router.py
### T-447 — T-311 database test format slice
- worker: W3 | priority: P1 | origin: bounded subdivision T-311
- target_files: backend/tests/test_database.py
- contract: format first180 source lines only, <=150 changed lines; exact AST preserved, parent full Ruff gate stays open
- verify: .venv/bin/ruff format --check --range 1-180 backend/tests/test_database.py && .venv/bin/python -c 'import ast,pathlib,subprocess; p="backend/tests/test_database.py"; assert ast.dump(ast.parse(pathlib.Path(p).read_text())) == ast.dump(ast.parse(subprocess.check_output(["git","show","HEAD:"+p],text=True)))'

## Blocked
- T-310/T-311 remain open until full parent Ruff/format/frontend-lint commands exit0; no intermediate count is a parent pass.
- T-440 (O, before motion packets): align plan2.3/2.7 with owner100–300ms and display>=48px leading limits; those conflicting catalogue specifications are missing a correction task.
- T-441 (W3, before T-360 palette change): add heading-contrast regression for real contrast<=1, preserving4.5 threshold and excluding aria-hidden decorative duplicates only; current >1 filter omits failures.

## Done
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
