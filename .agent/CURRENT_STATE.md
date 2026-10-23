# CURRENT_STATE
updated_at: 2026-10-23
git_head: 61643df
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

- Phase1 fresh dimension artifactsT44123..26 accepted; historical commit detail in git. ADR011T44130/lockdb26; only2newhealthpaths acceptedT44129a3c0554 with6PASS and exactexistingOpenAPI preservation. T44136 fixed missingleaseexpecteddown testbug beforeacceptance.
- Phase2 T44133/T44134 redtests accepted; T321CORS3PASS; T44135repo5red thenT44137repository/migration37lines5PASS/mypy0. T322all12header/CORS/healthPASS,mypy0. Migration004notyetapplied. No authoredorchestratorproductlines.

- T-44139 accepted5e9584b: Added per-test in-memory token revocation stubs for auth characterization tests and stubbed expired-revocation cleanup in the login-throttle client. Verify exit0; 9 changed lines.

- T-44138 accepted12edd4e: Wired revocation checks into HTTP authentication and WebSocket handshakes; stored validated claims for logout; added logout revocation and login cleanup with PostgreSQL 503 handling. Verify exit0; 61 changed lines.

- T44138 wiredrevocation accepted12edd4e23PASS; isolated004bootstrap0; fullbackendrunning. Freshmypy220 vs218 exposes2newannotations, T44142 fixesratchet beforephaseclose. T324clonebuild/lint/types0; rootacceptance+browserpending.

- T-44140 accepted3bb47c9: Added offline tests for malformed jti values, revocation lookup and revoke outages, and login cleanup success and failure. Confirmed legacy and browser login behavior. Verify exit0; 112 changed lines.

- T324 rootVerify wraps samebuild/lint/types torestoreonly Nextgeneratedtype-reference bytes finally, preventingbuildboundarynoise. Workerreported3tests actually3commands; accepted envelope records0tests, browsergate rootseparate.

- T-324 accepted61643df: Added CSP and security response headers. API and WebSocket origins derive from the sanitized API URL; unsafe-eval is limited to development. Verify exit0; 53 changed lines.
