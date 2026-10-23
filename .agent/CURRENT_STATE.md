# CURRENT_STATE
updated_at: 2026-10-23
git_head: b1fec1c
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


## Latest accepted work and active checks
- T3303afff87 complete: snapshot9+union7+realGETgoldens14=30PASS. Golden real fixture uses own transaction and rolls back0users/sessions. Full214PASS0skip/livePASS. Permanent snapshot gate on every backend change.
- T44151462ea55 EventBus; T4415247fc39d JSON/protocol; T44154882e5ed error handlers; T44156049a179 validators: exactAST/main alias checks0, snapshot9PASS each. Full214PASS0skip/livePASS throughT44154; T44156fullrunning.
- T44153a1eea31 typed comment masker accepted selftest/Ruff/mypy0; radius scanner T441504c707d9 selftest0, valid0/invalid1 and quotedkey/CSSURL probes1. Legacyglobals2radius hits remain; otherADR007lint rules pending.
- T441557768158 stagedtheme tokens63lines (not imported), typecheck/lint/old3lints0, tokenradius0. Taste: no DOM/rendering change. T441574f53ecd light luminance>=0.85 activated, AA4.5 preserved,80casescollected. Rootdesktopdashboard actually1FAIL as expected duringdarktransition; no skip. Root first used nonexistentprojectdesktop then correcteddesktop-1440, logged both.
- Rootmypy218 afterT44156: worker moved constant import indirectly through validation, causing new implicit-export error. T44158repair queued to restore direct simulation_core import/baseline217. No threshold changed; fullzero atT339.
- Worker reporting issues: T44154 summarized Verify instead of exactliteral, root normalized and reran; T44155 countedstaticcommands as tests, root corrected to0. No boundaries violated. Root authored0productlines.

- T-44158 acceptedcec7835: Restored direct MAX_SESSION_LAPS import; new implicit-export error removed, mypy returns to baseline217. Verify0.

- T44158cec7835 repaired import-only ratchet: mypy217 in15/39files, snapshot9PASS. T44156 full214PASS0skip/livePASS. T44158root fullrunning.
- T361 dependency installation is orchestrator-owned per explicit plan: Tailwind4/@tailwindcss/postcss replace Tailwind3/autoprefixer. npm-generated package-lock changes recorded separately from <=150-line authored worker packets; no hand-authored lockfile or product code. The UI integration remains a separate W1 packet.

- T-44160 accepted553ed00: Installed planned Tailwind4.3.3/PostCSS adapter; removed autoprefixer. npm-generated lock updated; root audit0 vulnerabilities. W1 config/import integration pending. Verify0.

- T-44161 accepted0adc5bb: Moved health and reservation models unchanged, preserving main aliases and OpenAPI contracts. Verify0.

- T-44159 accepted10b17c4: Added shared neutral color/gray-family rule and good/bad fixtures with29self-test assertions; scanner wiring next. Verify0.

- T-44162 accepted9335c83: Integrated installed Tailwind4 adapter/token import and removed obsolete config; all legacy CSS rules preserved. Offline build/lint/types0. Verify0.

- T-44163 acceptedb1fec1c: Wired gray/neutral checks into shared scanner and selftest, added inline JS style positive/negative controls.32gray assertions plus radius controls pass. Verify0.
