# NEXT_STATE
updated_at: 2026-10-23
phase: 1 honest green baseline

## Queue
### T-4481 — demo delete guards format/literals
- worker: W2 | priority: P1 | origin: bounded T-310 subdivision
- target_files: backend/app/demo_race_repository.py
- contract: validate-demo-delete function only, exact whole AST/SQL, <=150 changes
- verify: .venv/bin/python -c 'import ast,pathlib,subprocess; p="backend/app/demo_race_repository.py"; src=pathlib.Path(p).read_text(); tree=ast.parse(src); assert ast.dump(tree)==ast.dump(ast.parse(subprocess.check_output(["git","show","HEAD:"+p],text=True))); f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="validate_demo_race_delete"); subprocess.run([".venv/bin/ruff","check","--select","E501","--stdin-filename",p,"-"],input=ast.get_source_segment(src,f),text=True,check=True)'
### T-4480 — disposable verifier process cleanup
- worker: W3 | priority: P1 | origin: missing plan task, repeated runtime lease blocker
- target_files: scripts/eval/db-baseline.sh
- contract: exec API child so cleanup waits actual PID; root full gate and no listener proof
- verify: bash -n scripts/eval/db-baseline.sh
## Blocked
- T-310/T-311 remain open until full parent Ruff/format/frontend-lint commands exit0; no intermediate count is a parent pass.
- T-440 (O, before motion packets): align plan2.3/2.7 with owner100–300ms and display>=48px leading limits; those conflicting catalogue specifications are missing a correction task.
- T-441 (W3, before T-360 palette change): add heading-contrast regression for real contrast<=1, preserving4.5 threshold and excluding aria-hidden decorative duplicates only; current >1 filter omits failures.

## Done
- Phase0 T-300/T-301/T-302 accepted; ADR007 activated.
- Phase1 children T-442..T-460 accepted where recorded in CURRENT_STATE/git; T-450/T-461 were not dispatched. Parent T-310/T-311 remain open.
- Latest T-46012e8ea1 database tests full Ruff/format0 and unchangedAST; T-4595601bbd bootstrap format unchangedAST.
