# NEXT_STATE
updated_at: 2026-10-23
phase: 3 API contract guard (Phases0–2 complete; baseline score51.2974)

## Queue
### T-44169 W3 — OPEN
- target_files: scripts/eval/neo_weight.py, scripts/eval/rules/weight.good.css, scripts/eval/rules/weight.bad.css
- contract: T360 weight-rule child: implement typed font-weight900 lint with one good and one bad fixture. Catch CSS font-weight:900, font shorthand weight900, JS fontWeight:900 (quoted numeric values/keys too), and Tailwind font-black/font-[900] variants. Keep700/500/400 valid. No product edits; shared scanner wiring follows.
- verify: env PYTHONPATH=. .venv/bin/python scripts/eval/neo_weight.py --self-test && .venv/bin/ruff check scripts/eval/neo_weight.py && .venv/bin/ruff format --check scripts/eval/neo_weight.py && .venv/bin/mypy --strict scripts/eval/neo_weight.py

## Deferred
- T-44132 (W3, before claiming P-3): bundle checker counts only rootMainFiles+page chunk, omitting layout/shared dependency assets; add fixture regression and measure fullinitial asset graph with unchanged170KB threshold.

## Done
- T-44167 accepted6c04161; verify0.
- T-44170 accepted31a3bd4; verify0.
- T-44168 accepted4e8f466; verify0.
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
