# CURRENT_STATE
updated_at: 2026-10-25
git_head: 627d48a
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
- Latest full backend after tickpersistbbbd12e:231PASS,0fail/skip/xfailed + liveacceptancePASS, T44341.full.raw.log. Earlier restore/demo/incident/pit/reset/finalization/lifecycle fulls also231/livegreen. T44341 bbbd12e tickpersistence full231PASS0skip/livePASS T44341.full.raw.log. Main1047lines after CRUDrouterwire; root6callASTparity and11offlinePASS, fullT44359 confirms231PASS0skip/livePASS; fullT44364 running after CRUDwire. Snapshot9/runtimeuniqueness2/input27/seededGET14 retained. T44274 nestedrouter testlookup repair preserved STEWARDassertion.
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
- Authoredproductglue: T44250 8add/4remove12lines plus2importintegrationlines=14; allotherimplementation workers. Mechanical reviewedregionpatches for44330/44331 resolved staleimportcontexts, retained rootpagebytes; acceptedrootverifies0.
- Root44319 verifyquotingfailed, fixedshlex.quote/reaccept0; prematuremark removedbeforecommit. Worker44321/28/33 countmismatches normalizedrealstats. Root44334 -k reset selected0/exit5; isolatedtaskfiles restored/re-dispatchedonce with existinglifecycle/stop tests,17PASS; noassertionchanged.
- Root44331 dispatch briefly overlapped same relativetarget as44330 in separateclones; interruptedbeforeedits, resumedonlyafter44330accepted. Neverexceeded2workers. Allpackets/results/patches/acceptlogs inGit/.agent/results.

- Root44348 clone raced dependencyaccept: missinghelper TSexit2; isolatedtarget restored, acceptedreadonlydependency provisioned, repairpassed. Queue after dependencies accept.

- T44350 constmodule testharness lint defect blocked44348/51. W3T44353 bindingrename20b8d27 preserved allassertions; rootaccepts44348/51 subsequentlypassed.

- T44349 eagerfactory rootproposal failed react-hooks/refs; lazyevent-time repairpassed57f81b3. W1T44351 localRowtype boundary corrected to existingAPIimport beforeaccept.

- Recent accepts: T44361 5bba15e (CRUD router stage), T44362 cc361aa (polling), T44363 70bf3a3 (nested route traversal, unchanged422 assertion), T44365 68e26c9 (list refresh), T44364 a52fd5b (CRUD wiring). Root independently accept.sh0 for each.

- T44366 initial extraction introduced five exhaustive-deps warnings despite worker describing them as existing. Not accepted; repair1 requires stable setters/refs in deps and max-warnings0, no suppression.

- RootT44367 Verify mistakenly included DB-backed lease tests in worker scope; three active-owner failures, no accept. Corrected offline selection; root disposable full suite covers lease tests separately. No assertions changed.

- T-44366 accepted627d48a: Move live state/ref/error hooks verbatim with stable dependencies and zero lint warnings. Verify0.
