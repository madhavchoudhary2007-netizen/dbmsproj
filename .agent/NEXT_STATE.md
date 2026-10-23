# NEXT_STATE
updated_at: 2026-10-23
phase: 3 API contract guard (Phases0–2 complete; baseline score51.2974)

## Queue
### T-44160 Orchestrator — OPEN
- target_files: frontend/package.json, frontend/package-lock.json
- contract: planned root-owned npm installation; generated lock only.
- verify: npm --prefix frontend ls tailwindcss @tailwindcss/postcss && node -e 'const assert=require("node:assert/strict"); const p=require("./frontend/package.json"); assert.match(p.devDependencies.tailwindcss,/^\^4\./); assert.match(p.devDependencies["@tailwindcss/postcss"],/^\^4\./); assert.equal(p.devDependencies.autoprefixer,undefined); console.log("PASS planned Tailwind4 dependencies and removed autoprefixer")'

### T-44161 W2 — OPEN
- target_files: backend/app/schemas_health.py, backend/app/schemas_operations.py, backend/app/main.py
- contract: T331 move-only model extraction: move three health report types to schemas_health.py and ReservationStatus to existing schemas_operations.py, retaining main aliases. No field/default/typing/signature/wire changes.
- verify: env APP_ENV=local PYTHONPATH=backend .venv/bin/python -c 'import ast,importlib,inspect,subprocess; old=ast.parse(subprocess.check_output(["git","show","cec7835:backend/app/main.py"],text=True)); names=("HealthReport","LivenessReport","ReadinessReport","ReservationStatus"); originals={n.name:ast.dump(n) for n in old.body if isinstance(n,ast.ClassDef)}; main=importlib.import_module("backend.app.main"); modules={n:importlib.import_module("backend.app.schemas_operations" if n=="ReservationStatus" else "backend.app.schemas_health") for n in names}; assert all(originals[n]==ast.dump(next(x for x in ast.parse(inspect.getsource(m)).body if isinstance(x,ast.ClassDef) and x.name==n)) and getattr(main,n) is getattr(m,n) for n,m in modules.items()); print("PASS exact model AST and aliases")' && env APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_contract_snapshot.py backend/tests/test_security_headers.py && .venv/bin/ruff check backend/app/main.py backend/app/schemas_operations.py backend/app/schemas_health.py && .venv/bin/ruff format --check backend/app/main.py backend/app/schemas_operations.py backend/app/schemas_health.py

### T-44159 W3 — OPEN
- target_files: scripts/eval/neo_colour.py, scripts/eval/rules/gray.good.css, scripts/eval/rules/gray.bad.css
- contract: T360 lint child: implement a reusable gray-family rule plus good/bad fixtures. This module will be wired into the shared neo-brutal scanner in the next child. Detect forbidden gray/slate/zinc/neutral/stone utilities and neutral CSS hex colors except pure black/white. Preserve source positions; ignore comments through mask_comments. No product edits.
- verify: env PYTHONPATH=. .venv/bin/python scripts/eval/neo_colour.py --self-test && .venv/bin/ruff check scripts/eval/neo_colour.py && .venv/bin/ruff format --check scripts/eval/neo_colour.py && .venv/bin/mypy --strict scripts/eval/neo_colour.py

## Deferred
- T-44132 (W3, before claiming P-3): bundle checker counts only rootMainFiles+page chunk, omitting layout/shared dependency assets; add fixture regression and measure fullinitial asset graph with unchanged170KB threshold.

## Done
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
