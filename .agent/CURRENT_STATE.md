# CURRENT_STATE
updated_at: 2026-10-23
git_head: 87025ef
branch: overhaul/neo-brutal
architect_sha256: 9010959b1dacd9fc6b7d9af9afb9ee57fcd7a4753ea9557e397c90ca6982e1a0
harness: codex
archetype: Neo-Brutal Motorsport (light), ADR-007 approved
last_eval_score: historical 100 claim is not a verified baseline for this overhaul

## Active work
- Owner approved ADR-007 in chat: "ok approved continue", then "dont stop you have all permissions". T-302 approval is satisfied; proceed through the approved plan. Scoped ADRs, tests, no destructive/production changes and unchanged thresholds still apply.
- T-300 accepted e465e89: boot exit0/boot OK; branch based on perfection-loop1acf8e1. T-301 accepted13e6100 via accept.sh: ADR-007 draft amends A.4/A.5/B.5; five-lens pass2 yielded zero new amendments; relock/verify exit0. Phase0 paused at T-302 pending owner approved.
- H=codex; models.env defaults HARNESS via caller and uses gpt-6.1-sol/medium for Codex orchestrator. Worker models/efforts/cap and context windows preserved. Claude 433000 context settings were owner-supplied edits and are preserved.
- T-300 accepted by accept.sh, commit e465e89. Owner-supplied docs/overhaul-plan.md and .claude/settings.json were recorded unchanged; both were explicitly listed because accept.sh stages all changes.
- T-302 accepted59a180e; ADR activation locked9010959b. T-442 accepted7bdbf4c; bootstrap/operation+telemetry schemas Ruff and format exit0; 23 changed product lines. Disposable full suite/live acceptance running; parent T-310 not yet green.
- T-443 accepted6cca3aa: frontend lint0 errors/warnings, typecheck0; spacing/banned/motion scripts exit0. Neo-brutal lint NOT_RUN until T-360. Existing perf spec allows17.0ms vs required16.7; T-413 must tighten it, current performance not claimed passing.
- T-442 full gate initially failed104pass/32failed (7 failures+25 errors) because orphan PID79496 held test runtime lease. lsof confirmed only test ports15432/27018 and18000, PPID1; terminated that disposable API process gracefully. Full isolated rerun in progress, no real databases/volumes touched.
- T-442 rerun passed136 tests, zero failures/skips/xfails plus live acceptance. T-444 accepted87025ef: analytics/auth/pit routers Ruff+format0; OpenAPI SHA before/after identical60d831ab. Full backend check follows current bounded batch; no API contract changed.

## Contracts and guardrails
- Preserve every feature, route, copy string, data hook, aria name, state class and DBMS hash route. APIs additive only, each contract change needs ADR and owner approval at the stated hard stop.
- No secrets/.env access, recursive removal, real-database or production-volume changes. Database testing uses disposable apexgrid-test only.
- At most two workers. Packets only, accept.sh rerun/commit required. No bulk product edits by orchestrator. Commit only through accept.sh on overhaul/neo-brutal.
- scripts/agent/status.sh, root status.sh and owner edits in run-loop.sh remain owner property.

## Baseline and risks
- Fresh Phase1 baseline: Ruff542 across backend/app+tests+scripts/eval (540 backend,2 tooling); format25 files across that scope; frontend lint2 explicit-any errors in perf-fps.spec.ts. Mypy222/audit7high2moderate are prior documented inputs until rerun.
- Previous score omitted Ruff/mypy/audit from Functional; T-314 adds F-7..F-9 and hard F-2. Do not report old100 as current.
- Plan tasks larger than three files/150 lines must be split into atomic packets before dispatch. Worker-owned test/config work must respect W1/W2/W3 boundaries.
- ADR-007 approved: light palette/fonts, zero-blur shadows, restricted textures/domain colours, CI and F-7/8/9 plus hard F-2. Runtime gates unchanged until their plan tasks. Current scorer bands50–70/20–40/5–15 retained.
- T-442/443 subdivide oversized T-310/311 into bounded files; parent zero-error gates remain required. Worker edits use isolated local clones on the same overhaul/neo-brutal branch, shared dependency symlinks, no worker commits. Apply reviewed patches sequentially before accept.sh, avoiding its git-add-all boundary collision with another running worker.
- T-440: plan catalogue durations exceed owner100–300ms and display minimum40px conflicts with1.0 leading only>=48px; align specs before their implementation. T-441: palette heading contrast filter>1 can omit a failing real heading; add regression before changing palette gate.
- lock.sh commits directly, conflicting with owner accept-only Git rule. Produced its identical canonical SHA256 banner without its Git tail, verify-lock passed; script unchanged. T-325 test-only work routes to W3 per AGENTS despite plan W2 label.

## Orchestrator direct edits
- T-300: two requested models.env profile lines. T-301: architecture, ADR, lock banner and state/packet/envelope documentation only. Zero frontend/backend/gate edits; no workers dispatched.
- State checkpoint accept initially rejected because completed T-301 target declaration had been removed from NEXT_STATE; restored the completed declaration and reran unchanged lock verification. No product/test/gate changes.
