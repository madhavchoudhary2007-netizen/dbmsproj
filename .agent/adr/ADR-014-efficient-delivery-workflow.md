# ADR-014 — Consolidated delivery and verification workflow
Date: 2026-10-26
Status: Accepted by owner instruction to optimize referenced plan/protocol documents, then wait for start work.

## Context
T-44569 through T-44572 reduced main.py from 764 to 732 lines while adding 215 lines in four route-assembly modules. Small move packets, repeated state history, boot plus its own budget subcheck, and separate T-331/T-332 restructuring caused avoidable handoffs and intermediate wrappers. The old perfection-loop branch/cycle instructions conflict with the active twelve-phase overhaul. The owner authorized documentation optimization and paused product work.

## Decision
Use delivery-workflow.md as the canonical execution schedule. Keep normal packets small; allow a bounded one-domain mechanical/DI tranche up to eight named files and 800 changed lines, with justification and no unrelated semantic changes. Reconcile T-331/T-332 as one domain-by-domain structural milestone without temporary forwarding wrappers; retain main.py <=120 lines as a final gate. Documentation reconciliation is orchestrator-owned and may cover an explicit larger Markdown file set.

Keep worker verification plus independent accept.sh rerun. Use task-focused checks, complete domain/milestone integration gates and complete final release gates. Deduplicate only identical evidence at the same relevant revision/scope/environment. Full backend integration is required at a structural domain milestone; auth/schema/persistence-sensitive tasks require their own relevant integration proof. A missing integration check remains unverified. Boot runs once per session/configuration change and already includes budget/lock checks; budget runs every five accepted tasks or before handoff when not already covered.

No feature, API, schema, dependency, visual requirement, test assertion, score weight, threshold or final gate changes. Two-worker cap, roles, independent acceptance, secrets/data restrictions and five-repair limit remain. Archive stale execution directions through explicit headers; keep historical evidence. Implementation stays PAUSED until the owner's start instruction.

## Fresh-model handoff
START_HERE.md supplies a numbered root-relative reading/run order, explicit PAUSED -> RUNNING transition on owner start, a twelve-phase status table in CURRENT_STATE, first-domain source/test paths, role/verification decisions and failure handling. It requires no previous chat history and does not authorize implementation.

## Consequences
Larger coherent moves need careful review and explicit regression coverage; file/line caps never justify combining unrelated changes. Intermediate task evidence is not a full milestone or final score. Existing route/provider changes invalidate dependent evidence; shared UI changes invalidate affected route evidence. Product docs with old test counts are labelled historical, not treated as current readiness claims. No product implementation is performed by this ADR.

## Sections affected
AGENTS.md; ARCHITECT.md B.2 and focused Phase C; overhaul-plan.md status, T-331/T-332, dependency schedule, acceptance checklist and restart appendix; packets/state-files/roles/evaluation/architect/compaction/perfection-loop/design/bootstrap protocol routing; CURRENT_STATE/NEXT_STATE; project entrypoint documentation. delivery-workflow.md is canonical for cadence and task sizing. Existing design and evaluation rubric remain byte-for-byte unchanged in their normative sections.

## Focused Phase C
Pass 1 — Goal: all existing A.2 deliverables and twelve-phase requirements retain owners and final gates; pause blocks implementation. Verification: independent acceptance remains; task, integration and release evidence are distinct, with zero DB skips and no current score inferred. Taste: remove throwaway abstraction incentives; main length is a final entrypoint guard, not a per-task target. Technical: bounded domain tranches, context preflight, exact evidence identity, disposable DB boundary and no source/script/config edits in this reconciliation. Edge: stale results after shared changes, unavailable DB/browser, failed envelope, partial verification, resume on wrong branch and unrelated dirty files all remain visible/blocking as appropriate.
Pass 2 — All five lenses rechecked after explicitly requiring integration proof for auth/schema/persistence/shared-provider changes and retaining every scoring threshold. Zero additional amendments. Risk: the existing acceptance script validates/executes before checking a FAILED status; classify failed results before invoking it, without changing the executable during this documentation task.
