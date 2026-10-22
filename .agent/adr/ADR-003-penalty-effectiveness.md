# ADR-003: Do not accept sanctions the official timing model cannot apply

## Context

F-DOM-02 found that steward decisions persist `time_seconds` and `grid_places`, but no classification or starting-grid computation reads them. The seeded historical race includes a five-second penalty. `session_results.lap_time_ms` is a best lap, while generated-race finish order comes from telemetry `elapsed_ms`; treating the best lap as race elapsed time would give false rankings. There is no persisted starting-grid contract. Accepting a sanction as applied is therefore misleading.

## Decision

- Keep the existing `Decision` request fields and historical penalty rows. Reject a new decision with positive `time_seconds` or `grid_places` at the API boundary with HTTP 422 and a cause/next step; allow points-only and rejected decisions as before. No incident or penalty write occurs on rejection.
- Keep time and grid controls visible to explain the current limitation, but disable their use until timing and grid rules are implemented. Show existing nonzero sanctions as recorded but unapplied; mark affected classification/standings as provisional rather than calling them final.
- Add a Phase 3 change proposal for full time and grid enforcement within the existing steward and session capabilities. It must define race elapsed time, starting order, inherited data, reranking, and per-role acceptance tests before lifting the rejection. No historical data is deleted or rewritten.

## Consequences

The request shape stays compatible, but previously accepted positive time/grid values now receive HTTP 422. This is an intentional contract change backed by a reproducing test. Point penalties remain effective through the existing trigger. Existing stored sanctions require a visible provisional state, so this ADR alone does not close F-DOM-02. The full enforcement proposal remains fixable P2 work and is required before DONE.

## Sections affected and proof

- `.agent/ARCHITECT.md` A.2 API-05, B.3, B.4 and focused Phase C review.
- W3 reproduces the current silent acceptance and checks no-write rejection; W2 adds the boundary guard; W1 explains disabled controls; W3 verifies historical provisional display. Isolated backend, browser, and role journeys must pass before closing the silent-acceptance defect.
