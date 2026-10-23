# ADR-011 — Additive liveness and readiness probes

Status: accepted for implementation under owner-approved plan T-320/T-338; no runtime changes by this ADR.

## Context

The plan requires tests for /health/live and /health/ready in Phase2 T-320, while their implementation appears in Phase3 T-338. T-323 requires the full suite green before Phase3. Resolve this dependency by implementing only the health-probe slice as T-44129 after failing-first T-320 tests; logging/request IDs remain in T-338. Existing GET /api/health and every existing API path/method/response remain unchanged.

## Decision

- Add public GET /health/live, HTTP200 with {status: 'alive'}, describing only process availability. It performs no database, Mongo or lease probe and no writes. Runtime-lease middleware must allow this exact new path to reach its route even when the lease is lost.
- Add public GET /health/ready. HTTP200 {status: 'ready', services: {postgres:'up', mongodb:'up', runtime_lease:'up'}} only when all three probes succeed. Otherwise HTTP503 with status:'not_ready' and the same services keys using 'up'/'down'. Return no exception text, URLs, identities or secrets.
- Reuse the existing health() PostgreSQL/Mongo probe behavior without changing its response. Check app.state.runtime_lease explicitly; missing or invalid lease is down. Readiness must report the lease failure itself, so the middleware bypasses only the two new probe paths. All existing request/WS fail-closed lease behavior remains intact.
- Represent both new wire shapes with typed Pydantic models. Missing databases, raised ping errors and missing/lost lease must return the readiness503 contract rather than an unhandled exception or misleading healthy state. Liveness remains200 in those conditions.
- Tests use TestClient without lifespan and monkeypatched stores/lease, no sockets/servers or running DB writes. Root checks unchanged existing OpenAPI entries plus the two approved additions, then runs the full disposable apexgrid-test suite. Do not restart or modify the real application stack.

## Consequences

Deploy/Docker healthchecks can distinguish process failure from dependency unavailability. The old health endpoint and existing clients retain their contracts. Two new paths expose service availability only. Probe requests add read-only database pings and must not mutate race state. JSON logs/request IDs remain a separate Phase3 concern.

## Sections affected

ARCHITECT.md A.2/API-09 additive health contract, B.3/B.6 readiness flow, and T-320/T-338 ordering. NEXT_STATE records T-44129 as the narrowly moved health implementation. Existing routes/schemas/data are retained.

## Focused Phase C

Pass1: goal lens traces process/live and dependency/ready through T-320 tests -> T-44129 -> later T-340 Docker probes. Expert lens requires exact200/503 bodies, no-store liveness and individual dependency-failure tests. Taste lens reuses health() across existing and new endpoints and adds no UI/dependency. Technical lens catches global lease middleware blocking liveness, so only the two new paths receive a bypass and readiness checks ownership itself. Edge lens covers missing/invalid lease and PostgreSQL/Mongo exceptions without data/secret leakage. The dependency-cycle and lease-bypass findings amend this decision. Pass2 rechecked all five lenses with zero amendments; public service-status exposure is the explicit bounded risk.
