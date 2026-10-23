# CURRENT_STATE
updated_at: 2026-10-24
git_head: 030459a
branch: overhaul/neo-brutal
architect_sha256: db26d7463fae63c6defc3bfc3b4f503865d32a31eb1e97066e274a6875771f4e
harness: codex; orchestrator gpt-6.1-sol/medium; custom workers gpt-6-luna/high; cap2
archetype: Neo-Brutal Motorsport (light); ADR007 approved
last_eval_score: 51.2974358974359 baseline; F68/A53.333/P33.333/E46.154; failedF4; NOT_RUN P1/P2; notpresentable

## Phase and verified facts
- Phases0–2 complete; owner requests all12, unattended. Phase3 T330 complete, T331 extraction in progress. Phase5 T361 accepted1e61efd, T360 lints in progress; T362 waits for both per plan§4. No later-phase completion claimed.
- Phase1 acceptedT31035578c9/T3118570e58/T312e0f7adf/T3134089fb6/T314c0c8061. Root144PASS0skip/livePASS; browser1005PASS5projects. HostedCI NOT_RUN. Evidence/history in git/phase1.evidence.json.
- Phase2 parents T3204789586/T321caf033f/T322a12bc68/T3233146736/T32461643df/T3252bff831 accepted. JWTrevocation ADR008/migration004 onlydisposable; logoutreuse401/WS4401, CSRF/legacy/outage/expiry tests. ADR011 live/ready probes. Full184PASS0skip/livePASS twice. CSPbuild/lint/types0+85axePASS. Inlinebootstrap unsafe-inline compatibility retained; unsafe-eval devonly. T441458f721ae preserves exact3HTMLdocs routes,16testsPASS, APIs strict.
- T3303afff87 complete: snapshot9+union7+realGETgoldens14=30PASS; full214PASS0skip/livePASS. Fixture captures own SQLtransaction, rolls back0own users/sessions. Existing API snapshot permanent gate. No API/schema changes in current moves.
- T331 pure moves accepted: EventBus462ea55, JSON/parser47fc39d, errors882e5ed, validation049a179, models0adc5bb, livenessrouter4c4f401, domainhelpers64214d6. AST/alias proofs and snapshot9PASS each. Latest rootfull214PASS0skip/livePASS. Ruffall0; mypy217errors15/42files afterliveness, fullzeroT339.
- T44156 introduced1implicitexport error; repaircec7835 restored direct constant import/baseline217. No thresholds loosened. Some worker envelopes used placeholder Verify or inaccurate counts; root corrected format/counts and reranactualVerify beforeaccept, logged in childenvelopes.
- T361 accepted1e61efd from tokens7768158/rootinstall553ed00/config9335c83: Tailwind4.3.3 +@tailwindcss/postcss4.3.3, autoprefixer removed. Rootbuild/lint/types0,audit0vulnerabilities,925nonpalettebrowserchecksPASS5projects. npm-generatedlock1183changedlines separately from authored<=150workerpackets; ownerexplicitplaninstall, no handwritten product/lock lines.
- T360 lightgate4f53ecd activated>=0.85, AA4.5 unchanged,80cases collected. Actual dashboarddesktop1FAIL expected on currentdarkUI; never skipped. Radius4c707d9/maskera1eea31, gray10b17c4/wiringb1fec1c selftests0; good0/bad1 fixtures. All seven visual rule families wired; motion integration/mobile utility coverage and role-pixel gate pending. Legacy10hits retained.

## Execution contracts
- Only overhaul/neo-brutal, accept.sh commits, rerun every Verify, <=3files/150authoredchangedlines, atmost2 fresh packet-only customworkers in shared ignoredclones. No worker commits. Root integrates sequentially and updates state every acceptance. .agent/orchestrate.py persists clone/integrate/mark helpers.
- Never .env/secrets, recursive deletion, realDB/schema/volume writes. DBwork only disposable apexgrid-test(PG15432/Mongo27018), projectlabel checked. CI testguard additionally permits explicit ephemeral GitHubservices. Realbackend has no sourcebind/reload. Preserve owner status.sh paths/exclusions and run-loop.sh edits.
- Preserve every route/feature/copy/hook/aria/stateclass/hash, oneprimary/fivestates. API additions per ownADR; existing path/method/response changes needowner. Architecture lock unchanged andverified.

## Open risks / next checks
- Mypy217 pendingT339; oldgiantfiles/one-callsite complexity extractions need TasteA6 review. T44168 uses temporary typed registration wrapper solely for move; T332 replaces factory wiring/appglobals.
- P3bundlechecker misseslayout/sharedassets T44132; LighthouseCLIabsentP1/P2NOT_RUN; FPS17ms untilT41316.7. HostedCI NOT_RUN. CurrentdarkUI/lightpalette FAIL; baseline51.2974 is not a delivery score.
- Root initial palette check used wrongprojectdesktop, correcteddesktop-1440; both logs retained. ThreeoldCSSlints0; neo rules intentionally report legacy violations.

## Orchestrator direct edits
- Architecture/ADRs/docs/state/packets/envelopes/orchestration helpers and root-owned planned dependency installs only. Zero authored product lines; integrating worker patches is not product authorship. Canonical lock operation bypassed autoGit tail only to honor accept-only; independently verified.

## Recent acceptance / review
- Health/SQL pure moves through7c6c086 preserve AST/main aliases. Full214PASS0skip/livePASS through EXPLAIN; latest Mongo move full214PASS0skip/livePASS. Ruff0/mypy216errors17/44files after typed Collection boundary. Typed temporary factory helpers required by C901; T332 replaces them.
- T360 shadow66c4550/contrastd0e50ef/wiringb549015/motionc64e793 accepted with regression repairs. Shared neo actual10legacyCSSviolations; motion wrapper next. No thresholds weakened. Counts/static boundary not delivery proof.
- Root corrected FastAPI included-router probe, mypy namespace, and underestimated C901 (typed helper retained after observed11>10). Worker placeholder Verify formats normalized then exact command rerun.

- T-44181 accepted20466aa: Moved unchanged overview/telemetry handlers into typed Mongo factory with main aliases and late callbacks. Verify0.

- T-44182 accepted86e0b47: Integrated CSS motion validator, fixture selftest and explicit file mode while retaining original layout/shadow/all bans. Verify0.

- Motionwrapper86e0b47 selftest0; actual3legacytransition violations at globals146/294/1112, expected redesign gaps. Neo baseline10violations.

- T-44184 accepted008414f: Moved unchanged race-list endpoint into SQLrouter; mainalias and query ordering preserved. Verify0.

- Root read one101-line range accidentally (main1890–1990), no secrets exposed; subsequent source ranges capped80.

- T-44183 acceptedf385ea8: Extracted exact approved role-pixel scorer and boundary selftests; existing CLI now resolves installed Sharp offline and defaults to ADR007 roles. Verify0.

- T44185 worker reported25 added lines but actual27 (imports omitted); root corrected envelope counts before integration. No product/source outside task changed.

- T-44185 accepted030459a: Added actual1440 screenshot pixel-role gate using shared scorer and PNG/JSON evidence; preserved all80cases and prior luminance/AA assertions. Verify0.
