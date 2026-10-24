# CURRENT_STATE
updated_at: 2026-10-24
git_head: 60cc688
branch: overhaul/neo-brutal
architect_sha256: 3c4ab0a82eb81bc885d5b4a6baf4f64728a6cb87181b515f7cbffcb77c3701ae
harness: codex; orchestrator gpt-6.1-sol/medium; workers gpt-5.6-luna/high (latest owner override), cap2
archetype: Neo-Brutal Motorsport (light), ADR007 approved
last_eval_score: obsolete baseline51.2974358974359; no current score; final evaluation T430

## Verified milestones
- Phases0–2,5–6 COMPLETE (5 of12). Phase3 T331 extraction remains; main1424 lines, target<=120. Phase4 and7–11 unfinished. Owner requests autonomous completion of all12, no routine questions.
- Phase5 T3602ad337f/T3611e61efd/T362c0781f9/T36313f614a/T364d666cf6/T365b90911f/T366b18819f accepted through accept.sh. Tailwind4.3.3, SpaceGrotesk500/700 + SpaceMono400/700, scoped tokens/textures/plinth and complete shared primitives. Existing production routes adopt them in Phases6–7.
- Root60 browser cases PASS across320/375/768/1440/5120 (T366.matrix.browser.raw.log). Parent accept reruns: motion30 PASS, primitive30 PASS, axe375/1440 2 PASS; keyboard/font4 per runner. Build/lint/types0 and four CSS lints0. /__nb dev200, production not-found visible + noindex + guide absent + zero writes. Next streamed notFound HTTP200 is documented behavior; do not substitute status-only checks (.agent/check-guide-production.py).
- Phase5 fixes: escaped %5F_nb route6b9c6f7, explicit44px controlsfdb63e2, FLIP mount/scroll guarde6efcc1. Browser tests wait fonts/finite animations for axe without relaxing thresholds; reduced motion asserts immediately.
- Backend latest root full231 PASS,0 failed/skipped, live acceptance PASS after session lifecycle wiring94a7009 (T44265.full.raw.log). Earlier archive/lap wiring also227 PASS. API snapshot9 + runtime uniqueness2 are permanent; required-input regressions27 and seeded GET goldens14 retained. No API/schema changes in current moves.
- T331 extracted core tick46129c0, stewards89c82af, DBMS SQL/Mongo/archive2e5c5a4 and lapsef0dee3; lock helpers225b2b8 wiredc2616e0. api/dbms_lock.py stagedc6787b1 and wireddb3cf1b; originals removed. Exact lock body retained as module-level _run_lock_demo with explicit typed dependencies, thin public wrapper; no suppression/locals/classes. Factories/globals are transitional T332 debt.
- Preserve legacy main aliases and late-bound callbacks: Decision removal caused7 failures fixed5ee4710. OpenAPI alone cannot prove Python alias/runtime uniqueness compatibility.

## Next work
- T380 staged LoginArt/CSS622aafa; T44268 wiring6590437 accepted with mobile240px/contrast/copy fixes and unused legacy CSS removal. T44271 form primitives a98c95c accepted; browser65pass5palettefail initially; W1T44275 lightbody/redfeed12449c7 and W3T44278 realform/font/finite-animation synchronization3bade73 accepted, rerun70PASS; post-cleanup c16e5bb/b6fa4ad again70PASS T44283.browser.raw.log. Dashboard hook d7ece24 exactlogic and exactpage copy1f7a2d7 wired b8d5460; Session data hook7cb29bf accepted; remaining T379 page splits pending. Auth logic untouched. Pit reservation servicee5507c9 exact3bodies staged; T44269 thinrouter ed34d9d accepted; T44270 wiring298fef5 accepted. Full pit gate repaired by W3T44274 recursive discovery only (original STEWARD assertion retained):231pass0skip/livePASS. Restore helpers48bdf7b full231pass0skip/livePASS; auto restore097578f exactAST moved, full running.
- Phase6 parent T370/T371 accepted da5a72d/current HEAD. Root481 browser checks PASS in combined evidence T370.evidence.raw.json:85axe,20edge,15feed,10drawer,80routes,75targets,80primary,20auth,96responsive. Build/types/lint/fourCSS gates0. Cache4 and mapper3 offline cases pass. Shell retains routes/auth/copy/hash hooks; real next_event additive ADR012 in place.
- Start Phase7 login/dashboard before resources/live/session/stewards/pits/standings/analytics/DBMS. Use docs/overhaul-plan.md graph; DBMS showcase also requires Phase4. T331 backend continues in parallel; keep main aliases/latecallbacks and run full disposable suite after each wiring.
- Palette across redesigned routes remains unverified; no band widening. Final score only atT430. Phase5 primitives60 browser cases passed; development guide hidden in production.

## Safety / workflow
- Only overhaul/neo-brutal; commits only accept.sh; max2 custom-role workers, fresh packet-only clones, no per-call overrides. Profiles/models.env2bc94fb bind5.6/high after owner request; successful workers and tool role metadata confirm availability. No quota blocker.
- <=3 target files and150 changed lines/task, exact worker Verify independently rerun. Workers offline/no fixed ports; root owns browser/network/disposable checks. Integrate one patch then accept before another. Never accept concurrently with another Next build/dev check; helpers restore next-env and kill only their own temporary loopback servers.
- Never .env/secrets, recursive deletion, real database/schema/volumes. Only disposable apexgrid-test (PG15432/Mongo27018), project labels guarded, one db-baseline runner at a time on18000. Real backend has no source bind/reload. Owner status.sh and scripts/agent/status.sh excluded and untouched; preserve run-loop.sh owner edits.
- .agent/orchestrate.py persists queue/clone/integrate/mark. Worker envelopes require actual stats/integer static counts0, no extra keys. All features/routes/copy/hooks/aria/stateclasses/dbms hashes retained; five states/44px/token spacing/reduced motion mandatory.

## Open risks
- T331 giant main/transitional factories; strict mypy212 errors/24files (T44256.mypy.raw.log); zero required T339. No thresholds relaxed.
- T44132 bundle checker omits layout/shared assets; fix before P3. Lighthouse absent, FPS gate17ms until T41316.7, hosted CI unverified. Final score>=95/all hard gates/no NOT_RUN required; never present obsolete score as current.
- Worker review caught nested main/dead modal control (corrected), accidental root demo hook (removed only worker-owned unaccepted copy), and T44232 complexity suppression/locals namespace tricks (rejected, standard explicit helper accepted). No other work reverted; no test weakened.

## Orchestrator direct edits
- T-44250: 8 additions/4 removals in shell.tsx as cross-worker glue connecting accepted W1 presenters and W2 hook/mapper; no bulk implementation. Metadata, architecture/config/ADRs, packets/state/envelopes/root acceptance helpers and approved installs only. Applying worker patches is integration, not authorship. No new dependencies this continuation.

- TASTE login screenshot T44283: broken AG wrap/lime, tiny checker, card5sizes/textovergrid. T44284 scoped type/brand/checker/backing repair in progress; no threshold changes. T44285 SessionPage operations move in progress.

- T-44285 accepted58aad6d: Extract three SessionPage async operations with typed callbacks and exact request/error ordering; JSX unchanged. Verify0.

- T-44284 accepted27ee284: Fix measured login taste defects:44px yellow AG mark, three form type tiers, solid text backing and full-width checker texture. Verify0.

- T-44286 accepted60cc688: Stage three typed session write operations with unchanged serialization, modal updates and busy/error handling. Verify0.
