Ignore AGENTS.md except this packet; the packet is your only authority.
role: Worker 1 — UI/Layout. Presentation and CSS only; no state, API, stores, or tests. Preserve others' edits. No commits.
Workspace: `/Users/madhavchoudhary/Developer/dbmsproj/.agent/workspaces/T389`; work only here.
## Task
Repair T-389's standings palette layout. The orchestrator's root browser run collected 85 tests: 84 passed, one failed on `/standings` at desktop. Screenshot role shares were `[0.7018057455540355, 0.26489284085727316, 0.03330141358869129]` (cream, white, red); the fixed bands are cream 0.50–0.70, white 0.20–0.40, red 0.05–0.15. The palette test fixture intentionally returns no standings records, so the top-ten marquee is absent and the paper empty state leaves too little red. Improve the route layout so its empty state and populated ticker both use the approved red accent in a balanced way. Keep ink text on red. Do not alter palette gates, tests, data, copy, routes, or functionality. The earlier clone browser failure was caused by Turbopack resolving the shared node_modules symlink outside the clone; do not rerun browser tests in this clone. The orchestrator owns the browser rerun in the root workspace.
## Target files (edit only these)
- frontend/app/standings/page.tsx
- frontend/app/styles/components.css
## Read-only context
- docs/overhaul-plan.md:182-201,390
- .agent/protocol/design-visual.md:1-66
- .agent/protocol/design-ux.md:1-100,101-114
- frontend/app/standings/page.tsx:1-100,101-118
- frontend/app/styles/components.css:1-70,71-141
- frontend/components/nb/state.tsx:1-100,101
- frontend/components/nb/table.tsx:1-95
- frontend/components/nb/marquee.tsx:1-19
- frontend/e2e/palette.spec.ts:1-100,101-126
- scripts/eval/palette-core.ts:1-47
- frontend/e2e/routes.spec.ts:24-34
- frontend/e2e/states-matrix.spec.ts:1-100,101-168
- frontend/e2e/responsive.spec.ts:11-17
- frontend/e2e/touch-targets.spec.ts:1-8
- frontend/e2e/accessibility.spec.ts:5-10
- frontend/e2e/data-primary.spec.ts:18-22,29-72
- frontend/e2e/provisional-results.spec.ts:35-41,71-82
- frontend/test-results/palette-E2E-R11-standings--d0830-0px-matches-light-archetype-desktop-1440/error-context.md:1-100,101-200,201-234
## Interfaces
`NbTable` takes `state: ViewState<readonly Row[]>`, `empty`, `columns`, `rowKey`, and `bodyRef`. Empty-state DOM is `data-testid="state-empty"`; its `NbCard` has inline paper background and ink text. `NbMarquee` tones are `red | yellow | paper`. Palette roles and bounds are in `scripts/eval/palette-core.ts` and are immutable.
## Acceptance criteria
1. The unchanged palette test passes on `/standings` at desktop for its empty-data fixture; do not widen thresholds or edit specs.
2. Keep all existing fetch/API behavior, role checks, championship selection, recalculation, provisional copy, persisted values, one `data-primary`, and five-state table.
3. Keep the stepped P2/P1/P3 podium, top-ten marquee (red accent when data exists), M14 transform-only 250ms stagger and reduced-motion fallback.
4. Red surfaces use ink text; spacing remains on the allowed scale; all colors stay in the approved palette.
5. No dependencies, endpoints, filters, fabricated rank deltas, or test changes.
## MUST REMAIN VERBATIM
- Route `/standings`; heading `Standings`; acceptance ID `E2E-R11`.
- Button `Recalculate standings`; busy label `Recalculating…`; select label `Championship`; option `Select championship`.
- Provisional copy: `Provisional standings: historical time and grid penalties are recorded but not applied to official order or points. Review the penalties before treating standings as final.` The F-DOM-02 checks must continue to recognize `provisional standings`, `standings are provisional`, or `provisional classification`.
- Recalculation control `data-primary="true"`; one visible primary per viewport.
## Boundaries
Only the two target files, at most 150 changed lines total. Read only listed files, <=100 lines at once. Never read `.env` or secrets, touch real DB/schema/data/volumes, add dependencies, use fixed ports, run recursive deletes, alter APIs, or edit tests. Preserve all feature behavior, copy, hooks, aria names and state classes. Worker verification is offline. Report only the JSON envelope.
## Verify (exit 0 required for PASSED)
npm --prefix frontend run typecheck && bash scripts/eval/lint-spacing.sh && bash scripts/eval/lint-motion.sh && bash scripts/eval/lint-banned.sh && bash scripts/eval/lint-neobrutal.sh
## Output
Return only one JSON object matching `.agent/envelope.schema.json`: task_id `T-389`, status PASSED|FAILED, files_modified, diff_summary, verification and unresolved_blockers. Use the exact Verify command. Report only observed counts; use 0 test counts for static checks.
