# NEXT_STATE
updated_at: 2026-10-23
phase: 3 API contract guard (Phases0–2 complete; baseline score51.2974)

## Queue
### T-44175 W3 — OPEN
- target_files: scripts/eval/neo_contrast.py, scripts/eval/rules/contrast.good.css, scripts/eval/rules/contrast.bad.css
- contract: T360 white-on-red rule: add typed co-occurrence checker plus good/bad fixtures for the forbidden white foreground on #FF6B6B. Covers explicit CSS declarations, inline JS style objects and literal Tailwind class strings. Dynamic cascade remains covered by browser AA checks; do not pretend static text proves all computed styles.
- verify: env PYTHONPATH=. .venv/bin/python scripts/eval/neo_contrast.py --self-test && .venv/bin/ruff check scripts/eval/neo_contrast.py && .venv/bin/ruff format --check scripts/eval/neo_contrast.py && .venv/bin/mypy --strict scripts/eval/neo_contrast.py

### T-44174 W2 — OPEN
- target_files: backend/app/api/dbms_sql.py, backend/app/main.py
- contract: T331 SQL metadata handler moves: extend existing SQL router factory with unchanged dbms_indexes and dbms_locks handlers, preserving main aliases and all SQL/role/query/response behavior. Remove the original duplicate decorators/defs from main.
- verify: env APP_ENV=local PYTHONPATH=backend .venv/bin/python -c 'import ast,importlib,inspect,subprocess; names=("dbms_indexes","dbms_locks"); old=ast.parse(subprocess.check_output(["git","show","31a3bd4:backend/app/main.py"],text=True)); originals={n.name:n for n in old.body if isinstance(n,ast.FunctionDef) and n.name in names}; module=importlib.import_module("backend.app.api.dbms_sql"); moved={n.name:n for n in ast.walk(ast.parse(inspect.getsource(module))) if isinstance(n,ast.FunctionDef) and n.name in names}; [setattr(n,"decorator_list",[]) for n in list(originals.values())+list(moved.values())]; assert all(ast.dump(originals[n])==ast.dump(moved[n]) for n in names); main=importlib.import_module("backend.app.main"); routes=[r for outer in main.app.routes for r in (outer.original_router.routes if hasattr(outer,"original_router") else [outer])]; assert all(sum(getattr(r,"endpoint",None) is getattr(main,n) for r in routes)==1 for n in names); print("PASS exact metadata handlers and aliases")' && env APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_contract_snapshot.py && .venv/bin/ruff check backend/app/main.py backend/app/api/dbms_sql.py && .venv/bin/ruff format --check backend/app/main.py backend/app/api/dbms_sql.py

### T-44173 W3 — OPEN
- target_files: scripts/eval/neo_shadow.py, scripts/eval/rules/shadow.good.css, scripts/eval/rules/shadow.bad.css
- contract: T360 shadow-rule foundation: add typed literal hard-shadow validator/checker and good/bad fixtures. Enforce zero blur/spread, pure black and offsets<=16px; support max_offset=8 for mobile callers. Shared scanner/mobile integration follows next child; do not claim full T360 complete yet.
- verify: env PYTHONPATH=. .venv/bin/python scripts/eval/neo_shadow.py --self-test && .venv/bin/ruff check scripts/eval/neo_shadow.py && .venv/bin/ruff format --check scripts/eval/neo_shadow.py && .venv/bin/mypy --strict scripts/eval/neo_shadow.py

## Deferred
- T-44132 (W3, before claiming P-3): bundle checker counts only rootMainFiles+page chunk, omitting layout/shared dependency assets; add fixture regression and measure fullinitial asset graph with unchanged170KB threshold.

## Done
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
