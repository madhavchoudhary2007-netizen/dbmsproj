# NEXT_STATE
updated_at: 2026-10-23
phase: 3 API contract guard (Phases0–2 complete; baseline score51.2974)

## Queue
### T-44169 W3 — OPEN
- target_files: scripts/eval/neo_weight.py, scripts/eval/rules/weight.good.css, scripts/eval/rules/weight.bad.css
- contract: T360 weight-rule child: implement typed font-weight900 lint with one good and one bad fixture. Catch CSS font-weight:900, font shorthand weight900, JS fontWeight:900 (quoted numeric values/keys too), and Tailwind font-black/font-[900] variants. Keep700/500/400 valid. No product edits; shared scanner wiring follows.
- verify: env PYTHONPATH=. .venv/bin/python scripts/eval/neo_weight.py --self-test && .venv/bin/ruff check scripts/eval/neo_weight.py && .venv/bin/ruff format --check scripts/eval/neo_weight.py && .venv/bin/mypy --strict scripts/eval/neo_weight.py

### T-44168 W2 — OPEN
- target_files: backend/app/api/health.py, backend/app/main.py
- contract: T331 readiness route move: move health_ready verbatim into the health API module using a typed registration wrapper that closes over the exact existing app and callbacks. Retain main.health_ready and model aliases. This is transitional move-only wiring; full factory removal/app.state DI is T332, not this task.
- verify: env APP_ENV=local PYTHONPATH=backend .venv/bin/python -c 'import ast,importlib,inspect,subprocess; old=ast.parse(subprocess.check_output(["git","show","64214d6:backend/app/main.py"],text=True)); a=next(n for n in old.body if isinstance(n,ast.FunctionDef) and n.name=="health_ready"); a.decorator_list=[]; m=importlib.import_module("backend.app.api.health"); b=next(n for n in ast.walk(ast.parse(inspect.getsource(m))) if isinstance(n,ast.FunctionDef) and n.name=="health_ready"); b.decorator_list=[]; assert ast.dump(a)==ast.dump(b); main=importlib.import_module("backend.app.main"); routes=[r for outer in main.app.routes for r in (outer.original_router.routes if hasattr(outer,"original_router") else [outer])]; selected=[r for r in routes if getattr(r,"path",None)=="/health/ready"]; assert len(selected)==1 and selected[0].endpoint is main.health_ready; print("PASS exact readiness body and endpoint alias")' && env APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_contract_snapshot.py backend/tests/test_security_headers.py && .venv/bin/ruff check backend/app/main.py backend/app/api/health.py && .venv/bin/ruff format --check backend/app/main.py backend/app/api/health.py

### T-44167 W3 — OPEN
- target_files: scripts/eval/neo_gradient.py, scripts/eval/rules/gradient.good.css, scripts/eval/rules/gradient.bad.css
- contract: T360 gradient-rule child: add typed gradient-location checker with good and bad fixtures. CSS gradients and gradient utilities are allowed only in the exact frontend/app/styles/textures.css file. All other product paths must reject gradient declarations and Tailwind gradient utilities; no broad basename or substring exception.
- verify: env PYTHONPATH=. .venv/bin/python scripts/eval/neo_gradient.py --self-test && .venv/bin/ruff check scripts/eval/neo_gradient.py && .venv/bin/ruff format --check scripts/eval/neo_gradient.py && .venv/bin/mypy --strict scripts/eval/neo_gradient.py

## Deferred
- T-44132 (W3, before claiming P-3): bundle checker counts only rootMainFiles+page chunk, omitting layout/shared dependency assets; add fixture regression and measure fullinitial asset graph with unchanged170KB threshold.

## Done
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
