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
