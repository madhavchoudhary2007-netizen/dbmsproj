# CURRENT_STATE
updated_at: 2026-10-25
git_head: 445b08c
branch: overhaul/neo-brutal
architect_sha256: 3c4ab0a82eb81bc885d5b4a6baf4f64728a6cb87181b515f7cbffcb77c3701ae
harness: codex; orchestrator gpt-6.1-sol/medium; workers gpt-6-luna/high, cap2
archetype: Neo-Brutal Motorsport light, approved ADR007
last_eval_score: obsolete baseline51.2974358974359; no current score; final T430

## Verified milestones
- Phases0–2,5–6 COMPLETE (5/12). Phase3 T331/main<=120 unfinished; Phase4,7–11 unfinished. Owner requests autonomous all12, no routinequestions. Plan docs/overhaul-plan.md authoritative.
- Phase5 T360–366 complete: Tailwind4.3.3, SpaceGrotesk500/700+SpaceMono400/700, tokens/textures/plinth/primitives; root60browser and productionguidehidden/noindex/zero-write checks pass, build/static0. Evidence T366.matrix.browser.raw.log/Git.
- Phase6 T370da5a72d/T3718e498d7 complete:481browserchecks across axe/edge/feed/drawer/routes/targets/primary/auth/responsive. Build/types/lint/fourCSS0. Feed30svisiblepoll/cache10s/dedupe/cancellation/fivestates verified. ADR012 dashboard next_event additivequery/tests implemented.
- Login T3800a3e206 COMPLETE: root80browserPASS T380.final.browser.raw.log; settled5widthvisuals reviewed; build/types/lint0 T380.build.raw.log. Authlogic/copy unchanged; mobilegeometry/keyboardfeed and calleraria-busy fixes covered.

## Active work / evidence
- T379 exact moves: Dashboard hook/module; Sessions hooks/actions/components/module03ab0d5 plus8real-module operationtestsbd3f9c2, root120browserPASS. Steward f2ef65e root55browserPASS; Pit28eb2e1+DBMS8d44b1f root100browserPASS; Analyticsbd20525. Root105live/analyticsbrowserPASS T379-live-analytics.browser.raw.log. Only Live split remains beforeT379/T381.
- Live exact extracted charts5c977c3, records1c47bc2, timing409d428, latestcf15b05, snapshot477af90; data7603ad3 and demoactionsad281aa staged. Demoactions7718c89 and data8a33d97 (driverIds included) wired; controls/modal171cb46, records96cabf5 wired. Lazyactioncontext57f81b3 avoids render-time refs, fourruntimecases266e518/harnessrepair20b8d27. Selectorse517c82 wired; currentrunpredicatec3d1e7c wired66bccc6. Five timing/gap/lapcap/demo/predicatetests aeb35ee rootPASS; root55updatedlivebrowserPASS T379-live-controls.browser.raw.log. Streamtypesd181250 and exactbodye66ff78 staged; Stream wired065361e; root10streambrowserPASS plus60list-poll browserPASS T379-live-list.browser.raw.log; allfourCSSlints0.
- Backend T331 results/sessionaction/pit/DBMS/SQL/Mongo/locks/archive/laps/stewards/runtimehelpers extracted. Preserve legacy main aliases and currentcallbacklookup untilT332; removingDecision once caused7failures, fixed5ee4710. BodyAST parity independently checked for moves. No locals/proxy/class tricks.
- Latest full backend after simulatorroutea5bb1f7:231PASS,0fail/skip/xfailed + liveacceptancePASS, T44341.full.raw.log. Earlier restore/demo/incident/pit/reset/finalization/lifecycle fulls also231/livegreen. T44341 bbbd12e tickpersistence full231PASS0skip/livePASS T44341.full.raw.log. Main1047lines after CRUDrouterwire; root6callASTparity and11offlinePASS, fullT44359 confirms231PASS0skip/livePASS; fullT44364 confirms231PASS0skip/livePASS; fullT44367 confirms231PASS0skip/livePASS; runtime24PASS using --experimental-vm-modules. Snapshot9/runtimeuniqueness2/input27/seededGET14 retained. T44274 nestedrouter testlookup repair preserved STEWARDassertion.
- Owner worker switch implementedba3fa7c/4645e52; boot0 and freshcustom-role toolmetadata6luna/high. Prior5.6 quota retry44316 finishedbefore switch; old44318 interruptedbeforeedits. No dependencies added this continuation.

