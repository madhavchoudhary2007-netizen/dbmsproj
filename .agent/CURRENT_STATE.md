# CURRENT_STATE
updated_at: 2026-10-25
git_head: 0f0ec37
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
- Worker switch implementedba3fa7c/4645e52; allcustom-role toolmetadata gpt-6-luna/high, <=2workers; freshroles succeeded repeatedly. No deps added.
- T379 exactsplit source complete: special-pages9lines re-export7pages; live standalone149lines1af6714 andwireb0d6bcc. Dashboard/Sessions/Stewards/Pit/Analytics/DBMS source moves checked exactbytes/AST. Rootfocusedbrowser totals120sessions/55stewards/100pitDBMS/105analyticslive/60live; evidence T379*.browser.raw.log. Runtime24PASS0skip (--experimental-vm-modules), script added0752dcf; browserdiscovery remains1100cases.
- ParentT379 remainsUNACCEPTED: build/types/lint0 T379.final-build.raw.log; full1100mocked1020PASS80FAIL. Rootfixedbodydarkboot7a6fde5, actualheadingready445b08c, residualCSSmotionac27b29. Failure-only85cases70PASS15FAIL: all5motionPASS, body/headingchecksPASS;15remainingdesktopA3surface-sharefailures belong Phase7layouts. No gates waived. Use Phase7layouttasks as parentgate repairs, rerunfull beforeaccept.
- T44379 band64px regressed existing40px feed assertion; repaired09cae83 restoringoriginalCSS. Root95dashboard/primitive/feedbrowserPASS T381-hero-recovery.browser.raw.log afterrestoration. No assertionchanged. Packet missed sizeinvariant; recorded honestly.
- Backend latestfull T44386 e0f42fd:231PASS0fail/skip/xfailed plus liveacceptancePASS, T44386.full.raw.log. CRUD/WS/simulatorroutes extracted5bba15e/a52fd5b/1d7f717/a5bb1f7; WShelpers5ac053e; runnerbody7f62291 ASTexact. Main894lines, T331<=120stillopen; mainlegacyaliases/currentcallbacklookups retained untilT332.
- T381 KPIec4c854/hero02486b3/stat-hookd36776d accepted; root95browserPASS incl recovery and original40pxfeed. SharedNbStat defaults preserved; readonlytuple props. T44387 layout61cfaa0 root59browserPASS/1A3FAIL; planned lowerpaper panels pending.

## Safety / workflow
- Branchonly overhaul/neo-brutal; commits onlyaccept.sh, root independently reruns Verify; <=2 packet-onlycustomworkers, no model/effortoverride. Isolatedclones .agent/orchestrate.py; <=3files/150changedlines/task; normalize envelopes with actualstats.
- Workerchecks offline/no fixedports; rootowns browser/network/DB. Neveraccept during rootNext build/dev; helpers restore next-env/killownprocessgroups. One db-baseline at a time,18000 API; only apexgrid-test PG15432/Mongo27018 labelguarded. Never realDB/schema/data/volumes/.env/secrets/recursive removal. Owner status files excluded untouched, preserve run-loop edits.
- Preserve everyroute/feature/chart/modal/copy/aria/data/stateclass/DBMShash; fivestates/44targets/tokens/reducedmotion. Never changegates/assertions. Latest spacing/banned/motion/neobrutal all0. Wrongroot invocation nonexistentlint-colors returned127, corrected actualfourthscript0.

## Open risks / next
- T331/T332 DI and strictmypy212errors/24files atT44256 (stale), zero requiredT339; coverage/batching/DBMSshowcase/finaleval pending. Transitional wrappers/factorycallbacks remain.
- T44132 bundlechecker misses layout/sharedassets, repair beforeP3 with170KB unchanged. Lighthouseabsent, FPS17untilT41316.7, hostedCIunverified. Final>=95/allhardgates/noNOT_RUN; neverclaimobsoleteaggregate current.
- FinishT379 palettegate via Phase7dashboard/resources/live/sessions/stewards/pit/standings/analytics/DBMS perplan; DBMSredesign dependsPhase4.

## Orchestrator direct edits / process findings
- Productglue this turn14lines only, previous T44250 plus2importintegration lines. Workers implement all otherproductchanges.
- Actualstats normalized independently; worker countmisreports caughtpreaccept. Clone dependencyrace44348 and testharnesslint44350 repaired withoutassertchanges. W1localRow boundary44351 correctedpreaccept. Root44349 eagerfactory proposal repairedlazyrefs.
- T44366 introduced5newdepswarnings, repairedstabledeps/max-warnings0 beforeaccept627d48a; root60livebrowserPASS. T44367 rootpacket mistakenlyselected DBlease tests; active-owner failures, correctedoffline24PASS and rootfull231PASS0skip/livePASS. No assertionschanged.
- Exact bytes/AST verified for all moves; evidence/results/Githistory retain details. Rootruntime command firstomittedrequired VMflag; correct --experimental-vm-modules gives24PASS0skip. No productdefect.

- T44388 accepted0f0ec37: independent sources, guarded reload/abort and five-state pureclassification. Root24runtimePASS/types/lint0; new actual-module regression tests next. T44389 CSSmove accepteda74019e, exactCSS unchanged.

- T-44388 accepted0f0ec37: Independent dashboard and health source results with five-state classification, guarded reloads and abort/generation cleanup. Verify0.
