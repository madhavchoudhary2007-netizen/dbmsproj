# CURRENT_STATE
updated_at: 2026-10-23
git_head: e465e89
branch: overhaul/neo-brutal
architect_sha256: 80f8ab5074bfe238e9467f3eabde3df685f801fce2a1f667c8bd6f3d533ed421
harness: codex
archetype: Neo-Brutal Motorsport (light) proposal; owner approval pending T-302
last_eval_score: historical 100 claim is not a verified baseline for this overhaul

## Active work
- Owner's neo-brutal overhaul replaces the prior perfection-loop task queue. Source of tasks: docs/overhaul-plan.md sections 0,1,3-6. Product changes wait for explicit ADR-007 approval at T-302.
- T-300 accepted e465e89: boot exit0/boot OK; branch based on perfection-loop1acf8e1. T-301 ADR-007 draft amends A.4/A.5/B.5; focused five-lens pass2 yielded zero new amendments; relock/verify exit0, awaiting accept.sh.
- H=codex; models.env defaults HARNESS via caller and uses gpt-6.1-sol/medium for Codex orchestrator. Worker models/efforts/cap and context windows preserved. Claude 433000 context settings were owner-supplied edits and are preserved.
- T-300 accepted by accept.sh, commit e465e89. Owner-supplied docs/overhaul-plan.md and .claude/settings.json were recorded unchanged; both were explicitly listed because accept.sh stages all changes.

## Contracts and guardrails
- Preserve every feature, route, copy string, data hook, aria name, state class and DBMS hash route. APIs additive only, each contract change needs ADR and owner approval at the stated hard stop.
- No secrets/.env access, recursive removal, real-database or production-volume changes. Database testing uses disposable apexgrid-test only.
- At most two workers. Packets only, accept.sh rerun/commit required. No bulk product edits by orchestrator. Commit only through accept.sh on overhaul/neo-brutal.
- scripts/agent/status.sh, root status.sh and owner edits in run-loop.sh remain owner property.

## Baseline and risks
- Plan section0 records Ruff540, format23 files, mypy222, frontend lint2 errors, npm audit7 high/2 moderate; these are documented inputs, not fresh measurements this session.
- Previous score omitted Ruff/mypy/audit from Functional; T-314 adds F-7..F-9 and hard F-2. Do not report old100 as current.
- Plan tasks larger than three files/150 lines must be split into atomic packets before dispatch. Worker-owned test/config work must respect W1/W2/W3 boundaries.
- ADR-007 proposes light palette/fonts, zero-blur hard shadows, restricted textures/domain colours, CI and F-7/8/9 plus hard F-2. No gate changed. Current scorer bands50–70/20–40/5–15 retained; plan's tighter design targets do not widen them.
- T-440: plan catalogue durations exceed owner100–300ms and display minimum40px conflicts with1.0 leading only>=48px; align specs before their implementation. T-441: palette heading contrast filter>1 can omit a failing real heading; add regression before changing palette gate.
- lock.sh commits directly, conflicting with owner accept-only Git rule. Produced its identical canonical SHA256 banner without its Git tail, verify-lock passed; script unchanged. T-325 test-only work routes to W3 per AGENTS despite plan W2 label.

## Orchestrator direct edits
- T-300: two requested models.env profile lines. T-301: architecture, ADR, lock banner and state/packet/envelope documentation only. Zero frontend/backend/gate edits; no workers dispatched.
