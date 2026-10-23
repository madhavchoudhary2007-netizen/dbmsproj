# NEXT_STATE
updated_at: 2026-10-23
phase: 3 T331 extraction; Phase5 T360 lints / T361accepted (Phases0–2 complete; baseline51.2974)

## Queue
### T-44184 W2 — OPEN
- target_files: backend/app/api/dbms_sql.py, backend/app/main.py
- contract: T331 move unchanged DBMS race-list handler into SQL router.
- verify: env APP_ENV=local PYTHONPATH=backend .venv/bin/python -c 'import ast,importlib,inspect,subprocess; old=ast.parse(subprocess.check_output(["git","show","86e0b47:backend/app/main.py"],text=True)); a=next(n for n in old.body if isinstance(n,ast.FunctionDef) and n.name=="dbms_races"); a.decorator_list=[]; module=importlib.import_module("backend.app.api.dbms_sql"); b=next(n for n in ast.walk(ast.parse(inspect.getsource(module))) if isinstance(n,ast.FunctionDef) and n.name=="dbms_races"); b.decorator_list=[]; assert ast.dump(a)==ast.dump(b); main=importlib.import_module("backend.app.main"); routes=[r for outer in main.app.routes for r in (outer.original_router.routes if hasattr(outer,"original_router") else [outer])]; assert sum(getattr(r,"endpoint",None) is main.dbms_races for r in routes)==1; print("PASS exact race list and alias")' && env APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_contract_snapshot.py && .venv/bin/ruff check backend/app/main.py backend/app/api/dbms_sql.py && .venv/bin/ruff format --check backend/app/main.py backend/app/api/dbms_sql.py

### T-44183 W3 — OPEN
- target_files: scripts/eval/palette.ts, scripts/eval/palette-core.ts
- contract: T360 A3 role-pixel gate: extract exact existing nearest-role scoring into reusable typed core, make existing palette CLI executable offline with installed frontend Sharp, and selftest thresholds.
- verify: node --experimental-strip-types scripts/eval/palette.ts --self-test

## Deferred
- T-44132 (W3, before claiming P-3): bundle checker counts only rootMainFiles+page chunk, omitting layout/shared dependency assets; add fixture regression and measure fullinitial asset graph with unchanged170KB threshold.

## Done
- T-44182 accepted86e0b47; verify0.
- T-44181 accepted20466aa; verify0.
- T-44179 acceptedc64e793; verify0.
- T-44180 accepted7c6c086; verify0.
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
