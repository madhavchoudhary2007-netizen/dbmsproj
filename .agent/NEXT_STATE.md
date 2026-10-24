# NEXT_STATE
updated_at: 2026-10-24
phase: 3 T331 extraction + 6 shell; Phases0–2 and5 COMPLETE; no current score

## Queue
### T-44246 W3 — OPEN
- target_files: backend/tests/test_dashboard_next_event_db.py
- contract: Correct ADR012 DB fixture UUID construction to match its explicit fixed-prefix expectation; preserve all assertions.
- verify: env APP_ENV=local PYTHONPATH=backend .venv/bin/python -c 'from backend.tests.test_dashboard_next_event_db import _add; from uuid import UUID; from unittest.mock import MagicMock; c=MagicMock(); result=_add(c,1,"lower","RACE","SCHEDULED",None); assert result==UUID("10000000-0000-0000-0000-000000000001"); calls=c.execute.call_args_list; assert calls[1].args[1][0]==UUID("20000000-0000-0000-0000-000000000001"); print("PASS fixture UUID prefixes; database not contacted")' && .venv/bin/ruff check backend/tests/test_dashboard_next_event_db.py && .venv/bin/ruff format --check backend/tests/test_dashboard_next_event_db.py

### T-44245 W2 — OPEN
- target_files: frontend/lib/use-race-control-feed.ts, frontend/components/special-pages.tsx
- contract: T371 add visible-only shared dashboard feed hook and reuse cache in Dashboard fetch logic, preserving all existing JSX/health/reload behavior.
- verify: npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0

## Blocked
- None currently. Owner5.6/high override2bc94fb verified byfreshsuccessfulworkers.

## Deferred
- T-44240 (O/W3/W2, T370 dependency): planned next-event ticker requires a real next_event field absent from /dashboard; draft own additive ADR, focused lock review/tests, then add read-only field on disposable acceptance. Never fabricate next-event data.
- T-44132 (W3, before claiming P-3): bundle checker counts only rootMainFiles+page chunk, omitting layout/shared dependency assets; add fixture regression and measure fullinitial asset graph with unchanged170KB threshold.

## Done
- T-44244 acceptedef2f899; verify0.
- T-44243 accepted246f2f6; verify0.
- T-44242 accepted5627293; verify0.
- T-44241 accepted60e5e56; verify0.
- T-44237 acceptedfeeaef3; verify0.
- T-44238 acceptedcdd2dec; verify0.
- T-44240 acceptedc93ec77; verify0.
- T-44236 accepted63aa0ad; verify0.
- T-44235 accepted683c6b5; verify0.
- T-44234 acceptedac0a46e; verify0.
- T-44233 accepteddb3cf1b; verify0.
- Phase5 T360–T366 complete; parent d666cf6/b90911f/b18819f, root60 browser PASS, build/lint/types/CSS gates0, production guide hidden.
- T44232 c6787b1 staged lock/recalculate router; T44229 c2616e0 helper wiring full227 PASS/live PASS.
- T44230 fdb63e2 target44px; T44231 e6efcc1 FLIP; T44225 54449f5 and T44226 4b35c7a browser specs accepted.
- Earlier child task history/evidence in git and CURRENT_STATE; remaining task inventory docs/overhaul-plan.md.
