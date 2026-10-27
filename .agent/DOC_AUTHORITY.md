# Antigravity document authority map

Status: ACTIVE. Owner chat > AGENTS.md > routed protocols > repository evidence. This map resolves document roles; it does not add product scope or weaken a gate. Read this once at session recovery, not before every task.

## Follow for the active overhaul
| Decision | Source |
|---|---|
| Permission, priority, safety | Latest owner instruction; AGENTS.md |
| Recovery order | START_HERE.md; current CURRENT_STATE.md / NEXT_STATE.md |
| Requested/observed Antigravity model settings | protocol/antigravity.md (Gemini 3.8 Flash HIGH root / LOW workers, cap 2) |
| Task size, scheduling, evidence reuse | protocol/delivery-workflow.md; ADR-014 as clarified by ADR-015/ADR-016 |
| Roles / packets / state / context | protocol/roles.md, packets.md, state-files.md, compaction.md on their triggers |
| Remaining-work order after 2026-10-27 audit | docs/completion-plan.md and current NEXT_STATE; this schedules existing requirements, not new product scope |
| Product scope and visual identity | docs/overhaul-plan.md; approved ADR-007; locked ARCHITECT.md |
| Design / UX | protocol/design-visual.md and design-ux.md; existing tokens/types, approved plan section 2 |
| Architecture amendment | protocol/architect.md then lenses.md; archetypes.md records the already approved choice |
| Evaluation | protocol/evaluation.md and actual score.sh results; no old score is current |
| Run commands | .agent/commands.env and current packet; browser/DB/network checks are root-owned |
| Deferred findings | queue.md; promote only after reconciling accepted work and exact prerequisites |

## Evidence, never a competing workflow
- .agent/workspaces/** contains historical isolated checkout copies, not the current root instructions. Never search it during recovery or copy its old AGENTS/state/protocols into this checkout; preserve these directories and any live ownership.
- .agent/archive/**, LOOP.md, both FINAL_REPORT.md entrypoints, backlog.md and perfection-loop.md are historical or retirement pointers. They cannot authorize branch switches, phase caps, old model settings, exemptions, test skips, installs or completion claims.
- PROJECT_STATE.md, docs/flow-audit-2026-10-06.md, .agent/audit/**, .agent/results/** and old packets are observations/evidence. Only a current approved packet may instruct its assigned worker. Reconcile live ownership before changing/retrying an in-flight packet.
- ADR Context/Phase C records describe decision-time observations, not current implementation status. Later accepted ADRs amend earlier execution rules; current state/Git/results establish completion. ADR-007's old 3-file/150-line execution wording is superseded by ADR-014/015's bounded domain policy; its visual/safety gates still apply.
- README.md, PROJECT_CONTEXT.md, docs/api.md, docs/contracts.md, docs/database.md, docs/architecture.md and docs/demo-guide.md explain the product/operator flow. Their commands do not authorize an agent to mutate real databases, seed/reset records or start services. Verify wire/type observations against current source and snapshot before copying a packet; discrepancies become findings, never permission to change an API.
- Templates, .claude/** and .codex/** are harness-specific examples/configuration, not Antigravity worker instructions. frontend/AGENTS.md's generated framework advice is subordinate to root safety and packet scope; any needed vendor guide is listed by the root in read-only packet context.
- The historical perfection loop cannot reactivate itself. An explicit new owner instruction requires reconciling its archived plan against current branch/lock/gates first.

## Concrete conflict resolution
Spacing 0/4/8/12/16/24/32/48/64px; approved Space Grotesk/Space Mono; cream/paper/red roles and unchanged bands; max 3 accents; radius 0/9999px; zero-blur static hard shadows; transform/opacity/background-color motion at 100–300ms with reduced-motion fallback. Generic archetype examples cannot override these rules. Keep all five states and every existing feature/hook/copy/ARIA contract.

Worker Verify is exact and offline. Root separately runs browser/network/disposable DB gates; accept.sh repeats only the approved worker Verify. No arbitrary runtime cutoff, no third duplicate check, no skipped DB pass and no NOT_RUN completion. Documentation delivery needs documentation checks, not a fabricated product score.

## Audit boundary
ADR-016 records the file inventory, conflicts and validation scope. Documentation can reduce ambiguity; only actual UI/session evidence establishes model binding. No prose or static text scan guarantees future model compliance.
