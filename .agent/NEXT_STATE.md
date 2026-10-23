# NEXT_STATE
updated_at: 2026-10-23
phase: 3 API contract guard (Phases0–2 complete; baseline score51.2974)

## Queue
### T-44163 W3 — OPEN
- target_files: scripts/eval/neo_colour.py, scripts/eval/lint-neobrutal.sh
- contract: T360 child: wire accepted gray-family checker into lint-neobrutal.sh's existing shared scanner and --self-test; strengthen it to catch neutral hexes in JS/TS inline style color properties as well. Preserve radius rules/fixtures/selftests. No product changes.
- verify: bash scripts/eval/lint-neobrutal.sh --self-test && .venv/bin/ruff check scripts/eval/neo_colour.py && .venv/bin/ruff format --check scripts/eval/neo_colour.py && .venv/bin/mypy --strict scripts/eval/neo_colour.py

### T-44162 W1 — OPEN
- target_files: frontend/postcss.config.js, frontend/tailwind.config.ts, frontend/app/globals.css
- contract: T361 configuration/import integration: switch PostCSS to the installed Tailwind4 adapter, remove the obsolete Tailwind3 config, and replace the three @tailwind directives at the start of globals.css with @import './styles/tokens.css'. Keep every legacy CSS rule and route rendering contract. Do not redesign screens.
- verify: .venv/bin/python .agent/check-frontend-build.py

## Deferred
- T-44132 (W3, before claiming P-3): bundle checker counts only rootMainFiles+page chunk, omitting layout/shared dependency assets; add fixture regression and measure fullinitial asset graph with unchanged170KB threshold.

## Done
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
