# NEXT_STATE
updated_at: 2026-10-24
phase: 3 T331 + 7 route redesign; Phases0–2,5–6 COMPLETE; no current score

## Queue
### T-44282 W2 — OPEN
- target_files: frontend/lib/use-session-data.ts, frontend/components/special-pages.tsx
- contract: T379 extract SessionPage initial list loading into typed useSessionData hook, retaining all other logic and JSX.
- verify: npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0

### T-44281 W1 — OPEN
- target_files: frontend/app/globals.css, frontend/app/styles/login.css
- contract: T380 finish login legacy cleanup: remove remaining mobile/shared global login selectors and retain required scoped presentation.
- verify: bash scripts/eval/lint-spacing.sh && bash scripts/eval/lint-banned.sh && bash scripts/eval/lint-motion.sh && bash scripts/eval/lint-neobrutal.sh && npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0

## Blocked
- None currently. Owner5.6/high override2bc94fb verified byfreshsuccessfulworkers.

## Deferred
- T-44132 (W3, before claiming P-3): bundle checker counts only rootMainFiles+page chunk, omitting layout/shared dependency assets; add fixture regression and measure fullinitial asset graph with unchanged170KB threshold.

## Done
- T-44280 accepted097578f; verify0.
- T-44279 acceptedc16e5bb; verify0.
- T-44278 accepted3bade73; verify0.
- T-44277 accepted48bdf7b; verify0.
- T-44276 acceptedb8d5460; verify0.
- T-44275 accepted12449c7; verify0.
- T-44274 accepted7659085; verify0.
- T-44273 accepted1f7a2d7; verify0.
- T-44272 acceptedd7ece24; verify0.
- T-44271 accepteda98c95c; verify0.
- T-44270 accepted298fef5; verify0.
- T-44268 accepted6590437; verify0.
- T-44269 accepteded34d9d; verify0.
- Phase6 T370 da5a72d/T3718e498d7;481 browser checks, build/static gates0; details CURRENT_STATE and evidence logs.
- T44266 LoginArt/CSS622aafa staged; T44267 reservation servicee5507c9 staged.
- Session lifecycle wired94a7009; full231 PASS0skip/live PASS.
- Earlier accepted task/evidence history in git and .agent/results; remaining graph docs/overhaul-plan.md.
