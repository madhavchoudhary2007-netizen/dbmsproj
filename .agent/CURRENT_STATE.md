# CURRENT_STATE
updated_at: 2026-10-24
git_head: 14da91f
branch: overhaul/neo-brutal
architect_sha256: 3c4ab0a82eb81bc885d5b4a6baf4f64728a6cb87181b515f7cbffcb77c3701ae
harness: codex; orchestrator gpt-6.1-sol/medium; workers gpt-5.6-luna/high (latest owner override), cap2
archetype: Neo-Brutal Motorsport (light), ADR007 approved
last_eval_score: obsolete baseline51.2974358974359; no current score; final evaluation T430

## Verified milestones
- Phases0–2 and5 COMPLETE (4 of12). Phase3 T331 extraction remains; main1642 lines, target<=120. Phase4 and6–11 unfinished. Owner requests autonomous completion of all12, no routine questions.
- Phase5 T3602ad337f/T3611e61efd/T362c0781f9/T36313f614a/T364d666cf6/T365b90911f/T366b18819f accepted through accept.sh. Tailwind4.3.3, SpaceGrotesk500/700 + SpaceMono400/700, scoped tokens/textures/plinth and complete shared primitives. Existing production routes adopt them in Phases6–7.
- Root60 browser cases PASS across320/375/768/1440/5120 (T366.matrix.browser.raw.log). Parent accept reruns: motion30 PASS, primitive30 PASS, axe375/1440 2 PASS; keyboard/font4 per runner. Build/lint/types0 and four CSS lints0. /__nb dev200, production not-found visible + noindex + guide absent + zero writes. Next streamed notFound HTTP200 is documented behavior; do not substitute status-only checks (.agent/check-guide-production.py).
- Phase5 fixes: escaped %5F_nb route6b9c6f7, explicit44px controlsfdb63e2, FLIP mount/scroll guarde6efcc1. Browser tests wait fonts/finite animations for axe without relaxing thresholds; reduced motion asserts immediately.
- Backend latest root full231 PASS,0 failed/skipped, live acceptance PASS after results router wiring3e902c2 (T44256.full.raw.log). Earlier archive/lap wiring also227 PASS. API snapshot9 + runtime uniqueness2 are permanent; required-input regressions27 and seeded GET goldens14 retained. No API/schema changes in current moves.
- T331 extracted core tick46129c0, stewards89c82af, DBMS SQL/Mongo/archive2e5c5a4 and lapsef0dee3; lock helpers225b2b8 wiredc2616e0. api/dbms_lock.py stagedc6787b1 and wireddb3cf1b; originals removed. Exact lock body retained as module-level _run_lock_demo with explicit typed dependencies, thin public wrapper; no suppression/locals/classes. Factories/globals are transitional T332 debt.
- Preserve legacy main aliases and late-bound callbacks: Decision removal caused7 failures fixed5ee4710. OpenAPI alone cannot prove Python alias/runtime uniqueness compatibility.

## Next work
- Feed hookc1ecce3, mapper939fea6, presentersdfcf8ac and roote765662 glue integrated. Mapper3 offline tests39f2e59/2aa2b87 pass. T44251 root25 browser cases PASS across five projects (feed+drawer, T44251.browser.raw.log). Existing route/accessibility/targets/primary/edge gates running; Phase6 not complete.
- Backend lock endpoints wireddb3cf1b: root227 PASS0skip/live PASS (T44233.full.raw.log). Shell CSS ac0a46e/683c6b5 activated5627293. Cache63aa0ad and four offline regression casescdd2dec accepted; drawer hookfeeaef3 wired; actual10 browser drawer cases PASS across five projects (T44244.browser.raw.log). Remaining Phase6 existing route/responsive/a11y/touch/hash/auth gates. Missing next_event covered by ADR012/c93ec77 and focused relock; T44241 red tests60e5e56 and implementation246f2f6 accepted. Initial full230 PASS/1FAIL fixed by fixture-generator correction35b904f without assertion changes; rerun231 PASS0skip/live PASS. No fabricated event. Remaining graph docs/overhaul-plan.md.
- Four CSS lint gates0; production routes still legacy dark, light palette FAIL expected until Phase7, never skip/widen it. Last existing-route axe85 and non-palette925 before new shell. Phase5 guide60 now green; do not imply real-route redesign complete.

## Safety / workflow
- Only overhaul/neo-brutal; commits only accept.sh; max2 custom-role workers, fresh packet-only clones, no per-call overrides. Profiles/models.env2bc94fb bind5.6/high after owner request; successful workers and tool role metadata confirm availability. No quota blocker.
- <=3 target files and150 changed lines/task, exact worker Verify independently rerun. Workers offline/no fixed ports; root owns browser/network/disposable checks. Integrate one patch then accept before another. Never accept concurrently with another Next build/dev check; helpers restore next-env and kill only their own temporary loopback servers.
- Never .env/secrets, recursive deletion, real database/schema/volumes. Only disposable apexgrid-test (PG15432/Mongo27018), project labels guarded, one db-baseline runner at a time on18000. Real backend has no source bind/reload. Owner status.sh and scripts/agent/status.sh excluded and untouched; preserve run-loop.sh owner edits.
- .agent/orchestrate.py persists queue/clone/integrate/mark. Worker envelopes require actual stats/integer static counts0, no extra keys. All features/routes/copy/hooks/aria/stateclasses/dbms hashes retained; five states/44px/token spacing/reduced motion mandatory.

## Open risks
- T370 broad browser batch:260 PASS/80FAIL.75 axe cases fail mixed legacy dark/light contrast plus status visible-label/name mismatch;5 E5 failures are ambiguous substring Refresh selector. W1 T44257/W3 T44258 repaired label/Refresh/mostcontrast. Rerun110 PASS20FAIL, narrowed to4 legacy text selectors; T44260 accepted fix, fullaxe/feed/edge/drawer rerun in progress. No API/copy/threshold changes.
- T44248 first acceptance caught reserved module variable in new mapper test; W3 renamed binding2aa2b87, all3 assertions+global lint pass. Saved W1/root patches reapplied, acceptdfcf8ac/e765662 both0; no assertion weakened.
- T331 giant main/transitional factories; strict mypy212 errors/24files (T44256.mypy.raw.log); zero required T339. No thresholds relaxed.
- T44132 bundle checker omits layout/shared assets; fix before P3. Lighthouse absent, FPS gate17ms until T41316.7, hosted CI unverified. Final score>=95/all hard gates/no NOT_RUN required; never present obsolete score as current.
- Worker review caught nested main/dead modal control (corrected), accidental root demo hook (removed only worker-owned unaccepted copy), and T44232 complexity suppression/locals namespace tricks (rejected, standard explicit helper accepted). No other work reverted; no test weakened.

## Orchestrator direct edits
- T-44250: 8 additions/4 removals in shell.tsx as cross-worker glue connecting accepted W1 presenters and W2 hook/mapper; no bulk implementation. Metadata, architecture/config/ADRs, packets/state/envelopes/root acceptance helpers and approved installs only. Applying worker patches is integration, not authorship. No new dependencies this continuation.

- T-44259 accepted905b786: Stage typed result-write router with explicit helper dependencies and AST-identical implementation; no main wiring yet. Verify0.

- T-44260 accepted14da91f: Correct four remaining measured light-shell contrast selectors using approved ink/yellow surfaces and token spacing. Verify0.
