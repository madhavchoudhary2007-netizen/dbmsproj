# CURRENT_STATE
updated_at: 2026-10-24
git_head: 03ab0d5
branch: overhaul/neo-brutal
architect_sha256: 3c4ab0a82eb81bc885d5b4a6baf4f64728a6cb87181b515f7cbffcb77c3701ae
harness: codex; orchestrator gpt-6.1-sol/medium; workers gpt-5.6-luna/high (owner override2bc94fb), cap2
archetype: Neo-Brutal Motorsport light, approved ADR007
last_eval_score: obsolete baseline51.2974358974359; no current score; final T430

## Verified milestones
- Phases0–2,5–6 COMPLETE (5/12); Phase3 T331 extraction ongoing, main1368lines target<=120. Phase4 and7–11 unfinished. Owner requests autonomous all12 completion, no routine questions.
- Phase5 T360–366 complete: Tailwind4.3.3/SpaceGrotesk500,700/SpaceMono400,700, tokens/textures/plinth/primitives. Root60 browser cases and production guide-hidden/noindex/zero-write checks pass; build/static0. Evidence T366.matrix.browser.raw.log and prior Git/results.
- Phase6 T370 da5a72d/T3718e498d7 complete. Root481 browser checks:85axe,20edge,15feed,10drawer,80routes,75targets,80primary,20auth,96responsive. Build/types/lint/fourCSS0. Dashboard cache4/mapper3 offline cases pass. Shared feed visible30s polling, request dedupe, cancellation and five states verified. ADR012 next_event additive query/tests implemented; no other current API changes.
- Latest full backend after auto-restore097578f:231PASS,0fail/skip/xfailed + live acceptance PASS (T44280.full.raw.log). Pit298fef5 and restore48bdf7b also full231/live green. T44274 repaired nested runtime route discovery retaining STEWARD assertion. API snapshot9/runtime uniqueness2, required-input27, seeded GET goldens14 retained.
- T331 results read/write, session action, pit writes, DBMS SQL/Mongo/locks/archive/laps/core tick/stewards extracted. Preserve legacy main Python aliases and late-bound callbacks; Decision removal once caused7failures, fixed5ee4710. Standard typed services only, no locals/proxy/class/suppression tricks. Factories/global DI transitional T332 debt.

## Active work / evidence
- T380 ACCEPTED login route now uses LoginArt/NbCard/NbField/NbInput/NbButton,60/40 desktop/art240mobile; auth logic unchanged. Legacy desktop/mobile/shared login CSS removed c16e5bb/b6fa4ad. Root70 generic login checks pass after type/brand/checker/textbacking27ee284 (T44284.browser.raw.log). T44283 build/types/lint0; final production build/types/lint0 (T380.build.raw.log).
- Settled screenshot caught mobile motif clipping missed by generic checks:523cd33 fixes internal44px horizontal feed. New actual geometry/busy test6d32c9e initially failed native aria-busy override and wrong test ink fixture17instead0; product0d7dd28 preserves calleraria-busy, testc659147 exactblack correction. Final80browserPASS (T380.final.browser.raw.log), settledvisuals reviewed; c44f8ed adds keyboardfocus to mobilefeed. Testnormalization fixturec533c35 retains exact existing401prefix. T380 accepted; no assertions/gates weakened.
- T379 Dashboard exact module move b8d5460 and typed data hookd7ece24 done. Session loader7cb29bf, async operations58aad6d, writes60cc688 wired3e715d5, simulator86d745b wired52e84a0; original behavior/copy/JSX retained. Hook77d775d wiredbcf158f, resultsviewc8d5a5a, modals2f422c0, controls6e88345 accepted;8 actual-module offline operation tests bd3f9c2 pass. Overview2be7bec extracted; W1T44306 exact SessionPage module staging in progress, next wire then root mocked regression/build. Remaining page splits required before redesigns.
- T44292 driver name generation1a2b573: root12 seed/carcount output+RNGstate parity checks pass; main1368. Full disposable suite T44292.full.raw.log231PASS0skip/livePASS. Demo creation8e88bb7 exactAST moved, full T44302 231PASS0skip/livePASS. T44305 pitrefresh acceptance in progress; rootfull afteraccept.

## Safety / workflow
- Branch only overhaul/neo-brutal; commits only accept.sh, independently rerun exact Verify; max2 custom-role packet-only workers, no model/effort overrides. Isolated clones via .agent/orchestrate.py; <=3files/150 changedlines/task. Metadata state/envelopes normalized with realstats and integercounts.
- Worker checks offline/no fixed-port servers; root owns network/browser/DB. Never accept during root Next build/dev process; helpers restore next-env and kill only own loopback processgroups. One db-baseline at a time,18000 API; apexgrid-test only (PG15432/Mongo27018), projectlabels guarded. Never realDB/schema/data/volumes, .env/secrets, recursive removal. Owner status.sh/scripts/agent/status.sh excluded untouched; preserve run-loop edits.
- All routes/features/copy/charts/modals/aria/data/stateclasses/DBMS hashes retained; five states/44targets/token spacing/reduced motion. Palette bands unchanged, correct layout not thresholds. All details and accepted envelopes in Git/.agent/results; .agent/check-login-visual.py captures settled screens/geometry using temporary root server.

## Open risks / next
- T331 main still1378; strict mypy212errors/24files at T44256, zero required T339. Coverage/DI/batched simulator writes/DBMS showcase and final evaluation pending.
- T44132 bundle checker misses layout/shared assets; fix before P3 (170KB unchanged). Lighthouse absent, FPS17ms until T41316.7, hostedCI unverified. Final aggregate>=95/allhardgates/no NOT_RUN required; never claim obsolete score current.
- Finish remaining T379 splits, then dashboard/resources/live/session/stewards/pit/standings/analytics/DBMS according to plan. DBMS redesign also needs Phase4. Keep backend T331 progressing in parallel and full suite after each wiring.

## Orchestrator direct edits
- T44250 shell glue8add/4remove (12productlines this turn), logged and accepted e765662; all other product implementation delegated. Metadata/config/ADRs/packets/state/root verification helpers only. No new dependencies this continuation.

- T-44306 accepted478cffa: Stage byte-identical small SessionPage module with its typed hook and focused presentation imports; no route wiring yet. Verify0.

- T-44307 accepted03ab0d5: Activate exact SessionPage module via compatibility reexport; remove old copy and session-only imports. Verify0.
