# NEXT_STATE
updated_at: 2026-10-24
phase: 3 T331 extraction + 6 shell; Phases0–2 and5 COMPLETE; no current score

## Queue
### T-44236 W2 — OPEN
- target_files: frontend/lib/dashboard-feed.ts
- contract: T371 shared dashboard read cache with10-second TTL and independent consumer cancellation.
- verify: npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0 && bash scripts/eval/lint-spacing.sh && bash scripts/eval/lint-banned.sh && bash scripts/eval/lint-motion.sh && bash scripts/eval/lint-neobrutal.sh

### T-44235 W1 — OPEN
- target_files: frontend/app/styles/shell.css
- contract: T370 stage responsive shell drawer and reduced-motion CSS before markup activation.
- verify: bash scripts/eval/lint-spacing.sh && bash scripts/eval/lint-banned.sh && bash scripts/eval/lint-motion.sh && bash scripts/eval/lint-neobrutal.sh && npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0

## Blocked
- None currently. Owner5.6/high override2bc94fb verified byfreshsuccessfulworkers.

## Deferred
- T-44240 (O/W3/W2, T370 dependency): planned next-event ticker requires a real next_event field absent from /dashboard; draft own additive ADR, focused lock review/tests, then add read-only field on disposable acceptance. Never fabricate next-event data.
- T-44132 (W3, before claiming P-3): bundle checker counts only rootMainFiles+page chunk, omitting layout/shared dependency assets; add fixture regression and measure fullinitial asset graph with unchanged170KB threshold.

## Done
- T-44234 acceptedac0a46e; verify0.
- T-44233 accepteddb3cf1b; verify0.
- Phase5 T360–T366 complete; parent d666cf6/b90911f/b18819f, root60 browser PASS, build/lint/types/CSS gates0, production guide hidden.
- T44232 c6787b1 staged lock/recalculate router; T44229 c2616e0 helper wiring full227 PASS/live PASS.
- T44230 fdb63e2 target44px; T44231 e6efcc1 FLIP; T44225 54449f5 and T44226 4b35c7a browser specs accepted.
- Earlier child task history/evidence in git and CURRENT_STATE; remaining task inventory docs/overhaul-plan.md.
