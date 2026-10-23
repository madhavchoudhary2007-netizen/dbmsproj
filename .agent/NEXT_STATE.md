# NEXT_STATE
updated_at: 2026-10-23
phase: 3 T331 extraction; Phase5 T360 lints / T361accepted (Phases0–2 complete; baseline51.2974)

## Queue
### T-44188 W2 — OPEN
- target_files: backend/app/api/dbms_mongo.py, backend/app/main.py
- contract: T331 move unchanged Mongo paged-document handler into existing Mongo router registration with precise Database callback.
- verify: env APP_ENV=local PYTHONPATH=backend .venv/bin/python -c 'import ast,importlib,inspect,subprocess; old=ast.parse(subprocess.check_output(["git","show","9977cdf:backend/app/main.py"],text=True)); a=next(n for n in old.body if isinstance(n,ast.FunctionDef) and n.name=="dbms_mongo_collection_documents"); a.decorator_list=[]; module=importlib.import_module("backend.app.api.dbms_mongo"); b=next(n for n in ast.walk(ast.parse(inspect.getsource(module))) if isinstance(n,ast.FunctionDef) and n.name=="dbms_mongo_collection_documents"); b.decorator_list=[]; assert ast.dump(a)==ast.dump(b); main=importlib.import_module("backend.app.main"); routes=[r for outer in main.app.routes for r in (outer.original_router.routes if hasattr(outer,"original_router") else [outer])]; assert sum(getattr(r,"endpoint",None) is main.dbms_mongo_collection_documents for r in routes)==1; print("PASS exact Mongo documents handler and alias")' && env APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_contract_snapshot.py backend/tests/test_route_registration.py && .venv/bin/ruff check backend/app/main.py backend/app/api/dbms_mongo.py && .venv/bin/ruff format --check backend/app/main.py backend/app/api/dbms_mongo.py

## Deferred
- T-44132 (W3, before claiming P-3): bundle checker counts only rootMainFiles+page chunk, omitting layout/shared dependency assets; add fixture regression and measure fullinitial asset graph with unchanged170KB threshold.

## Done
- T-44187 accepted3c10f63; verify0.
- T-44189 accepted3343d87; verify0.
- T-44186 accepted9977cdf; verify0.
- T-44185 accepted030459a; verify0.
- T-44183 acceptedf385ea8; verify0.
- T-44184 accepted008414f; verify0.
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
- Older accepted tasks: git history and CURRENT_STATE phase summaries.
