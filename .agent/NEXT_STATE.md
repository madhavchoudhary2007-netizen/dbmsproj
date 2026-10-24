# NEXT_STATE
updated_at: 2026-10-23
phase: 3 T331 extraction; Phase5 T360–T363verified, T364/T365inprogress (Phases0–2 complete; baseline51.2974)

## Queue
### T-44217 W1 — OPEN
- target_files: frontend/components/nb/table.tsx, frontend/components/nb/state.tsx
- contract: T365 typed five-state table with preserved selection and internal scrolling, plus skeleton row-count passthrough.
- verify: bash scripts/eval/lint-spacing.sh && bash scripts/eval/lint-banned.sh && bash scripts/eval/lint-motion.sh && bash scripts/eval/lint-neobrutal.sh && npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0

### T-44216 W1 — OPEN
- target_files: frontend/components/nb/modal.tsx, frontend/components/nb/tabs.tsx
- contract: T365 native modal and controlled accessible folder tabs, using existing lifecycle hook.
- verify: bash scripts/eval/lint-spacing.sh && bash scripts/eval/lint-banned.sh && bash scripts/eval/lint-motion.sh && bash scripts/eval/lint-neobrutal.sh && npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0

## Blocked
- Previous6Luna usage-limit blocker superseded byowner5.6/high authorization; availability pendingfirstdispatch.

## Deferred
- T-44132 (W3, before claiming P-3): bundle checker counts only rootMainFiles+page chunk, omitting layout/shared dependency assets; add fixture regression and measure fullinitial asset graph with unchanged170KB threshold.

## Done
- T-44212 accepted46129c0; verify0.
- T-44215 accepted0bd674b; verify0.
- T-44211 accepted8275aab; verify0.
- T-44213 accepted471cb56; verify0.
- T-44210 accepted8ba857e; verify0.
- T-44214 accepted5ee4710; verify0.
- T-44208 accepted72a5b82; verify0.
- T-44209 accepted89c82af; verify0.
- T-44204 acceptede4a3f6c; verify0.
- T-44205 accepted65bd176; verify0.
- T-44203 accepted6eefdaa; verify0.
- T-44207 accepted2bc94fb; verify0.
- T-44206 accepted35ba591; verify0.
- T-44200 accepted47c0408; verify0.
- T-363 accepted13f614a; verify0.
- Recentaccepted tasks andevidence in CURRENT_STATE andgit history; earlierqueue fullyretained in docs/overhaul-plan.md.
