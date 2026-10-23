# NEXT_STATE
updated_at: 2026-10-23
phase: 3 T331 extraction; Phase5 T360/T361accepted, T362 next (Phases0–2 complete; baseline51.2974)

## Queue
### T-44191 W3 — OPEN
- target_files: backend/tests/test_contract_requests.py
- contract: T330 P1 failing-first request contract regressions: reject new required query/header/body requirements that existing compatibility checker currently misses.
- verify: python3 .agent/check-red-tests.py T-44191 backend/tests/test_contract_requests.py && .venv/bin/ruff check backend/tests/test_contract_requests.py && .venv/bin/ruff format --check backend/tests/test_contract_requests.py

## Deferred
- T-44132 (W3, before claiming P-3): bundle checker counts only rootMainFiles+page chunk, omitting layout/shared dependency assets; add fixture regression and measure fullinitial asset graph with unchanged170KB threshold.

## Done
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
