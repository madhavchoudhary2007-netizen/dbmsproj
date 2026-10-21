---
name: compact-state
description: Compact context safely by syncing the on-disk state files, checkpointing, compacting and re-seeding. Use right after a compaction (automatic at 400k) to re-seed, or before ending a long session.
---

Read `.agent/protocol/compaction.md` and run its sequence in order. Re-seed only from `ARCHITECT.md`, `CURRENT_STATE.md` and `NEXT_STATE.md`.
