# CURRENT_STATE
updated_at: 2026-10-23
git_head: 882e5ed
branch: overhaul/neo-brutal
architect_sha256: db26d7463fae63c6defc3bfc3b4f503865d32a31eb1e97066e274a6875771f4e
harness: codex; orchestrator gpt-6.1-sol/medium; custom workers gpt-6-luna/high; cap2
archetype: Neo-Brutal Motorsport (light); ADR007 approved
last_eval_score: 51.2974358974359 baseline; F68/A53.333/P33.333/E46.154; failedF4; NOT_RUN P1/P2; notpresentable

## Phase and verified facts
- Phases0–2 complete under approvedADR007; ownerwantsall12phases. Phase3 T330 complete; T331 behavior-preserving extraction in progress. Phase5foundationmayinterleaveperplan§4.
- Phase1 T31035578c9/T3118570e58/T312e0f7adf/T3134089fb6/T314c0c8061 accepted. Full144PASS/livePASS; browser1005PASS(all5projects), rootbuild/lint/types0. HostedCI NOT_RUN. Exactchildhistoryin git andphase1.evidence.json.
- Phase2 T3204789586/T321caf033f/T322a12bc68/T3233146736/T32461643df/T3252bff831 acceptedwithboundedchildren. ADR008JWTrevocation/004onlydisposablestack, logoutreuse401/WS4401, legacycompat/CSRF/outage/malformed tests. ADR011healthprocess/readiness6casesPASS. AlloldOpenAPIpaths/schemasunchanged; only2approvedhealthpathsadded. No realstacksourcebindmount/reload.
- Phase2full184PASS0failed/skipped/xfail/livePASS twice inclT323accept. T324rootbuild/lint/types0+85axe/reducedmotionPASS, productionCSPsanitizedHTTPS/WSS/noeval. Bootstrapinlineunsafe-inline retainedcompatibility; evaldevonly. T441458f721ae preserves3legacyHTMLdocspathsfromAPI-onlyCSP; 16testsPASS, API/404strictretained.
- Phase3 T441465b0b7e4 snapshot+9tests, full193PASS/livePASS. T441476ae5e39 union/ref/enumguard+7regressions16PASS, full200PASS/livePASS. Rootreproduced4pre-fixFAIL2PASSagainstoldhelper; firstrootprobefilenameimportfailedthenfixed, logged. Generatedredlogexcludedfromcommittedchangeenvelope, preservedseparately.
- LatestRuffall0,55filesformatted, strictmypy217errors11/33files(T339). ThreeCSSlints0; neo radius scanner selftest0, legacy2hits; remainingT360rulespending. Pip audit0; npmhighaudit0 with3moderate. P3missinglayout/sharedassetsT44132; LighthouseabsentP1/P2NOT_RUN; FPS17msnot16.7untilT413. Currentdarkvisualdesignnotyetapprovedlightimplementation; nofinishedscoreclaim.
- T44148fixture141linesrootcaptured10realGETresponsestwiceidentically; transactionrollbackleft0ownusers/sessions. FirstcapturecaughtwrongMongoenv/ConnectionAPI; repairedonce, importsPyJWT/dynamicexpiry/clientclose. Goldencomparisonchildnext; noDBschema/handler/resultmock.

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


- T-44148 accepteda5535b2: Updated the disposable fixture to read MONGODB_URL, use PyJWT with a ten-minute token, insert users through the real connection, and close TestClient after capture. Verify exit0; 141 changed lines.

- T-44149 accepted62443d0: Added ten golden route cases and pure comparison checks for additive keys, removed fields, changed values, and type changes. Copied the provided snapshot byte-for-byte. Verify exit0; 55 changed lines.

- T44149rootreal14casesPASS (tenGETgoldens+4comparison); immutablefixturecopiedbyteidentically. Initialworkerclaimedmissingfiledespiteexisting2376bytefixture, absolute-pathretryresolved; no changesoutsidepacket. Rootfull214suite running. T44150radiuslintfoundationW3runninginparallelallowedPhase5interleave.

- T-330 accepted3afff87: Close OpenAPI and ten real GET golden contract guard from accepted W3 children. Thirty focused tests pass; full isolated suite has 214 passed, zero skips, with live acceptance passed. Verify exit0; 0 changed lines.

- T-44151 accepted462ea55: Moved EventBus verbatim into backend.app.core.events, added the main.EventBus import alias, and retained bus = EventBus() in its original location. Verify exit0; 82 changed lines.

- T-44150 accepted4c707d9: Updated the shared checker to preserve CSS URLs and detect quoted JS radius keys, including corner properties. Self-test covers both reported cases and comment line positions. Default scan reports the two existing globals.css hits at lines 116 and 985. Verify exit0; 94 changed lines.

- T3303afff87 accepted30contractchecks; full214PASS0skip/livePASS. T44151462ea55 EventBus exactAST/publicalias+11PASS/full214PASS0skip/livePASS. T441504c707d9 radius-onlylinter acceptedafter2repairs/sharedscanner/URL+quotedkeyprobes, selftest0; actuallegacy2radiusviolations remainbaseline, wholeT360notcomplete. T4415247fc39d serializers/protocol parser exactAST+12PASS/full214PASS0skip/livePASS; T44153a1eea31 typed masker selftest/Ruff/mypy0 accepted; no authoredorchestratorproductcode.

- T-44152 accepted47fc39d: Moved JSON/telemetry serializers and WebSocket bearer parser verbatim to core modules; retained main aliases. Verify exit0; 64 changed lines.

- T-44153 accepteda1eea31: Extracted typed comment masking helper; radius scanner policies and fixtures unchanged. Verify exit0; 62 changed lines.

- T-44154 accepted882e5ed: Moved four unchanged exception handlers and retained main aliases with all seven registrations. Envelope command normalized to packet literal before root rerun. Verify exit0; 69 changed lines.

- T44154 worker Verify field summarized instead of literal; root normalized envelope format, accepted only after actual command rerun0. No re-dispatch needed per failed-format rule. Full isolated rerun in progress. T44155 staged theme token file W1 running; not imported until Tailwind4 integration.
