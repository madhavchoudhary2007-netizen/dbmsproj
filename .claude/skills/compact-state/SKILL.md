---
name: compact-state
description: Compact context safely by syncing on-disk state through normal accept.sh tasks and re-seeding without an extra checkpoint commit. Use right after a compaction (automatic at 400k) to re-seed, or before ending a long session.
---

Read `.agent/protocol/compaction.md` and run its sequence in order. Re-seed only from `ARCHITECT.md`, `CURRENT_STATE.md` and `NEXT_STATE.md`.
