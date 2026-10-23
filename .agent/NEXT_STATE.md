# NEXT_STATE
updated_at: 2026-10-23
phase: 3 API contract guard (Phases0–2 complete; baseline score51.2974)

## Queue
### T-44155 W1 — OPEN
- target_files: frontend/app/styles/tokens.css
- contract: T361 foundation child: add the approved Tailwind4 tokens.css only. It is staged for subsequent PostCSS/import integration, and must not change current route rendering yet. Define the exact approved palette, restricted spacing/radius/hard shadows/font aliases and fluid type tokens. No layout redesign.
- verify: npm --prefix frontend run typecheck && bash scripts/eval/lint-spacing.sh && bash scripts/eval/lint-banned.sh && bash scripts/eval/lint-motion.sh

### T-44154 W2 — OPEN
- target_files: backend/app/core/errors.py, backend/app/main.py
- contract: T331 move-only child: move four exception handlers from main.py into core/errors.py. Retain the public main aliases and register each existing exception class with the same handler on the app. Function bodies and signatures remain verbatim; no behavior or contract change.
- verify: env APP_ENV=local PYTHONPATH=backend .venv/bin/python -c 'import ast,importlib,subprocess; old=ast.parse(subprocess.check_output(["git","show","a1eea31:backend/app/main.py"],text=True)); names=("conflict_handler","reference_conflict_handler","integrity_handler","database_unavailable_handler"); orig={n.name:n for n in old.body if isinstance(n,ast.AsyncFunctionDef) and n.name in names}; new=importlib.import_module("backend.app.core.errors"); main=importlib.import_module("backend.app.main"); import inspect; moved={n.name:n for n in ast.parse(inspect.getsource(new)).body if isinstance(n,ast.AsyncFunctionDef)}; [setattr(n,"decorator_list",[]) for n in orig.values()]; assert all(ast.dump(orig[n])==ast.dump(moved[n]) and getattr(main,n) is getattr(new,n) for n in names); assert all(any(h is getattr(new,n) for h in main.app.exception_handlers.values()) for n in names); print("PASS exact handler bodies, aliases and registration")' && env APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_contract_snapshot.py && .venv/bin/ruff check backend/app/main.py backend/app/core && .venv/bin/ruff format --check backend/app/main.py backend/app/core

## Deferred
- T-44132 (W3, before claiming P-3): bundle checker counts only rootMainFiles+page chunk, omitting layout/shared dependency assets; add fixture regression and measure fullinitial asset graph with unchanged170KB threshold.

## Done
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
