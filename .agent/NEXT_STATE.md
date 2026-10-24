# NEXT_STATE
updated_at: 2026-10-23
phase: 3 T331 extraction; Phase5 T360–T363verified, T364/T365inprogress (Phases0–2 complete; baseline51.2974)

## Queue
### T-44219 W2 — OPEN
- target_files: backend/app/api/race_archive.py
- contract: T331 stage exact race archive handler in focused API module; separate next packet wires/removes original.
- verify: env APP_ENV=local PYTHONPATH=backend .venv/bin/python -c 'import ast,subprocess; old=ast.parse(subprocess.check_output(["git","show","46129c0:backend/app/main.py"],text=True)); a=next(n for n in old.body if isinstance(n,ast.FunctionDef) and n.name=="dbms_race"); a.decorator_list=[]; new=ast.parse(open("backend/app/api/race_archive.py").read()); b=next(n for n in ast.walk(new) if isinstance(n,ast.FunctionDef) and n.name==a.name); b.decorator_list=[]; assert ast.dump(a)==ast.dump(b); print("PASS exact staged race archive handler AST")' && env APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_contract_snapshot.py backend/tests/test_route_registration.py && .venv/bin/ruff check backend/app/api/race_archive.py && .venv/bin/ruff format --check backend/app/api/race_archive.py

## Blocked
- None currently. Owner5.6/high override2bc94fb verified byfreshsuccessfulworkers.

## Deferred
- T-44132 (W3, before claiming P-3): bundle checker counts only rootMainFiles+page chunk, omitting layout/shared dependency assets; add fixture regression and measure fullinitial asset graph with unchanged170KB threshold.

## Done
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
