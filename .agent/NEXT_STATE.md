# NEXT_STATE
updated_at: 2026-10-23
phase: 0 architecture amendment

## Queue
### T-300 — branch and harness boot
- worker: O | priority: P0 | origin: overhaul-plan section3 Phase0
- target_files: .agent/models.env, .claude/settings.json, docs/overhaul-plan.md
- contract: branch overhaul/neo-brutal from perfection-loop; caller-selected harness; Codex gpt-6.1-sol; preserve owner-supplied settings/plan and worker/cap/context settings
- verify: HARNESS=codex bash -c 'source .agent/models.env && bash scripts/agent/boot.sh'
### T-301 — ADR-007 architecture amendment
- worker: O | priority: P0 | after: T-300
- target_files: .agent/ARCHITECT.md, .agent/adr/ADR-007-neo-brutal-motorsport-light-overhaul.md
- contract: amend A.4/A.5/B.5; focused five-lens review and relock; no product or gate edits
- verify: bash scripts/agent/verify-lock.sh
### T-302 — explicit owner approval
- worker: O | priority: P0 | after: T-301
- target_files: .agent/CURRENT_STATE.md, .agent/NEXT_STATE.md
- contract: post ADR summary and wait for owner message approved before frontend/backend edits or product dispatch
- verify: owner message

## Blocked
- T-310 onward: ADR-007 owner approval required.
- T-440 reserved only for a concrete missing plan task; none added.

## Done
- none in overhaul branch yet.
