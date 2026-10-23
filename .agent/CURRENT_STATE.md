# CURRENT_STATE
updated_at: 2026-10-23
git_head: a3c0554
branch: overhaul/neo-brutal
architect_sha256: db26d7463fae63c6defc3bfc3b4f503865d32a31eb1e97066e274a6875771f4e
harness: codex; orchestrator gpt-6.1-sol/medium; custom workers gpt-6-luna/high; cap2
archetype: Neo-Brutal Motorsport (light); ADR007 approved
last_eval_score: 51.2974358974359 baseline; F68/A53.333/P33.333/E46.154; failedF4; NOT_RUN P1/P2; notpresentable

## Phase and verified facts
- Phase0 completeT300e465e89/T30113e6100/T30259a180e. ADR007 activated after owner approval; lock9010959b verifies, boot0. Work through all12phases per owner's latest instruction.
- Phase1 T31035578c9/T3118570e58 accepted: WHOLEapp/testsRuff0 and43filesformatted; no remainingC901. T312e0f7adf selected3filesmypy0; freshglobal227 ->218 belowplan222. T3134089fb6 CIvalidator0; hostedCI NOT_RUN. T314c0c8061 scorer accepted;8regressionsPASS, F7/F8/F9+hardF2, missing/duplicate/unknown/reweighted/null evidence blocks delivery. All four freshdimension artifacts acceptedT44123..26; score51.2974 exit1honestbaseline, notdeliverable. Phase1complete; Phase2testsnext.
- Phase1 fullisolated144passed0failed/skipped/xfail and liveacceptanceallflowsPASS; browser1005PASS/all5projects after2originmockfixesT44128ad19d48. Typecheck/lint/build/Ruff44formatted/audit-high0; npm3moderate. Strictmypy218errors11/31files remainsT339. APIbaseline60d831ab5cc96051d2fa2caa9b4a2f25d89a6444c05c2a5ceed0aaf8c660346b capturedphase2.openapi-before.raw.json. CIvalidator0,hostedNOT_RUN.
- Phase1 accepted child details live in git and phase1.evidence.json. Score51.2974 is baselineonly; F4realbrowserjourney, F8typing,A3/A5/A6lightdesign/bloat,P1/P2Lighthouse,P3assetgraph,P5FPS,E1/E2coverage stillgaps. No pass claim for incompletechecks.

## Execution contracts
- Only overhaul/neo-brutal; no merge/force/historyrewrite. Only accept.sh commits; rerun every Verify. <=3files/150changedlines perpacket. Atmost2 packet-only customworkers in ignoredsharedclones .agent/workspaces, dependency symlinks; workers nevercommit. Integrate sequentially, updatestate everyaccept.
- Preserve routes/features/copy/hooks/aria/stateclasses/hashroutes, exactlyoneprimary/fiveUIstates. APIchanges additive/perownADR; no existingpath/method/response changes without ownerapproval. Lockedarchitecture governs.
- Never .env/secrets/recursiveremoval/realDB/schema/volumewrites. DBtests only disposableapexgrid-test(postgres15432/Mongo27018). Preserve ownerstatus.sh paths/exclusions and run-loop.sh edits.
- .agent/check-format-progress.py proves partialformat AST+canonical equivalence and strictdistance reduction. Parent zero gates never weakened. Rootlockscript autoGit tail bypassed only to honoraccept-only; canonical lock independentlyverified.

## Open risks / task notes
- T325 test-only W3 despiteplanW2 label. Oversizedplanrows split into boundedtasks. Domainstart/reset/finalize functions are cohesivecomplexity extractions; their singlecallsite status needs explicitA6 review at scoring/T331, do not conceal it.
- Rejectedcapoverruns repaired in clones; T44111 envelopecounts corrected actual35/27 beforeaccept. T44114 unnecessarydriverhelper removed onreview. No rule/threshold weakening.

## Orchestrator direct edits
- Requested modelprofilelines; architecture/ADR/docs/state/packets/envelopes/orchestrationhelpers only. T440 docs15lines. No authored productcode; integrating workerpatches is not bulkcode authorship.

