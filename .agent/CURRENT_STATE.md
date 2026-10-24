# CURRENT_STATE
updated_at: 2026-10-24
git_head: db3cf1b
branch: overhaul/neo-brutal
architect_sha256: db26d7463fae63c6defc3bfc3b4f503865d32a31eb1e97066e274a6875771f4e
harness: codex; orchestrator gpt-6.1-sol/medium; workers gpt-5.6-luna/high (latest owner override), cap2
archetype: Neo-Brutal Motorsport (light), ADR007 approved
last_eval_score: obsolete baseline51.2974358974359; no current score; final evaluation T430

## Verified milestones
- Phases0–2 and5 COMPLETE (4 of12). Phase3 T331 extraction remains; main1746 lines, target<=120. Phase4 and6–11 unfinished. Owner requests autonomous completion of all12, no routine questions.
- Phase5 T3602ad337f/T3611e61efd/T362c0781f9/T36313f614a/T364d666cf6/T365b90911f/T366b18819f accepted through accept.sh. Tailwind4.3.3, SpaceGrotesk500/700 + SpaceMono400/700, scoped tokens/textures/plinth and complete shared primitives. Existing production routes adopt them in Phases6–7.
- Root60 browser cases PASS across320/375/768/1440/5120 (T366.matrix.browser.raw.log). Parent accept reruns: motion30 PASS, primitive30 PASS, axe375/1440 2 PASS; keyboard/font4 per runner. Build/lint/types0 and four CSS lints0. /__nb dev200, production not-found visible + noindex + guide absent + zero writes. Next streamed notFound HTTP200 is documented behavior; do not substitute status-only checks (.agent/check-guide-production.py).
- Corrected missing route: Next app/__nb is private; escaped app/%5F_nb restores /__nb (6b9c6f7). Browser found43.5px controls fixed with explicit44px dimensions fdb63e2. FLIP incorrectly animated mount/scroll; container-relative/key-order guard e6efcc1 passes actual mounted tests. Finite-animation/fonts readiness before axe preserves thresholds; reduced-motion still zero immediately.
- Backend last root full227 PASS,0 failed/skipped, live acceptance PASS after lock-helper wiringc2616e0 (T44229.full.raw.log). Earlier archive/lap wiring also227 PASS. API snapshot9 + runtime uniqueness2 are permanent; required-input regressions27 and seeded GET goldens14 retained. No API/schema changes in current moves.
- T331 extracted core tick46129c0, stewards89c82af, DBMS SQL/Mongo/archive2e5c5a4 and lapsef0dee3; lock helpers225b2b8 wiredc2616e0. New api/dbms_lock.py stagedc6787b1, next wire/remove originals. Exact lock body retained as module-level _run_lock_demo with explicit typed dependencies, thin public wrapper; no suppression/locals/classes. Factories/globals are transitional T332 debt.
- Legacy Decision import removal caused7 failures;5ee4710 restored explicit main.Decision/IncidentIn exports, full227 green. Preserve all legacy main aliases and late-bound callbacks in further moves. OpenAPI alone does not prove route uniqueness or Python aliases.

## Next work
- No workers currently running. Queue T44233 W2 wire staged lock endpoints and T44234 W1 shell CSS foundation (T370), disjoint clones. Then shell markup/data hook T371, with root existing route/responsive/a11y/touch/hash/auth checks. Remaining task graph is docs/overhaul-plan.md.
- Four CSS lint gates0; production routes still legacy dark, light palette FAIL expected until Phase7, never skip/widen it. Last existing-route axe85 and non-palette925 before new shell. Phase5 guide60 now green; do not imply real-route redesign complete.

## Safety / workflow
- Only overhaul/neo-brutal; commits only accept.sh; max2 custom-role workers, fresh packet-only clones, no per-call overrides. Profiles/models.env2bc94fb bind5.6/high after owner request; successful workers and tool role metadata confirm availability. No quota blocker.
- <=3 target files and150 changed lines/task, exact worker Verify independently rerun. Workers offline/no fixed ports; root owns browser/network/disposable checks. Integrate one patch then accept before another. Never accept concurrently with another Next build/dev check; helpers restore next-env and kill only their own temporary loopback servers.
- Never .env/secrets, recursive deletion, real database/schema/volumes. Only disposable apexgrid-test (PG15432/Mongo27018), project labels guarded, one db-baseline runner at a time on18000. Real backend has no source bind/reload. Owner status.sh and scripts/agent/status.sh excluded and untouched; preserve run-loop.sh owner edits.
- .agent/orchestrate.py persists queue/clone/integrate/mark. Worker envelopes require actual stats/integer static counts0, no extra keys. All features/routes/copy/hooks/aria/stateclasses/dbms hashes retained; five states/44px/token spacing/reduced motion mandatory.

## Open risks
- T331 giant main/transitional factories; strict mypy last snapshot211 errors before latest moves, current count not rerun; zero required T339. No thresholds relaxed.
- T44132 bundle checker omits layout/shared assets; fix before P3. Lighthouse absent, FPS gate17ms until T41316.7, hosted CI unverified. Final score>=95/all hard gates/no NOT_RUN required; never present obsolete score as current.
- Worker review caught nested main/dead modal control (corrected), accidental root demo hook (removed only worker-owned unaccepted copy), and T44232 complexity suppression/locals namespace tricks (rejected, standard explicit helper accepted). No other work reverted; no test weakened.

## Orchestrator direct edits
- Zero authored product lines. Metadata, architecture/config/ADRs, packets/state/envelopes/root acceptance helpers and approved installs only. Applying worker patches is integration, not authorship. No new dependencies this continuation.

- T-44233 accepteddb3cf1b: Wired lock/recalculate router with preserved aliases, late-bound callbacks, existing guard/auth and explicit legacy runtime reexports. Verify0.
