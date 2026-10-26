---
name: evaluate
description: Run the multi-dimension evaluation and the defect loop, then score. Use when a milestone's tasks are verified or before presenting a deliverable.
---

Read `.agent/protocol/evaluation.md` and `.agent/protocol/packets.md`, use a shared evidence set and at most two concurrent W3 workers for independent missing evidence (never four duplicate suite runs), run `bash scripts/eval/score.sh`, and follow the defect loop. Present only when the script exits 0.
