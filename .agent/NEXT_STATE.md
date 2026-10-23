# NEXT_STATE
updated_at: 2026-10-23
phase: 3 T331 extraction; Phase5 T360 lints / T361accepted (Phases0–2 complete; baseline51.2974)

## Queue
### T-44180 W2 — OPEN
- target_files: backend/app/api/dbms_sql.py, backend/app/main.py
- contract: T331 move unchanged constraint_demo and transaction_demo handlers into SQL router; preserve authorization, rollback logic, response and precise connection typing.
- verify: env APP_ENV=local PYTHONPATH=backend .venv/bin/python -c 'import ast,importlib,inspect,subprocess; old=ast.parse(subprocess.check_output(["git","show","b886991:backend/app/main.py"],text=True)); module=importlib.import_module("backend.app.api.dbms_sql"); tree=ast.parse(inspect.getsource(module)); main=importlib.import_module("backend.app.main"); routes=[r for outer in main.app.routes for r in (outer.original_router.routes if hasattr(outer,"original_router") else [outer])]; names=("constraint_demo","transaction_demo"); original={n.name:n for n in old.body if isinstance(n,ast.FunctionDef) and n.name in names}; moved={n.name:n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name in names}; [(setattr(original[n],"decorator_list",[]),setattr(moved[n],"decorator_list",[])) for n in names]; assert all(ast.dump(original[n])==ast.dump(moved[n]) for n in names); assert all(sum(getattr(r,"endpoint",None) is getattr(main,n) for r in routes)==1 for n in names); print("PASS exact transaction/constraint handlers and aliases")' && env APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_contract_snapshot.py && .venv/bin/ruff check backend/app/main.py backend/app/api/dbms_sql.py && .venv/bin/ruff format --check backend/app/main.py backend/app/api/dbms_sql.py

### T-44179 W3 — OPEN
- target_files: scripts/eval/neo_motion.py, scripts/eval/rules/motion.good.css, scripts/eval/rules/motion.bad.css
- contract: T360 motion rule foundation: typed static CSS transition validator and plinth regression fixtures. Wrapper integration follows next atomic child.
- verify: env PYTHONPATH=. .venv/bin/python scripts/eval/neo_motion.py --self-test && .venv/bin/ruff check scripts/eval/neo_motion.py && .venv/bin/ruff format --check scripts/eval/neo_motion.py && .venv/bin/mypy --strict --explicit-package-bases scripts/eval/neo_motion.py

## Deferred
- T-44132 (W3, before claiming P-3): bundle checker counts only rootMainFiles+page chunk, omitting layout/shared dependency assets; add fixture regression and measure fullinitial asset graph with unchanged170KB threshold.

## Done
- T-44178 acceptedb886991; verify0.
- T-44177 acceptedb549015; verify0.
- T-44175 acceptedd0e50ef; verify0.
- T-44173 accepted66c4550; verify0.
- T-44176 accepted9d8cae0; verify0.
- T-44174 accepted1356d28; verify0.
- T-44172 accepted4b411cc; verify0.
- T-44171 accepted7b1c487; verify0.
- T-44169 accepted20e9e21; verify0.
- T-44167 accepted6c04161; verify0.
- T-44170 accepted31a3bd4; verify0.
- T-44168 accepted4e8f466; verify0.
- T-44166 accepted64214d6; verify0.
- T-44165 acceptedb395e35; verify0.
- T-361 accepted1e61efd; verify0.
- T-44164 accepted4c4f401; verify0.
- T-44163 acceptedb1fec1c; verify0.
- T-44162 accepted9335c83; verify0.
- T-44159 accepted10b17c4; verify0.
- T-44161 accepted0adc5bb; verify0.
- T-44160 accepted553ed00; verify0.
- T-44158 acceptedcec7835; verify0.
- T-44157 accepted4f53ecd; verify0.
- T-44156 accepted049a179; verify0.
- T-44155 accepted7768158; verify0.
- T-44154 accepted882e5ed; verify0.
- T-44153 accepteda1eea31; verify0.
- T-44152 accepted47fc39d; verify0.
- Older accepted tasks: git history and CURRENT_STATE phase summaries.
