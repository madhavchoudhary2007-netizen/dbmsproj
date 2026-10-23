# NEXT_STATE
updated_at: 2026-10-23
phase: 3 API contract guard (Phases0–2 complete; baseline score51.2974)

## Queue
### T-44151 W2 — OPEN
- target_files: backend/app/core/__init__.py, backend/app/core/events.py, backend/app/main.py
- contract: T331 first puremovechild: extract EventBus class verbatim into backend/app/core/events.py. Keep main.EventBus publicalias import and main.bus singletoncreation exactlyasbefore; no behavior/typechanges. Do notmoveotherfunctions. Explicitcorepackage empty__init__.py permitted.
- verify: env APP_ENV=local PYTHONPATH=backend DATABASE_URL=postgresql://127.0.0.1:1/unreachable MONGODB_URL=mongodb://127.0.0.1:1 .venv/bin/python .agent/check-event-bus-move.py && env APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_api.py -k 'websocket_bus or websocket_uses_bearer' && env APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_contract_snapshot.py && .venv/bin/ruff check backend/app/main.py backend/app/core && .venv/bin/ruff format --check backend/app/main.py backend/app/core

### T-44150 W3 — OPEN
- target_files: scripts/eval/lint-neobrutal.sh, scripts/eval/rules/radius.good.css, scripts/eval/rules/radius.bad.css
- contract: Phase5 T360 boundedchild1, allowedinterleavewithbackendperplan§4: create lint-neobrutal.sh foundation enforcingONLYradius sofar, plusonegood/bad radiusfixture. LaterchildrenaddotherADR007rules; don'tclaimwholeT360complete. DefaultscanactualSRC_DIRS viaexisting_dirs.sh, targetedfileargsforverification, --self-test usescommittedfixtures and exits0 onlycorrectgood0/badnonzero. NormalcurrentrepoexpectedFAILoldradiusbaseline; reporthitsnochangeUI.
- verify: bash scripts/eval/lint-neobrutal.sh --self-test

## Blocked
- T-44132 (W3, before claiming P-3): bundle checker counts only rootMainFiles+page chunk, omitting layout/shared dependency assets; add fixture regression and measure fullinitial asset graph with unchanged170KB threshold.

## Done
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
- T-44136 accepted31e5494; verify0.
- T-321 acceptedcaf033f; verify0.
- T-44134 accepted749f9c5; verify0.
- T-44133 accepted091e4de; verify0.
- T-44130 acceptedce4b44b; verify0.
- T-44126 acceptedc2eb8d2; verify0.
- T-44125 accepted4eed78c; verify0.
- T-44124 accepted1d5cb48; verify0.
- T-44123 acceptedfd18bfd; verify0.
- T-44128 acceptedad19d48; verify0.
- T-44127 accepted34dbb99; verify0.
- T-314 acceptedc0c8061; verify0.
- T-313 accepted4089fb6; verify0.
- T-312 acceptede0f7adf; verify0.
- T-310 accepted35578c9; verify0.
- T-44122 accepted024f663; verify0.
- T-44121 accepted0aafbee; verify0.
- T-44120 acceptedcd970ca; verify0.
- T-44119 accepted64ae141; verify0.
- T-44118 acceptedebb3b8f; verify0.
- T-44117 accepted7789fde; verify0.
- T-44116 accepted265c60d; verify0.
- T-441 accepteda49641c; verify0.
- T-44115 accepted0224127; verify0.
- T-44114 accepted8969b47; verify0.
- T-440 accepted5248d21; catalogue alignment verify0.
- T-44113 accepted11595ad; verify0.
- T-44111 acceptedb069dab; verify0.
- T-44112 accepted518b4b4; verify0.
- T-44110 acceptedfd42784; verify0.
- T-44107 accepted2429939; verify0.
- T-311 accepted8570e58; verify0.
- T-44109 acceptedd9258cb; verify0.
- T-44105 accepted41a5b46; verify0.
- T-44108 accepteda893c67; verify0.
- T-44106 acceptedc6e5749; verify0.
- T-44103 accepted307771a; verify0.
- T-44104 accepted639e5a9; verify0.
- T-44102 accepted111241c; verify0.
- T-44101 accepted19620dd; verify0.
- T-44100 accepted121a209; verify0.
- T-4499 accepted73599b2; verify0.
- T-4498 acceptedd8abb08; verify0.
- T-4497 acceptedf941fc9; verify0.
- T-4496 accepted293ac25; verify0.
- T-4495 acceptedadc090f; verify0.
- T-4494 accepted4ce3333; verify0.
- T-4493 accepted5218003; verify0.
- T-4492 accepteda928c9c; verify0.
- T-4491 accepted6e710b3; verify0.
- T-4490 accepted1f55cb6; verify0.
- T-4489 acceptedab5592b; verify0.
- T-4488 accepted918245b; verify0.
- T-4487 acceptedb5afb5a; verify0.
- T-4486 accepteda141bc4; verify0.
- T-4485 acceptede2d86a7; verify0.
- T-4484 accepted2cc09da; verify0.
- T-4482 accepteda20f2a0; verify0.
- T-4483 acceptedbfad8d0; verify0.
- T-4481 accepted2cf7b01; verify0.
- T-4480 accepted4a3ab7f; verify0.
- Phase0 T-300/T-301/T-302 accepted; ADR007 activated.
- Phase1 children T-442..T-460 accepted where recorded in CURRENT_STATE/git; T-450/T-461 were not dispatched. Parents T-310/T-311 accepted.
- Latest T-46012e8ea1 database tests full Ruff/format0 and unchangedAST; T-4595601bbd bootstrap format unchangedAST.
