# NEXT_STATE
updated_at: 2026-10-23
phase: 1 honest green baseline

## Queue
### T-311 — full test/frontend lint milestone
- worker: W3 | priority: P1 | origin: plan3 Phase1
- target_files: backend/tests/test_api.py, backend/tests/test_database.py, scripts/eval/verify-bundle-size.py
- contract: verify-only, no edits; full plan lint command0
- verify: .venv/bin/ruff check backend/tests && npm --prefix frontend run lint -- --max-warnings 0
### T-44107 — demo/config lint cleanup
- worker: W2 | priority: P1 | origin: bounded T-310 subdivision
- target_files: backend/app/demo_race_repository.py, backend/app/config.py, pyproject.toml
- contract: preserve all defaults/guards/SQL; narrow false-positive comments only, <=150
- verify: .venv/bin/ruff check backend/app/demo_race_repository.py backend/app/config.py && .venv/bin/ruff format --check backend/app/demo_race_repository.py backend/app/config.py
## Blocked
- T-310/T-311 remain open until full parent Ruff/format/frontend-lint commands exit0; no intermediate count is a parent pass.
- T-440 (O, before motion packets): align plan2.3/2.7 with owner100–300ms and display>=48px leading limits; those conflicting catalogue specifications are missing a correction task.
- T-441 (W3, before T-360 palette change): add heading-contrast regression for real contrast<=1, preserving4.5 threshold and excluding aria-hidden decorative duplicates only; current >1 filter omits failures.

## Done
- T-44109 acceptedd9258cb; verify0.
- T-44105 accepted41a5b46; verify0.
- T-44108 accepteda893c67; verify0.
- T-44106 acceptedc6e5749; verify0.
- T-44103 accepted307771a; verify0.
- T-44104 accepted639e5a9; verify0.
- T-44102 accepted111241c; verify0.
- T-44101 accepted19620dd; verify0.
- T-44100 accepted121a209; verify0.
- T-4499 accepted73599b2; verify0.
- T-4498 acceptedd8abb08; verify0.
- T-4497 acceptedf941fc9; verify0.
- T-4496 accepted293ac25; verify0.
- T-4495 acceptedadc090f; verify0.
- T-4494 accepted4ce3333; verify0.
- T-4493 accepted5218003; verify0.
- T-4492 accepteda928c9c; verify0.
- T-4491 accepted6e710b3; verify0.
- T-4490 accepted1f55cb6; verify0.
- T-4489 acceptedab5592b; verify0.
- T-4488 accepted918245b; verify0.
- T-4487 acceptedb5afb5a; verify0.
- T-4486 accepteda141bc4; verify0.
- T-4485 acceptede2d86a7; verify0.
- T-4484 accepted2cc09da; verify0.
- T-4482 accepteda20f2a0; verify0.
- T-4483 acceptedbfad8d0; verify0.
- T-4481 accepted2cf7b01; verify0.
- T-4480 accepted4a3ab7f; verify0.
- Phase0 T-300/T-301/T-302 accepted; ADR007 activated.
- Phase1 children T-442..T-460 accepted where recorded in CURRENT_STATE/git; T-450/T-461 were not dispatched. Parent T-310/T-311 remain open.
- Latest T-46012e8ea1 database tests full Ruff/format0 and unchangedAST; T-4595601bbd bootstrap format unchangedAST.
