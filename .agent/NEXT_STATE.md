# NEXT_STATE
updated_at: 2026-10-23
phase: 3 T331 extraction; Phase5 T360–T363verified, T364/T365inprogress (Phases0–2 complete; baseline51.2974)

## Queue
### T-44209 W2 — OPEN
- target_files: backend/app/main.py, backend/app/api/stewards.py
- contract: T331 move unchanged incident-decision endpoint into existing stewards module.
- verify: env APP_ENV=local PYTHONPATH=backend .venv/bin/python -c 'import ast,importlib,inspect,subprocess; old=ast.parse(subprocess.check_output(["git","show","65bd176:backend/app/main.py"],text=True)); a=next(n for n in old.body if isinstance(n,ast.FunctionDef) and n.name=="decide_incident"); a.decorator_list=[]; mod=importlib.import_module("backend.app.api.stewards"); b=next(n for n in ast.walk(ast.parse(inspect.getsource(mod))) if isinstance(n,ast.FunctionDef) and n.name==a.name); b.decorator_list=[]; assert ast.dump(a)==ast.dump(b); m=importlib.import_module("backend.app.main"); routes=[r for outer in m.app.routes for r in (outer.original_router.routes if hasattr(outer,"original_router") else [outer])]; assert sum(getattr(r,"endpoint",None) is m.decide_incident for r in routes)==1; print("PASS exact incident decision and alias")' && env APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_contract_snapshot.py backend/tests/test_route_registration.py && .venv/bin/ruff check backend/app/main.py backend/app/api/stewards.py && .venv/bin/ruff format --check backend/app/main.py backend/app/api/stewards.py

### T-44208 W1 — OPEN
- target_files: frontend/components/nb/input.tsx, frontend/components/nb/field.tsx
- contract: T365 accessible native form controls and labeled field primitive, no route changes.
- verify: bash scripts/eval/lint-spacing.sh && bash scripts/eval/lint-banned.sh && bash scripts/eval/lint-motion.sh && bash scripts/eval/lint-neobrutal.sh && npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0

## Blocked
- Previous6Luna usage-limit blocker superseded byowner5.6/high authorization; availability pendingfirstdispatch.

## Deferred
- T-44132 (W3, before claiming P-3): bundle checker counts only rootMainFiles+page chunk, omitting layout/shared dependency assets; add fixture regression and measure fullinitial asset graph with unchanged170KB threshold.

## Done
- T-44204 acceptede4a3f6c; verify0.
- T-44205 accepted65bd176; verify0.
- T-44203 accepted6eefdaa; verify0.
- T-44207 accepted2bc94fb; verify0.
- T-44206 accepted35ba591; verify0.
- T-44200 accepted47c0408; verify0.
- T-363 accepted13f614a; verify0.
- Recentaccepted tasks andevidence in CURRENT_STATE andgit history; earlierqueue fullyretained in docs/overhaul-plan.md.
