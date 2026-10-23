# NEXT_STATE
updated_at: 2026-10-23
phase: 1 honest green baseline

## Queue
### T-44121 W2 — OPEN
- target_files: backend/app/main.py, backend/app/login_limiter.py
- contract: preservetick/stateflow, C901loopzero; loginformatterexactAST.
- verify: .venv/bin/python -c "import ast,subprocess; p='backend/app/main.py';s=open(p).read();ns=[n for n in ast.parse(s).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in ('simulation_loop','_persist_simulation_tick')];assert len(ns)==2;subprocess.run(['.venv/bin/ruff','check','--select','C901','--stdin-filename',p,'-'],input=chr(10).join(ast.get_source_segment(s,n) for n in ns),text=True,check=True)" && .venv/bin/ruff check backend/app/login_limiter.py && .venv/bin/ruff format --check --output-format concise backend/app/main.py backend/app/login_limiter.py && .venv/bin/python .agent/check-format-progress.py backend/app/login_limiter.py

## Blocked
- T-310 remains open until full app Ruff/format exit0; T-311 accepted8570e58; no intermediate count is a parent pass.

## Done
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
- Phase1 children T-442..T-460 accepted where recorded in CURRENT_STATE/git; T-450/T-461 were not dispatched. Parent T-310/T-311 remain open.
- Latest T-46012e8ea1 database tests full Ruff/format0 and unchangedAST; T-4595601bbd bootstrap format unchangedAST.
