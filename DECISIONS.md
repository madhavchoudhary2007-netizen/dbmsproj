# ADR-001 — Data ownership and application shape

Date: 2026-10-05
Status: Accepted

## Context

The presentations require transactional official state and flexible high-volume telemetry.

## Decision

Use a FastAPI modular monolith, PostgreSQL for official state, MongoDB for telemetry, Next.js for UI and WebSockets for live updates.

## Reason

This maps the demonstrated DBMS behavior to the database responsible for it and keeps deployment small.

## Consequences

Cross-store joins occur in the backend by shared UUID. MongoDB availability must be reported separately.

## Reconsider only if

Measured scale requires a separate ingest service.

# ADR-002 — Database-enforced race rules

Date: 2026-10-05
Status: Accepted

## Context

The project must demonstrate actual PostgreSQL behavior.

## Decision

Use a penalty insert trigger, explicit-cursor standings routine, and row-locked pit reservation transaction with overlap protection.

## Reason

Application-only calculations would not satisfy the required database demonstration.

## Consequences

Integration tests must use PostgreSQL, not SQLite.

## Reconsider only if

The product requirements remove the DBMS demonstrations.

Perfection loop authorizations: `.agent/adr/ADR-001-perfection-loop-authorizations.md` (agent-architecture ADR namespace).

- ADR-008 JWT logout revocation: .agent/adr/ADR-008-jwt-revocation.md (planned additive disposable-stack store; existing opaque jti and API contracts retained).

- ADR-011 health probes: .agent/adr/ADR-011-health-probes.md; additive liveness/readiness only, health slice moved before T-323 to satisfy T-320 tests.

- ADR-012 dashboard next event: .agent/adr/ADR-012-dashboard-next-event.md; additive read-only nullable field for plan T-370, existing fields retained.

- ADR-013 stewarding read models: .agent/adr/ADR-013-stewarding-read-models.md; planned read-only official penalty history and explicit seasonal licence points for T-387.

- ADR-014 efficient delivery: .agent/adr/ADR-014-efficient-delivery-workflow.md; consolidated task/evidence schedule, bounded domain tranches, unchanged final gates, implementation paused until owner start.

- ADR-015 Antigravity domain delivery: .agent/adr/ADR-015-antigravity-domain-delivery.md; HIGH orchestrator/LOW workers, bounded domains, exact packet verification and root-owned integration; no product/config/gate changes.
