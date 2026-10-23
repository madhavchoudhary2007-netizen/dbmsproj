# NEXT_STATE
updated_at: 2026-10-23
phase: 1 honest green baseline

## Queue
### T-4483 — precise test-fixture lint exceptions
- worker: W3 | priority: P1 | origin: bounded T-311 subdivision
- target_files: backend/tests/test_api.py, pyproject.toml
- contract: inline specific false positives only, unchanged AST/assertions, config comments only
- verify: .venv/bin/ruff check --select S311,S105,S106 backend/tests/test_api.py
### T-4482 — CRUD factory complexity
- worker: W2 | priority: P1 | origin: bounded T-310 subdivision
- target_files: backend/app/main.py
- contract: reused payload/record helpers, same guards/messages/API, <=150 changes
- verify: .venv/bin/python -c 'import ast,pathlib,subprocess; p="backend/app/main.py"; s=pathlib.Path(p).read_text(); names={"_crud_write_payload","_require_crud_record","crud_routes"}; nodes=[n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef) and n.name in names]; assert len(nodes)==3; subprocess.run([".venv/bin/ruff","check","--select","C901","--stdin-filename",p,"-"],input=chr(10).join(ast.get_source_segment(s,n) for n in nodes),text=True,check=True)'
## Blocked
- T-310/T-311 remain open until full parent Ruff/format/frontend-lint commands exit0; no intermediate count is a parent pass.
- T-440 (O, before motion packets): align plan2.3/2.7 with owner100–300ms and display>=48px leading limits; those conflicting catalogue specifications are missing a correction task.
- T-441 (W3, before T-360 palette change): add heading-contrast regression for real contrast<=1, preserving4.5 threshold and excluding aria-hidden decorative duplicates only; current >1 filter omits failures.

## Done
- T-4481 accepted2cf7b01; verify0.
- T-4480 accepted4a3ab7f; verify0.
- Phase0 T-300/T-301/T-302 accepted; ADR007 activated.
- Phase1 children T-442..T-460 accepted where recorded in CURRENT_STATE/git; T-450/T-461 were not dispatched. Parent T-310/T-311 remain open.
- Latest T-46012e8ea1 database tests full Ruff/format0 and unchangedAST; T-4595601bbd bootstrap format unchangedAST.
