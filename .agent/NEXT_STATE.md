# NEXT_STATE
updated_at: 2026-10-23
phase: 3 T331 extraction; Phase5 T360–T363verified, T364/T365inprogress (Phases0–2 complete; baseline51.2974)

## Queue
### T-44213 W2 — OPEN
- target_files: frontend/lib/use-delayed-flag.ts, frontend/lib/use-native-dialog.ts, frontend/lib/use-nb-demo.ts
- contract: T365 state helpers required by accessible primitives and the development-only style guide.
- verify: npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0

### T-44211 W2 — OPEN
- target_files: backend/app/core/simulation_tick.py
- contract: T331 stage exact pure simulation tick in core module; wiring/removal is next atomic task.
- verify: env APP_ENV=local PYTHONPATH=backend .venv/bin/python -c 'import ast,copy,importlib,subprocess; from datetime import UTC,datetime; from uuid import UUID; from backend.app.simulation_core import Simulation; old=ast.parse(subprocess.check_output(["git","show","89c82af:backend/app/main.py"],text=True)); a=next(n for n in old.body if isinstance(n,ast.FunctionDef) and n.name=="advance_simulation_tick"); new=ast.parse(open("backend/app/core/simulation_tick.py").read()); b=next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name==a.name); assert ast.dump(a)==ast.dump(b); m=importlib.import_module("backend.app.main"); c=importlib.import_module("backend.app.core.simulation_tick"); s=Simulation(UUID(int=1),[{"id":UUID(int=2),"number":7}],2,total_laps=2,seed=123); t=copy.deepcopy(s); stamp=datetime(2026,10,24,tzinfo=UTC); assert all(m.advance_simulation_tick(s,stamp)==c.advance_simulation_tick(t,stamp) for _ in range(8)); assert s==t; print("PASS exact tick AST and8deterministic differential ticks")' && env APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_contract_snapshot.py backend/tests/test_route_registration.py backend/tests/test_simulation_replay.py && .venv/bin/ruff check backend/app/core/simulation_tick.py && .venv/bin/ruff format --check backend/app/core/simulation_tick.py

## Blocked
- Previous6Luna usage-limit blocker superseded byowner5.6/high authorization; availability pendingfirstdispatch.

## Deferred
- T-44132 (W3, before claiming P-3): bundle checker counts only rootMainFiles+page chunk, omitting layout/shared dependency assets; add fixture regression and measure fullinitial asset graph with unchanged170KB threshold.

## Done
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
