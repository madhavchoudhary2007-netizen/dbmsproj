# CURRENT_STATE
updated_at: 2026-10-24
git_head: 5ee4710
branch: overhaul/neo-brutal
architect_sha256: db26d7463fae63c6defc3bfc3b4f503865d32a31eb1e97066e274a6875771f4e
harness: codex; orchestrator gpt-6.1-sol/medium; workers gpt-5.6-luna/high (owner override); cap2
archetype: Neo-Brutal Motorsport (light); ADR007 approved
last_eval_score: 51.2974358974359 baseline; F68/A53.333/P33.333/E46.154; failedF4; NOT_RUN P1/P2; notpresentable

## Phase and verified facts
- Phases0–2 complete; owner requests all12, unattended. Phase3 T330 complete, T331 extraction in progress. Phase5 T361 accepted1e61efd, T360 accepted2ad337f; T362 acceptedc0781f9; T363 CSS foundation verified, T364/T365 primitives in progress. No later-phase completion claimed.
- Phase1 acceptedT31035578c9/T3118570e58/T312e0f7adf/T3134089fb6/T314c0c8061. Root144PASS0skip/livePASS; browser1005PASS5projects. HostedCI NOT_RUN. Evidence/history in git/phase1.evidence.json.
- Phase2 parents T3204789586/T321caf033f/T322a12bc68/T3233146736/T32461643df/T3252bff831 accepted. JWTrevocation ADR008/migration004 onlydisposable; logoutreuse401/WS4401, CSRF/legacy/outage/expiry tests. ADR011 live/ready probes. Full184PASS0skip/livePASS twice. CSPbuild/lint/types0+85axePASS. Inlinebootstrap unsafe-inline compatibility retained; unsafe-eval devonly. T441458f721ae preserves exact3HTMLdocs routes,16testsPASS, APIs strict.
- T3303afff87 complete: snapshot9+union7+realGETgoldens14=30PASS; full214PASS0skip/livePASS. Fixture captures own SQLtransaction, rolls back0own users/sessions. Existing API snapshot permanent gate. No API/schema changes in current moves.
- T331 pure moves accepted: EventBus462ea55, JSON/parser47fc39d, errors882e5ed, validation049a179, models0adc5bb, livenessrouter4c4f401, domainhelpers64214d6. AST/alias proofs and snapshot9PASS each. Latest rootfull227PASS0skip/livePASS. Ruffall0; latest mypy212errors18/45files; fullzeroT339.
- T361 accepted1e61efd from tokens7768158/rootinstall553ed00/config9335c83: Tailwind4.3.3 +@tailwindcss/postcss4.3.3, autoprefixer removed. Rootbuild/lint/types0,audit0vulnerabilities,925nonpalettebrowserchecksPASS5projects. npm-generatedlock1183changedlines separately from authored<=150workerpackets; ownerexplicitplaninstall, no handwritten product/lock lines.
- T360 lightgate4f53ecd activated>=0.85, AA4.5 unchanged,80cases collected. Actual dashboarddesktop1FAIL expected on currentdarkUI; never skipped. Radius4c707d9/maskera1eea31, gray10b17c4/wiringb1fec1c selftests0; good0/bad1 fixtures. All seven visual families and motion wired; actual1440 role gate030459a added using scorerf385ea8. Shadow utility fix3c10f63 accepted; allfourglobalCSSlints0 afterT44195.

## Execution contracts
- Only overhaul/neo-brutal, accept.sh commits, rerun every Verify, <=3files/150authoredchangedlines, atmost2 fresh packet-only customworkers in shared ignoredclones. No worker commits. Root integrates sequentially and updates state every acceptance. .agent/orchestrate.py persists clone/integrate/mark helpers.
- Never .env/secrets, recursive deletion, realDB/schema/volume writes. DBwork only disposable apexgrid-test(PG15432/Mongo27018), projectlabel checked. CI testguard additionally permits explicit ephemeral GitHubservices. Realbackend has no sourcebind/reload. Preserve owner status.sh paths/exclusions and run-loop.sh edits.
- Preserve every route/feature/copy/hook/aria/stateclass/hash, oneprimary/fivestates. API additions per ownADR; existing path/method/response changes needowner. Architecture lock unchanged andverified.

## Open risks / next checks
- Mypy212 pendingT339; oldgiantfiles/one-callsite complexity extractions need TasteA6 review. T44168 uses temporary typed registration wrapper solely for move; T332 replaces factory wiring/appglobals.
- P3bundlechecker misseslayout/sharedassets T44132; LighthouseCLIabsentP1/P2NOT_RUN; FPS17ms untilT41316.7. HostedCI NOT_RUN. CurrentdarkUI/lightpalette FAIL; baseline51.2974 is not a delivery score.
- Root initial palette check used wrongprojectdesktop, correcteddesktop-1440; both logs retained. Allfour globalCSSlints0 afterT44195; pixel palette remains FAIL untilPh7.

## Orchestrator direct edits
- Architecture/ADRs/docs/state/packets/envelopes/orchestration helpers and root-owned planned dependency installs only. Zero authored product lines; integrating worker patches is not product authorship. Canonical lock operation bypassed autoGit tail only to honor accept-only; independently verified.

## Recent acceptance / next
- Ownerworker overrideGPT5.6Luna/high: profile2bc94fb, toolbinding5.6/high andcompletedfreshresultsconfirmavailability. Noquota blocker; cap2/orchestratorunchanged. T44203 button/card6eefdaa andT44204 badges e4a3f6c acceptedoffline; runtimeT366 pending. Badges repairedgenericnamedspan toroleimg.
- T44205 incidentcreate65bd176 exactAST/snapshot/runtime11+rootlateconnection sentinel0; full227PASS0skip/livePASS. T44209 decisionreadyreviewed exactAST; temporarytypedregistration helper avoidsC901increase, T332 replaces it. Currentmypy212errors18/45files, no relaxedgate.
- T44208 formcandidate reviewFAIL1: redbodytext onwhite contrast~2.8; own2newfilesreset, rawpatch referenced; repair1ink/red-errorblock required. Noaccepteddefect or weakenedtest. Rootauthor0productlines.
- SharedhooksT364 accepted47c0408 inclcancelcleanup, runtimeT366 pending. T36313f614a complete: fourCSSlints0/rootproductionbuild0/85axe+4keyboardPASS after2colorcontrastfix. Currentdarkpalette remainsFAIL untilPh7; no fullcompletion claim.

- T-44209 accepted89c82af: Moved exact incident decision and preserved alias/late callbacks; typed registration helper retains C901 gate,11 contract/runtime checks pass. Verify0.

- T-44208 accepted72a5b82: Added typed ref-forwarded native controls and field label/error linkage; repaired error text to ink on red for AA contrast. Verify0.

- RootfullT44209 nowRED7FAIL220PASS0skip: main.Decision missingexport (T44209removedimport). T44214 P0 restores explicitDecision/IncidentIn aliases; focused7regressioncases addedtoVerify. No testchanges; parentT331 stillunfinished. T44210 UIreviewrepair1 genericparagraphnaming andactualmarqueeentry, candidatepreserved.

- T-44214 accepted5ee4710: Restored explicit Decision/IncidentIn legacy exports after7full-suite failures; all18focused contract/regression cases pass unchanged. Verify0.
