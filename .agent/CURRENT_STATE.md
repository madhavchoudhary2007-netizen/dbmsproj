# CURRENT_STATE
updated_at: 2026-10-23
git_head: 1acf8e1
branch: overhaul/neo-brutal
architect_sha256: 0dbd38b2c32d662bc2d5aaa31178ba23a93b28d1f8a6dfd23a8322e5bf229cda
harness: codex
archetype: existing enterprise-saas; Neo-Brutal Motorsport (light) proposed in T-301
last_eval_score: historical 100 claim is not a verified baseline for this overhaul

## Active work
- Owner's neo-brutal overhaul replaces the prior perfection-loop task queue. Source of tasks: docs/overhaul-plan.md sections 0,1,3-6. Product changes wait for explicit ADR-007 approval at T-302.
- T-300 boot exit 0: architecture lock verifies; CURRENT/NEXT budgets pass; boot OK. Created overhaul/neo-brutal from perfection-loop 1acf8e1.
- H=codex; models.env defaults HARNESS via caller and uses gpt-6.1-sol/medium for Codex orchestrator. Worker models/efforts/cap and context windows preserved. Claude 433000 context settings were owner-supplied edits and are preserved.
- Owner-supplied docs/overhaul-plan.md and .claude/settings.json are being recorded unchanged with T-300; accept.sh stages all changes, so both are explicitly listed in that task's targets.

## Contracts and guardrails
- Preserve every feature, route, copy string, data hook, aria name, state class and DBMS hash route. APIs additive only, each contract change needs ADR and owner approval at the stated hard stop.
- No secrets/.env access, recursive removal, real-database or production-volume changes. Database testing uses disposable apexgrid-test only.
- At most two workers. Packets only, accept.sh rerun/commit required. No bulk product edits by orchestrator. Commit only through accept.sh on overhaul/neo-brutal.
- scripts/agent/status.sh, root status.sh and owner edits in run-loop.sh remain owner property.

## Baseline and risks
- Plan section0 records Ruff540, format23 files, mypy222, frontend lint2 errors, npm audit7 high/2 moderate; these are documented inputs, not fresh measurements this session.
- Previous score omitted Ruff/mypy/audit from Functional; T-314 adds F-7..F-9 and hard F-2. Do not report old100 as current.
- Plan tasks larger than three files/150 lines must be split into atomic packets before dispatch. Worker-owned test/config work must respect W1/W2/W3 boundaries.
- Plan conflicts pending ADR-007: light palette, permitted zero-blur shadows, multiple accent tokens/textures, font/display leading, CI/gate expansion. No gate changed yet.

## Orchestrator direct edits
- T-300: two requested models.env profile lines; state/packet/envelope documentation only. Zero frontend/backend edits.