## Safety / workflow
- Branchonly overhaul/neo-brutal; commits onlyaccept.sh, root independently reruns Verify; <=2 packet-onlycustomworkers, no model/effortoverride. Isolatedclones .agent/orchestrate.py; <=3files/150changedlines/task; normalize envelopes with actualstats.
- Workerchecks offline/no fixedports; rootowns browser/network/DB. Neveraccept during rootNext build/dev; helpers restore next-env/killownprocessgroups. One db-baseline at a time,18000 API; only apexgrid-test PG15432/Mongo27018 labelguarded. Never realDB/schema/data/volumes/.env/secrets/recursive removal. Owner status files excluded untouched, preserve run-loop edits.
- Preserve everyroute/feature/chart/modal/copy/aria/data/stateclass/DBMShash; fivestates/44targets/tokens/reducedmotion. Never changegates/assertions. Latest spacing/banned/motion/neobrutal all0. Wrongroot invocation nonexistentlint-colors returned127, corrected actualfourthscript0.

## Open risks / next
- T331/T332 DI and strictmypy212errors/24files atT44256 (stale), zero requiredT339; coverage/batching/DBMSshowcase/finaleval pending. Transitional wrappers/factorycallbacks remain.
- T44132 bundlechecker misses layout/sharedassets, repair beforeP3 with170KB unchanged. Lighthouseabsent, FPS17untilT41316.7, hostedCIunverified. Final>=95/allhardgates/noNOT_RUN; neverclaimobsoleteaggregate current.
- FinishLive split then dashboard/resources/live/sessions/stewards/pit/standings/analytics/DBMS perplan; DBMSredesign dependsPhase4.

## Orchestrator direct edits / process findings
- Productglue this turn14lines only, previous T44250 plus2importintegration lines. Workers implement all otherproductchanges.
- Actualstats normalized independently; worker countmisreports caughtpreaccept. Clone dependencyrace44348 and testharnesslint44350 repaired withoutassertchanges. W1localRow boundary44351 correctedpreaccept. Root44349 eagerfactory proposal repairedlazyrefs.
- T44366 introduced5newdepswarnings, repairedstabledeps/max-warnings0 beforeaccept627d48a; root60livebrowserPASS. T44367 rootpacket mistakenlyselected DBlease tests; active-owner failures, correctedoffline24PASS and rootfull231PASS0skip/livePASS. No assertionschanged.
- Exact bytes/AST verified for all moves; evidence/results/Githistory retain details. Rootruntime command firstomittedrequired VMflag; correct --experimental-vm-modules gives24PASS0skip. No productdefect.

- T-44370 acceptedb6494d1: Remove only unused legacy imports, keeping LiveTiming function bytes and compatibility exports unchanged. Verify0.

- T-44371 acceptedb0d6bcc: Activate standalone LiveTiming through compatibility export; remove obsolete local body and imports. Verify0.

- T-44372 accepteda5bb1f7: Move simulator control route into API module preserving response, role dependency and late-bound callbacks. Verify0.

- T379 final build/types/lint0; full mocked browser1100collected:1020PASS/80FAIL, no complete-parentaccept. Failures75body-luminance darkdocument and5reduced-motion animations. T44374 accepted7a6fde5 lightdocument; T44375 445b08c waitsactualh1. Probe traces actualfeed CSS transitions0.01ms, not devtools; T44376 makesfallbackstatic. No thresholds/tests relaxed.

- T-44373 accepted0752dcf: Separate Playwright spec discovery and expose all 24 Node runtime tests through an explicit runnable script. Verify0.

- T-44374 accepted7a6fde5: Use approved cream document background and ink authentication-loading text with light colour scheme. Verify0.

- T-44375 accepted445b08c: Wait for actual route heading before unchanged palette, luminance and contrast measurements. Verify0.
