# NEXT_STATE
updated_at: 2026-10-23
phase: 3 API contract guard (Phases0–2 complete; baseline score51.2974)

## Queue
### T-44153 W3 — OPEN
- target_files: scripts/eval/source_text.py, scripts/eval/lint-neobrutal.sh
- contract: T360 foundation readability: extract sourcecommentmasking fromembeddedchecker into formatted reusable stdlibmodule scripts/eval/source_text.py. Sharedmask_comments(text:str,css:bool=False)->str preservesoffset/newlines/quotes andonlyJSlinecomments exactlycurrentbehavior. Checker callshelper, allradiuspatterns/selftests/fixtures/output remainunchanged. No additionalrulesyet.
- verify: bash scripts/eval/lint-neobrutal.sh --self-test && .venv/bin/ruff check scripts/eval/source_text.py && .venv/bin/ruff format --check scripts/eval/source_text.py && .venv/bin/mypy --strict scripts/eval/source_text.py

### T-44152 W2 — OPEN
- target_files: backend/app/core/serialization.py, backend/app/core/security.py, backend/app/main.py
- contract: T331 puremovechild2: move jsonable and telemetry_ws_payload verbatim tocore/serialization.py andwebsocket_bearer tocore/security.py; retainmainpublicaliasesimports andsamebindingsforrouterfactories. No logic/type changes.
- verify: env APP_ENV=local PYTHONPATH=backend .venv/bin/python -c 'import ast,importlib,pathlib,subprocess; old=ast.parse(subprocess.check_output(["git","show","4c707d9:backend/app/main.py"],text=True)); originals={n.name:ast.dump(n) for n in old.body if isinstance(n,ast.FunctionDef)}; moves={"jsonable":"serialization","telemetry_ws_payload":"serialization","websocket_bearer":"security"}; assert all(originals[n]==ast.dump(next(x for x in ast.parse(pathlib.Path("backend/app/core/"+m+".py").read_text()).body if isinstance(x,ast.FunctionDef) and x.name==n)) for n,m in moves.items()); main=importlib.import_module("backend.app.main"); assert all(getattr(main,n) is getattr(importlib.import_module("backend.app.core."+m),n) for n,m in moves.items()); print("PASS exact function bodies and main public aliases")' && env APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_api.py -k 'websocket_uses_bearer or mongo_telemetry_payload or mongo_naive_utc' && env APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_contract_snapshot.py && .venv/bin/ruff check backend/app/main.py backend/app/core && .venv/bin/ruff format --check backend/app/main.py backend/app/core

## Deferred
- T-44132 (W3, before claiming P-3): bundle checker counts only rootMainFiles+page chunk, omitting layout/shared dependency assets; add fixture regression and measure fullinitial asset graph with unchanged170KB threshold.

## Done
- T-44150 accepted4c707d9; verify0.
- T-44151 accepted462ea55; verify0.
- T-330 accepted3afff87; verify0.
- T-44149 accepted62443d0; verify0.
- T-44148 accepteda5535b2; verify0.
- T-44147 accepted6ae5e39; verify0.
- T-44146 accepted5b0b7e4; verify0.
- T-323 accepted3146736; verify0.
- T-320 accepted4789586; verify0.
- T-44145 accepted8f721ae; verify0.
- T-44144 accepted2e0345c; verify0.
- T-44143 accepted9b8322c; verify0.
- T-325 accepted2bff831; verify0.
- T-44142 accepted42f0a46; verify0.
- T-324 accepted61643df; verify0.
- T-44140 accepted3bb47c9; verify0.
- T-44138 accepted12edd4e; verify0.
- T-44139 accepted5e9584b; verify0.
- T-322 accepteda12bc68; verify0.
- T-44137 accepted4b6a0fd; verify0.
- T-44135 accepted7afadff; verify0.
- T-44129 accepteda3c0554; verify0.
- Older accepted tasks: git history and CURRENT_STATE phase summaries.
