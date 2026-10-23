# NEXT_STATE
updated_at: 2026-10-23
phase: 1 honest green baseline

## Queue
### T-440 O — IN_REVIEW
- target_files: docs/overhaul-plan.md
- contract: catalogue respects locked owner100–300ms and display48px limits.
- verify: .venv/bin/python -c "from pathlib import Path; s=Path('docs/overhaul-plan.md').read_text(); assert 'clamp(3rem, 1.944rem + 4.507vw, 6rem)' in s; assert all(x not in s for x in ('30s loop','600ms steps','blink, 1s','900ms linear','800ms linear')); assert 'T-440 reconciliation:' in s"

### T-44114 W2 — OPEN
- target_files: backend/app/main.py
- contract: cohesive simulation start extraction preserving behavior; C901 strictly decreases.
- verify: .venv/bin/python -c "import json,subprocess; r=subprocess.run(['.venv/bin/ruff','check','--select','C901','--output-format','json','backend/app/main.py'],capture_output=True,text=True); d=json.loads(r.stdout); assert all('control_simulation' not in x['message'] or int(x['message'].split('(')[1].split()[0])<24 for x in d); assert all(not x['message'].startswith(chr(96)+'_start_session_simulation') for x in d)" && .venv/bin/ruff format --check backend/app/main.py

## Blocked
- T-310 remains open until full app Ruff/format exit0; T-311 accepted8570e58; no intermediate count is a parent pass.
- T-440 (O, before motion packets): align plan2.3/2.7 with owner100–300ms and display>=48px leading limits; those conflicting catalogue specifications are missing a correction task.
- T-441 (W3, before T-360 palette change): add heading-contrast regression for real contrast<=1, preserving4.5 threshold and excluding aria-hidden decorative duplicates only; current >1 filter omits failures.

## Done
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
