# NEXT_STATE
updated_at: 2026-10-23
phase: 3 API contract guard (Phases0–2 complete; baseline score51.2974)

## Queue
### T-44153 W3 — OPEN
- target_files: scripts/eval/source_text.py, scripts/eval/lint-neobrutal.sh
- contract: T360 foundation readability: extract sourcecommentmasking fromembeddedchecker into formatted reusable stdlibmodule scripts/eval/source_text.py. Sharedmask_comments(text:str,css:bool=False)->str preservesoffset/newlines/quotes andonlyJSlinecomments exactlycurrentbehavior. Checker callshelper, allradiuspatterns/selftests/fixtures/output remainunchanged. No additionalrulesyet.
- verify: bash scripts/eval/lint-neobrutal.sh --self-test && .venv/bin/ruff check scripts/eval/source_text.py && .venv/bin/ruff format --check scripts/eval/source_text.py && .venv/bin/mypy --strict scripts/eval/source_text.py

## Deferred
- T-44132 (W3, before claiming P-3): bundle checker counts only rootMainFiles+page chunk, omitting layout/shared dependency assets; add fixture regression and measure fullinitial asset graph with unchanged170KB threshold.

## Done
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
