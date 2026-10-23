# NEXT_STATE
updated_at: 2026-10-23
phase: 3 API contract guard (Phases0–2 complete; baseline score51.2974)

## Queue
### T-44166 W2 — OPEN
- target_files: backend/app/main.py, backend/app/pit_strategy_service.py, backend/app/demo_race_repository.py
- contract: T331 move-only domain helper child: move tire_stint_target and PIT_TIRE_STINT_LAPS to pit_strategy_service.py, and choose_demo_car_numbers to demo_race_repository.py. Keep public main aliases. No policy, random generator, seed or callback behavior changes.
- verify: env APP_ENV=local PYTHONPATH=backend .venv/bin/python -c 'import ast,importlib,inspect,subprocess; old=ast.parse(subprocess.check_output(["git","show","4c4f401:backend/app/main.py"],text=True)); modules={"tire_stint_target":"pit_strategy_service","choose_demo_car_numbers":"demo_race_repository"}; a={n.name:ast.dump(n) for n in old.body if isinstance(n,ast.FunctionDef)}; main=importlib.import_module("backend.app.main"); assert all(a[n]==ast.dump(next(x for x in ast.parse(inspect.getsource(importlib.import_module("backend.app."+m))).body if isinstance(x,ast.FunctionDef) and x.name==n)) and getattr(main,n) is getattr(importlib.import_module("backend.app."+m),n) for n,m in modules.items()); assert main.PIT_TIRE_STINT_LAPS==18; print("PASS exact helpers and main aliases")' && env APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_api.py -k 'demo_car_numbers or pit_strategy_reports or sector_lap_elapsed' && env APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_contract_snapshot.py && .venv/bin/ruff check backend/app/main.py backend/app/pit_strategy_service.py backend/app/demo_race_repository.py && .venv/bin/ruff format --check backend/app/main.py backend/app/pit_strategy_service.py backend/app/demo_race_repository.py

### T-44165 W3 — OPEN
- target_files: scripts/eval/neo_effects.py, scripts/eval/rules/blur.good.css, scripts/eval/rules/blur.bad.css
- contract: T360 blur-rule child: add typed reusable blur checker with one good and one bad fixture. It must catch blur CSS functions in filter/backdrop-filter style declarations (including inline JS styles) and blur/backdrop-blur Tailwind utilities except explicit blur-none. This is a new rule module for subsequent shared-scanner integration; do not change the UI.
- verify: env PYTHONPATH=. .venv/bin/python scripts/eval/neo_effects.py --self-test && .venv/bin/ruff check scripts/eval/neo_effects.py && .venv/bin/ruff format --check scripts/eval/neo_effects.py && .venv/bin/mypy --strict scripts/eval/neo_effects.py

## Deferred
- T-44132 (W3, before claiming P-3): bundle checker counts only rootMainFiles+page chunk, omitting layout/shared dependency assets; add fixture regression and measure fullinitial asset graph with unchanged170KB threshold.

## Done
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
