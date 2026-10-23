# NEXT_STATE
updated_at: 2026-10-23
phase: 3 T331 extraction; Phase5 T360/T361accepted, T362 next (Phases0–2 complete; baseline51.2974)

## Queue
### T-44202 W1 — OPEN
- target_files: frontend/app/globals.css
- contract: TASTE accessibility finding: restore AA text contrast for dashboard stat helper labels and login visual footer after gradient removal.
- verify: bash scripts/eval/lint-spacing.sh && bash scripts/eval/lint-banned.sh && bash scripts/eval/lint-motion.sh && bash scripts/eval/lint-neobrutal.sh && npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0

### T-44201 W2 — OPEN
- target_files: backend/app/main.py, backend/app/api/stewards.py
- contract: T331 move unchanged incident-list endpoint into API stewards module.
- verify: env APP_ENV=local PYTHONPATH=backend .venv/bin/python -c 'import ast,importlib,inspect,subprocess; old=ast.parse(subprocess.check_output(["git","show","5898b4f:backend/app/main.py"],text=True)); a=next(n for n in old.body if isinstance(n,ast.FunctionDef) and n.name=="get_incidents"); a.decorator_list=[]; mod=importlib.import_module("backend.app.api.stewards"); b=next(n for n in ast.walk(ast.parse(inspect.getsource(mod))) if isinstance(n,ast.FunctionDef) and n.name==a.name); b.decorator_list=[]; assert ast.dump(a)==ast.dump(b); m=importlib.import_module("backend.app.main"); routes=[r for outer in m.app.routes for r in (outer.original_router.routes if hasattr(outer,"original_router") else [outer])]; assert sum(getattr(r,"endpoint",None) is m.get_incidents for r in routes)==1; print("PASS exact incident list and alias")' && env APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_contract_snapshot.py backend/tests/test_route_registration.py && .venv/bin/ruff check backend/app/main.py backend/app/api/stewards.py && .venv/bin/ruff format --check backend/app/main.py backend/app/api/stewards.py

### T-44199 W2 — OPEN
- target_files: frontend/lib/cn.ts, frontend/lib/use-reduced-motion.ts
- contract: T364 first foundations: dependency-free class join helper and SSR-safe reduced-motion subscription.
- verify: npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0

## Deferred
- T-44132 (W3, before claiming P-3): bundle checker counts only rootMainFiles+page chunk, omitting layout/shared dependency assets; add fixture regression and measure fullinitial asset graph with unchanged170KB threshold.

## Done
- T-44198 accepted5898b4f; verify0.
- T-44197 accepted8c03959; verify0.
- T-44196 acceptedd0bb56a; verify0.
- T-44194 accepteddc48751; verify0.
- T-44195 accepted2ff639d; verify0.
- T-44193 accepted2c78430; verify0.
- T-44191 accepted9efac10; verify0.
- T-44192 accepted2e9106e; verify0.
- T-44190 acceptedcdd4ad2; verify0.
- T-362 acceptedc0781f9; verify0.
- T-360 accepted2ad337f; verify0.
- T-44188 accepted7eeb81d; verify0.
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
