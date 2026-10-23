# NEXT_STATE
updated_at: 2026-10-23
phase: 0 architecture amendment

## Queue
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
- T-440 (O, before motion packets): align plan2.3/2.7 with owner100–300ms and display>=48px leading limits; those conflicting catalogue specifications are missing a correction task.
- T-441 (W3, before T-360 palette change): add heading-contrast regression for real contrast<=1, preserving4.5 threshold and excluding aria-hidden decorative duplicates only; current >1 filter omits failures.

## Done
- T-300 accepted e465e89; boot exit0, lock/budgets pass, boot OK.
