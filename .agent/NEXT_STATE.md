# NEXT_STATE
updated_at: 2026-10-23
phase: 3 API contract guard (Phases0–2 complete; baseline score51.2974)

## Queue
### T-44172 W2 — OPEN
- target_files: backend/app/api/dbms_sql.py, backend/app/main.py
- contract: T331 DBMS SQL module first move: extract dbms_schema verbatim to a typed router factory in api/dbms_sql.py, retaining main.dbms_schema and live query/serializer callback bindings. No SQL, response or authorization changes. Future children move the remaining SQL handlers into this same factory before T332 removes factories.
- verify: env APP_ENV=local PYTHONPATH=backend .venv/bin/python -c 'import ast,importlib,inspect,subprocess; old=ast.parse(subprocess.check_output(["git","show","31a3bd4:backend/app/main.py"],text=True)); a=next(n for n in old.body if isinstance(n,ast.FunctionDef) and n.name=="dbms_schema"); a.decorator_list=[]; module=importlib.import_module("backend.app.api.dbms_sql"); b=next(n for n in ast.walk(ast.parse(inspect.getsource(module))) if isinstance(n,ast.FunctionDef) and n.name=="dbms_schema"); b.decorator_list=[]; assert ast.dump(a)==ast.dump(b); main=importlib.import_module("backend.app.main"); routes=[r for outer in main.app.routes for r in (outer.original_router.routes if hasattr(outer,"original_router") else [outer])]; chosen=[r for r in routes if getattr(r,"path",None)=="/api/dbms/schema"]; assert len(chosen)==1 and chosen[0].endpoint is main.dbms_schema; print("PASS original schema handler and endpoint alias")' && env APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_contract_snapshot.py && .venv/bin/ruff check backend/app/main.py backend/app/api/dbms_sql.py && .venv/bin/ruff format --check backend/app/main.py backend/app/api/dbms_sql.py

### T-44171 W3 — OPEN
- target_files: scripts/eval/lint-neobrutal.sh
- contract: T360 scanner wiring: integrate accepted blur, gradient and weight rule modules into the shared neo-brutal scanner and its --self-test. Existing radius/gray rules and assertions stay intact. No UI changes.
- verify: bash scripts/eval/lint-neobrutal.sh --self-test && .venv/bin/ruff check scripts/eval/source_text.py scripts/eval/neo_colour.py scripts/eval/neo_effects.py scripts/eval/neo_gradient.py scripts/eval/neo_weight.py && .venv/bin/mypy --strict --explicit-package-bases scripts/eval/source_text.py scripts/eval/neo_colour.py scripts/eval/neo_effects.py scripts/eval/neo_gradient.py scripts/eval/neo_weight.py

## Deferred
- T-44132 (W3, before claiming P-3): bundle checker counts only rootMainFiles+page chunk, omitting layout/shared dependency assets; add fixture regression and measure fullinitial asset graph with unchanged170KB threshold.

## Done
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
