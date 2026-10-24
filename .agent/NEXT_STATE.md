# NEXT_STATE
updated_at: 2026-10-24
phase: 3 T331 extraction + 6 shell; Phases0–2 and5 COMPLETE; no current score

## Queue
### T-44258 W3 — OPEN
- target_files: frontend/e2e/edge-resilience.spec.ts
- contract: Disambiguate existing dashboard Refresh selector after addition of separately named feed refresh button; strengthen exact-name match without weakening any recovery assertion.
- verify: npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0 && cd frontend && ./node_modules/.bin/playwright test e2e/edge-resilience.spec.ts --list

### T-44257 W1 — OPEN
- target_files: frontend/components/shell-feed.tsx, frontend/app/styles/shell.css
- contract: Fix measured light-shell integration accessibility regressions and remove legacy1480px content cap, without redesigning route markup.
- verify: bash scripts/eval/lint-spacing.sh && bash scripts/eval/lint-banned.sh && bash scripts/eval/lint-motion.sh && bash scripts/eval/lint-neobrutal.sh && npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0

## Blocked
- None currently. Owner5.6/high override2bc94fb verified byfreshsuccessfulworkers.

## Deferred
- T-44240 (O/W3/W2, T370 dependency): planned next-event ticker requires a real next_event field absent from /dashboard; draft own additive ADR, focused lock review/tests, then add read-only field on disposable acceptance. Never fabricate next-event data.
- T-44132 (W3, before claiming P-3): bundle checker counts only rootMainFiles+page chunk, omitting layout/shared dependency assets; add fixture regression and measure fullinitial asset graph with unchanged170KB threshold.

## Done
- T-44256 accepted3e902c2; verify0.
- T-44251 accepted3483224; verify0.
- T-44254 accepted145c55f; verify0.
- T-44255 acceptedad1383a; verify0.
- T-44250 acceptede765662; verify0.
- T-44248 accepteddfcf8ac; verify0.
- T-44253 accepted2aa2b87; verify0.
- T-44252 accepted39f2e59; verify0.
- T-44249 accepted939fea6; verify0.
- T-44247 acceptedc18eb51; verify0.
- T-44245 acceptedc1ecce3; verify0.
- T-44246 accepted35b904f; verify0.
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
