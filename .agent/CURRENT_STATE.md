# CURRENT_STATE
updated_at: 2026-10-25
git_head: 8d44b1f
branch: overhaul/neo-brutal
architect_sha256: 3c4ab0a82eb81bc885d5b4a6baf4f64728a6cb87181b515f7cbffcb77c3701ae
harness: codex; orchestrator gpt-6.1-sol/medium; workers gpt-6-luna/high (latest owner override2026-10-25), cap2
archetype: Neo-Brutal Motorsport light, approved ADR007
last_eval_score: obsolete baseline51.2974358974359; no current score; final T430

## Verified milestones
- Phases0–2,5–6 COMPLETE (5/12); Phase3 T331 extraction ongoing, main1220lines target<=120. Phase4 and7–11 unfinished. Owner requests autonomous all12 completion, no routine questions.
- Phase5 T360–366 complete: Tailwind4.3.3/SpaceGrotesk500,700/SpaceMono400,700, tokens/textures/plinth/primitives. Root60 browser cases and production guide-hidden/noindex/zero-write checks pass; build/static0. Evidence T366.matrix.browser.raw.log and prior Git/results.
- Phase6 T370 da5a72d/T3718e498d7 complete. Root481 browser checks:85axe,20edge,15feed,10drawer,80routes,75targets,80primary,20auth,96responsive. Build/types/lint/fourCSS0. Dashboard cache4/mapper3 offline cases pass. Shared feed visible30s polling, request dedupe, cancellation and five states verified. ADR012 next_event additive query/tests implemented; no other current API changes.
- Backend latest full231PASS/0skip/livePASS after45cbcad; T44314.full.raw.log. T44274 repaired nested runtime route discovery retaining STEWARD assertion. API snapshot9/runtime uniqueness2, required-input27, seeded GET goldens14 retained.
- T331 results read/write, session action, pit writes, DBMS SQL/Mongo/locks/archive/laps/core tick/stewards extracted. Preserve legacy main Python aliases and late-bound callbacks; Decision removal once caused7failures, fixed5ee4710. Standard typed services only, no locals/proxy/class/suppression tricks. Factories/global DI transitional T332 debt.

## Active work / evidence
- T380 login COMPLETE0a3e206: root80browserPASS T380.final.browser.raw.log; settled5widthvisuals reviewed; build/types/lint0 T380.build.raw.log. Layout60/40 desktop,240mobileart, motifs/3type sizes; exactauthcopy retained. New login-layout tests cover geometry/busy/error. NbButton aria-busy fixed0d7dd28, mobilefeed focus c44f8ed; no gate weakened.
- T379 Dashboard exactmodule/hook complete; Sessions exactmodule/hooks/components complete03ab0d5 and8actual-module operation tests bd3f9c2. Root120dashboard/sessionbrowserPASS T379-sessions.browser.raw.log. Steward hook3989f9d,reportf51818a,sanctions0f39a4b,module7bc73c9 wiredf2ef65e; byte-identical page/body verified. Rootstewardbrowser currently running. RemainingLive/Pit/Analytics/DBMS split beforeT381.
- T331 latest incidentsb0972ed and pit cancellation45cbcad full231PASS0skip/livePASS T44312/T44314.full.raw.log. Reset measurement helper e0e553d ASTexact; fullT44317 running/completed log toinspect. Main1220lines. Naming parity12seed/countchecks, restore/demo/pit scheduling previousfulls green. Transitional main wrappers/callback injection preserve tests pendingT332.
- Owner latest switch gpt-6-luna/high: profiles ba3fa7c/4645e52; boot0; fresh custom W1/W2 toolmetadata confirm6luna/high. Prior5.6 usage-limit worker44316 retry returnedvalidbefore switch; 44318 oldworker interrupted before edits. Root44319 firstverify had shellquotingerror; corrected using shlex.quote, rerunaccept0; erroneous premature mark removed beforecommit.
- Active: W1T44321 DBMS exactmodule move; W2T44322 finalization helper; T44318 pit hook result readyforreview. At most2active workers. Allresults/patches/acceptlogs inGit/.agent/results.

## Safety / workflow
- Branch only overhaul/neo-brutal; commits only accept.sh, independently rerun exact Verify; max2 custom-role packet-only workers, no model/effort overrides. Isolated clones via .agent/orchestrate.py; <=3files/150 changedlines/task. Metadata state/envelopes normalized with realstats and integercounts.
- Worker checks offline/no fixed-port servers; root owns network/browser/DB. Never accept during root Next build/dev process; helpers restore next-env and kill only own loopback processgroups. One db-baseline at a time,18000 API; apexgrid-test only (PG15432/Mongo27018), projectlabels guarded. Never realDB/schema/data/volumes, .env/secrets, recursive removal. Owner status.sh/scripts/agent/status.sh excluded untouched; preserve run-loop edits.
- All routes/features/copy/charts/modals/aria/data/stateclasses/DBMS hashes retained; five states/44targets/token spacing/reduced motion. Palette bands unchanged, correct layout not thresholds. All details and accepted envelopes in Git/.agent/results; .agent/check-login-visual.py captures settled screens/geometry using temporary root server.

## Open risks / next
- T331 main currently1220; strict mypy212errors/24files at T44256, zero required T339. Coverage/DI/batched simulator writes/DBMS showcase and final evaluation pending.
- T44132 bundle checker misses layout/shared assets; fix before P3 (170KB unchanged). Lighthouse absent, FPS17ms until T41316.7, hostedCI unverified. Final aggregate>=95/allhardgates/no NOT_RUN required; never claim obsolete score current.
- Finish remaining T379 splits, then dashboard/resources/live/session/stewards/pit/standings/analytics/DBMS according to plan. DBMS redesign also needs Phase4. Keep backend T331 progressing in parallel and full suite after each wiring.

## Orchestrator direct edits
- T44250 shell glue8add/4remove (12productlines this turn), logged and accepted e765662; all other product implementation delegated. Metadata/config/ADRs/packets/state/root verification helpers only. No new dependencies this continuation.









- T44319 first acceptance failed shell quoting in root-authored verify; corrected with shlex.quote, no false acceptance retained.



- T-44318 accepted3b7ca06: Stage exact PitWall state, effects and actions in a typed hook; original presentation remains unchanged. Verify0.

- T44321 worker envelope overreported removals16vsactual14; root normalized realstats beforeaccept, no out-of-scope changes.

- T-44321 accepted8d44b1f: Move exact DbmsCenter page and retain compatibility reexport, auth guard and overview hash. Verify0.
