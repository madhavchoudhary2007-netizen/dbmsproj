# ADR-012 — Dashboard next scheduled race
Date: 2026-10-24
Status: Accepted under owner automatic approval for the overhaul

## Context
Plan T-370 requires an active session, incident count and next event in the shell ticker. Existing GET /api/dashboard has counts and active_session but no upcoming event identity. Inventing an event from a count would misrepresent database records. Owner approved additive finding-backed API changes with their own ADR and later instructed autonomous completion.

## Decision
Add only next_event to the existing dashboard response. It is null or {id, name, session_id, scheduled_at, circuit_name}: id is race_events.id; session_id is race_sessions.id; scheduled_at is the session timestamp serialized as UTC. Choose the earliest future scheduled RACE session (scheduled_at >= CURRENT_TIMESTAMP), ordered by scheduled_at then session id. Exclude active, paused, completed, cancelled and overdue scheduled sessions. Preserve every existing field and count calculation. Read only existing tables; no migration or data changes. W3 writes regression tests before W2 implements this query; root runs the disposable full suite. Shell and dashboard share the existing cached dashboard read.

## Consequences
Clients gain one nullable field and can display actual upcoming race details without another endpoint. Old clients ignore it. The scheduled_events count can exceed upcoming candidates because its existing definition includes overdue scheduled races; preserve that definition. Database timestamp comparison supplies one authoritative clock. Missing data hides the ticker item. No unrelated endpoint, auth, schema or feature change is authorized.

## Sections affected
ARCHITECT A.2 API-09; B.3 cross-module contracts; focused Phase C below. T-44240 documents the proposal; subsequent W3/W2 tasks own tests and implementation. Existing OpenAPI and runtime route gates remain mandatory.

## Focused Phase C
Pass1 Lens1: dashboard -> shared cache -> shell ticker and dashboard; prerequisites existing authenticated read and PostgreSQL, W3/W2/root owned. Lens2: focused pytest verifies null, future ordering/ties, exclusions and all old fields; full apexgrid-test suite and OpenAPI checks follow implementation. Lens3: one existing query module, no dependency or new abstraction, two planned consumers. Lens4: UTC database clock, stable session-id tie-break, read-only query and preserved count semantics prevent fabricated or nondeterministic records. Lens5: no candidate, multiple sessions per event, equal timestamps, overdue and non-RACE/terminal states covered by tests. Pass2: all five lenses reviewed with zero additional amendments. Implementation and tests remain pending, not passing claims.
