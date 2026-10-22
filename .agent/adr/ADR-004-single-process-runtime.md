# ADR-004: Guard the in-memory race runtime to one backend process

## Context

`backend/app/main.py` keeps `simulations` and the WebSocket `EventBus` in process memory. Two API processes can each accept control requests but see different simulator state and subscriber sets. PostgreSQL/MongoDB persist race records, but they do not broadcast live events between processes. The supplied Dockerfile and Compose command each start one Uvicorn worker; a changed worker count or a second backend replica would silently split live race control.

## Decision

- Support one active backend process per PostgreSQL database until simulator ownership and event delivery move to shared coordination. The Compose/Docker commands remain one worker and the README must state this deployment limit.
- Hold a PostgreSQL session-level advisory lock for the full FastAPI lifespan before starting or restoring any simulation. A second process using that database must fail startup with a clear error. If the lock connection is lost, fail closed rather than continuing to serve simulation/WebSocket operations without ownership. Release the lock at normal shutdown.
- Keep PostgreSQL official rows and MongoDB telemetry as they are; no data/schema or public HTTP contract changes. A future multi-process design needs a separate ADR with shared simulator leadership and cross-process event delivery.

## Consequences

An extra backend process cannot silently operate a divergent in-memory race. Startup depends on PostgreSQL ownership; loss of that connection stops the runtime. This is intentional for correctness and may require a process restart after database recovery. No new runtime dependency or migration is needed.

## Sections affected and proof

- `.agent/ARCHITECT.md` B.4, B.6, Risks and focused Phase C review.
- W3 pins first-owner/second-owner/release/reacquire and lost-connection behavior on apexgrid-test. W2 implements lifespan acquisition, monitoring and shutdown release. Orchestrator reruns the scoped and full isolated gates; docs and Compose single-worker expectations are checked before Phase 2 closure.
