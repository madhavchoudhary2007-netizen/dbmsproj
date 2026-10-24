# NEXT_STATE
updated_at: 2026-10-23
phase: 3 T331 extraction; Phase5 T360–T363verified, T364/T365inprogress (Phases0–2 complete; baseline51.2974)

## Queue
### T-44207 Orchestrator — REVIEW
- target_files: .codex/agents/w1-ui.toml, .codex/agents/w2-state.toml, .codex/agents/w3-eval.toml
- contract: Owner-authorized GPT5.6Luna/high worker profile switch; cap2/orchestrator unchanged.
- verify: export HARNESS=codex; source .agent/models.env && bash scripts/agent/boot.sh

### T-44205 W2 — OPEN
- target_files: backend/app/main.py, backend/app/api/stewards.py
- contract: T331 move unchanged incident-create endpoint into existing stewards router.
- verify: env APP_ENV=local PYTHONPATH=backend .venv/bin/python -c 'import ast,importlib,inspect,subprocess; old=ast.parse(subprocess.check_output(["git","show","fa39f5d:backend/app/main.py"],text=True)); a=next(n for n in old.body if isinstance(n,ast.FunctionDef) and n.name=="create_incident"); a.decorator_list=[]; mod=importlib.import_module("backend.app.api.stewards"); b=next(n for n in ast.walk(ast.parse(inspect.getsource(mod))) if isinstance(n,ast.FunctionDef) and n.name==a.name); b.decorator_list=[]; assert ast.dump(a)==ast.dump(b); m=importlib.import_module("backend.app.main"); routes=[r for outer in m.app.routes for r in (outer.original_router.routes if hasattr(outer,"original_router") else [outer])]; assert sum(getattr(r,"endpoint",None) is m.create_incident for r in routes)==1; print("PASS exact incident creation and alias")' && env APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_contract_snapshot.py backend/tests/test_route_registration.py && .venv/bin/ruff check backend/app/main.py backend/app/api/stewards.py && .venv/bin/ruff format --check backend/app/main.py backend/app/api/stewards.py

### T-44204 W1 — OPEN
- target_files: frontend/components/nb/sticker.tsx, frontend/components/nb/badge.tsx, frontend/components/nb/tyre-badge.tsx
- contract: T365 typed static sticker, status badge and compound badge primitives.
- verify: bash scripts/eval/lint-spacing.sh && bash scripts/eval/lint-banned.sh && bash scripts/eval/lint-motion.sh && bash scripts/eval/lint-neobrutal.sh && npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0

### T-44203 W1 — OPEN (resume with owner-authorized5.6/high)
- target_files: frontend/components/nb/button.tsx, frontend/components/nb/card.tsx
- contract: T365 first typed primitives: NbButton and NbCard, no routes use them yet.
- verify: bash scripts/eval/lint-spacing.sh && bash scripts/eval/lint-banned.sh && bash scripts/eval/lint-motion.sh && bash scripts/eval/lint-neobrutal.sh && npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0

## Blocked
- Previous6Luna usage-limit blocker superseded byowner5.6/high authorization; availability pendingfirstdispatch.

## Deferred
- T-44132 (W3, before claiming P-3): bundle checker counts only rootMainFiles+page chunk, omitting layout/shared dependency assets; add fixture regression and measure fullinitial asset graph with unchanged170KB threshold.

## Done
- T-44206 accepted35ba591; verify0.
- T-44200 accepted47c0408; verify0.
- T-363 accepted13f614a; verify0.
- Recentaccepted tasks andevidence in CURRENT_STATE andgit history; earlierqueue fullyretained in docs/overhaul-plan.md.