- T44128ad19d48 fixes2hardcoded API mock origins withoutassertionchanges. Initialbrowser980PASS/25mock-originfail, focusedrepair25PASS, fullrerun1005PASS(3.1m) across5projects. Productionrebuild0; own generatednext-env diff restored.
- ADR00834dbb99 accepted forplannedT323: keep existingopaquejti/CSRF, maptoUUIDrevocationkey, additive004onlydisposablestack, no-jticompatibility. Currentlockc05eeb0c. Realbackendcontainer hasno sourcebindmount, so editingrepo cannotautoreloaditsdatabase.
- P3legacytoolreturns0butcountsroot+pageonly; shared/layoutassets omitted, do notclaimbudgetuntilT44132fix. LighthouseCLIabsent(P1/P2NOT_RUN). FPS17ms checkdoesnotprove16.7msuntilT413.
- Ownacceptanceboundaryerrors fromgeneratednext-env andprematureparallelpatch application were reconciled by restoringonlyowngenerateddiff/deferringsecondpatch; workeroutputsinscope.

- T-44123 acceptedfd18bfd: Recorded fresh functional evidence for F-1 through F-9 with the required IDs and weights; retained the F-4 and F-8 failures and disclosed npm moderate vulnerabilities. Verify exit0; 58 changed lines.

- T-44124 accepted1d5cb48: Recorded fresh aesthetic evidence for A-1 through A-7 with exact rubric weights; preserved A-5 and A-6 judgments. Verify exit0; 46 changed lines.

- T-44125 accepted4eed78c: Recorded all six performance checks with their specified weights and evidence-based results; artifact is 40 lines. Verify exit0; 40 changed lines.

- T-44126 acceptedc2eb8d2: Recorded fresh edge-check evidence from the current E2E specs and full rerun; E-1 and E-2 remain false because coverage is incomplete. Verify exit0; 34 changed lines.

- T-44130 acceptedce4b44b: Recorded additive health ADR011 and early health dependency slice with focused architecture review and lock. Verify exit0; 37 changed lines.

- T44134 firstresultFAILED because orchestrator-created redrecorder was not yet committed into clone. Product/testdiffinscope; infrastructure-only failure. Root linked read-only helper into bothsecuritytestclones, willrerun exactverify ratherthan re-dispatch (packets failed-result rule).

- T-44133 accepted091e4de: Added failing-first tests for CORS defaults and wildcard rejection, security headers and HSTS, and liveness/readiness probes. The red recorder confirmed 11 expected failures, 1 pass, 0 errors, and 0 skips. Verify exit0; 148 changed lines.

- T-44134 accepted749f9c5: Added the workspace root to sys.path inside the fixture before importing the app. The recorder captured the expected offline red baseline: 2 passed, 4 failed, 0 errors, 0 skipped. Verify exit0; 123 changed lines.

- T-321 acceptedcaf033f: Default CORS allow-list now includes localhost and loopback origins. Config import raises a clear CORS_ORIGINS error if the allow-list contains '*'. Verify exit0; 6 changed lines.

- T44134 requiredoneimportpathrepairafterrecorderexposedcollectionerror; corrected123lines,2PASS4expectedFAIL0errors/skips. T44133red12collected1PASS11expectedFAIL; T321CORS3PASS/ruff/format0. T44129healthimplementationrunning; T44135repo unittestredqueued.

- T44129FAILED5PASS1testexpectationbug: missing_lease503 expectedallservicesup contraryADR011down. Productdiff36linesheldinclone; W3T44136correctsexpectation(noassertionweakening) beforehealthreverify.

- T-44136 accepted31e5494: Mapped missing_lease to runtime_lease=down in the expected readiness services; retained all cases and assertions. Verify exit0; 2 changed lines.

- T-44129 accepteda3c0554: Added typed liveness and readiness endpoints, with an exact-path lease middleware bypass. Readiness reuses health() and reports missing or invalid leases as down; liveness returns no-store. Verify exit0; 36 changed lines.
