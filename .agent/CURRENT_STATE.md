# CURRENT_STATE
updated_at: 2026-10-24
git_head: b886991
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
- T360 lightgate4f53ecd activated>=0.85, AA4.5 unchanged,80cases collected. Actual dashboarddesktop1FAIL expected on currentdarkUI; never skipped. Radius4c707d9/maskera1eea31, gray10b17c4/wiringb1fec1c selftests0; good0/bad1 fixtures. Blur b395e35 accepted17cases after repair1 for root-proven bareutility/commafilter bypasses; not wired yet. Gradient/weight wiring accepted. Legacyradius2hits remain; otherstyle rules/motionplinth/palette roles pending.

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
- Health wrappers4e8f466/31a3bd4 and SQLrouter4b411cc/1356d28 preserve exact handler AST/main aliases. Full214PASS0skip/livePASS after each; Ruff0; mypy217errors16/43files. Temporary callback factories are T332 dependency-injection debt.
- Gradient6c04161/weight20e9e21/wiring7b1c487 accepted after regression repairs: selftests24/31; shared scanner/mypy0; actual seven legacy violations remain, covered by visual phases.
- Root fixed two Verify assumptions without weakening assertions: FastAPI included-router identity traversal; multi-module mypy --explicit-package-bases.
- T44173 repair2 and T44175 repair1 returned PASSED in isolated clones; root review/acceptance pending. Repairs cover CSS important/case and shadow aliases/RGB; contrast offset/order/conditional classes. T44176 EER move ready.

- T-44176 accepted9d8cae0: Moved unchanged EER metadata handler into SQL router with main alias; exact AST and endpoint identity plus9 snapshot tests pass. Verify0.

- T-44173 accepted66c4550: Added hard-shadow validator with28 regression controls including canonical aliases, RGB, CSS case and important handling. Verify0.

- T-44175 acceptedd0e50ef: Added white-on-red checker with24 controls, character offsets, declaration precedence and conditional JSX literals. Verify0.

- T-44177 acceptedb549015: Integrated shadow/contrast into shared scanner and selftests; good fixtures0 and bad fixtures1. Verify0.

- T-44178 acceptedb886991: Moved unchanged EXPLAIN handler into SQL router with precise Connection callback and preserved alias. Verify0.

- T44180 rejected beforeaccept: unnecessary untyped registration helper hid connection types; repair1 requests direct typed factory nesting and exact Verify envelope. Isolated clone only. Rootfull214PASS0skip/livePASS after EXPLAIN, mypy217/Ruff0.

- T44179 motion candidate rejected: seconds/important false positives, unknown timing/10s delay and no-preference bypass. Repair1 adds exact probes; patch stays isolated.

- T44180repair1 Verify failed C90111>10, contradicting root estimate. Repair2 allows fully typed helper as temporary complexity boundary with precise Connection callback; no gate relaxed.
