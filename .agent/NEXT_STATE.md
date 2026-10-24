# NEXT_STATE
updated_at: 2026-10-23
phase: 3 T331 extraction; Phase5 T360–T363verified, T364/T365inprogress (Phases0–2 complete; baseline51.2974)

## Queue
### T-44228 W1 — OPEN
- target_files: frontend/app/__nb/page.tsx, frontend/app/%5F_nb/page.tsx
- contract: T365 repair hidden guide route: leading underscore folder is private in Next, must escape first underscore.
- verify: npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0

### T-44227 W2 — OPEN
- target_files: backend/app/core/lock_demo.py
- contract: T331 stage exact lock-demo transaction helpers in focused core module.
- verify: env APP_ENV=local PYTHONPATH=backend .venv/bin/python -c 'import ast,subprocess; old=ast.parse(subprocess.check_output(["git","show","ef0dee3:backend/app/main.py"],text=True)); new=ast.parse(open("backend/app/core/lock_demo.py").read()); names={"_competing_lock_demo_reservation","_cleanup_lock_demo"}; a={n.name:ast.dump(n) for n in ast.walk(old) if isinstance(n,ast.FunctionDef) and n.name in names}; b={n.name:ast.dump(n) for n in ast.walk(new) if isinstance(n,ast.FunctionDef) and n.name in names}; assert a==b and len(a)==2; print("PASS exact lock helper ASTs")' && env APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_contract_snapshot.py backend/tests/test_route_registration.py && .venv/bin/ruff check backend/app/core/lock_demo.py && .venv/bin/ruff format --check backend/app/core/lock_demo.py

### T-44226 W3 — OPEN
- target_files: frontend/e2e/motion-hooks.spec.ts
- contract: T364/T366 real mounted hook browser tests through local guide fixture.
- verify: npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0 && cd frontend && ./node_modules/.bin/playwright test e2e/motion-hooks.spec.ts --list

### T-44225 W3 — OPEN
- target_files: frontend/e2e/nb-primitives.spec.ts
- contract: T366 browser assertions for actual shared primitives through dev-only guide.
- verify: npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0 && cd frontend && ./node_modules/.bin/playwright test e2e/nb-primitives.spec.ts --list

## Blocked
- None currently. Owner5.6/high override2bc94fb verified byfreshsuccessfulworkers.

## Deferred
- T-44132 (W3, before claiming P-3): bundle checker counts only rootMainFiles+page chunk, omitting layout/shared dependency assets; add fixture regression and measure fullinitial asset graph with unchanged170KB threshold.

## Done
- T-44224 acceptedef0dee3; verify0.
- T-44222 accepted24fae87; verify0.
- T-44223 accepted818ff70; verify0.
- T-44220 accepted324c60b; verify0.
- T-44221 accepted2e5c5a4; verify0.
- T-44219 accepted35fe855; verify0.
- T-44218 accepted2d00c1f; verify0.
- T-44217 accepted0e166fc; verify0.
- T-44216 accepted38ae29f; verify0.
- T-44212 accepted46129c0; verify0.
- T-44215 accepted0bd674b; verify0.
- T-44211 accepted8275aab; verify0.
- T-44213 accepted471cb56; verify0.
- T-44210 accepted8ba857e; verify0.
- T-44214 accepted5ee4710; verify0.
- T-44208 accepted72a5b82; verify0.
- T-44209 accepted89c82af; verify0.
- T-44204 acceptede4a3f6c; verify0.
- T-44205 accepted65bd176; verify0.
- T-44203 accepted6eefdaa; verify0.
- T-44207 accepted2bc94fb; verify0.
- T-44206 accepted35ba591; verify0.
- T-44200 accepted47c0408; verify0.
- T-363 accepted13f614a; verify0.
- Recentaccepted tasks andevidence in CURRENT_STATE andgit history; earlierqueue fullyretained in docs/overhaul-plan.md.
