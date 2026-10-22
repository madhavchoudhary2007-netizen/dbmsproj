# Phase 1 domain correctness audit (area A)

Audited committed `HEAD` on 2026-10-22. Findings below are based on the current source and schema.

## Findings

1. **F-DOM-01 — P1 — Unclassified results can score championship bonus points.** `backend/migrations/001_initial.sql:258-269` gates position points on `r.classified`, but adds pole and fastest-lap points unconditionally at line 264. Reproduction: create a completed race result with `classified=false`, `pole=true` (or `fastest_lap=true`), recalculate the championship; the driver receives a point. This gives the admin/steward an incorrect standings total for a DNF/DSQ. Gate all scoring bonuses on the applicable classification rule and cover unclassified results.

2. **F-DOM-02 — P1 — Official time penalties do not change classification.** Steward decisions persist `time_seconds` and `grid_places` in `backend/app/main.py:800-801`, but result reads and writes at `backend/app/main.py:707-745` and standings recalculation at `backend/migrations/001_initial.sql:258-289` never apply them. Reproduction: approve a positive time penalty for a driver in a completed race, then fetch results; its position and lap time remain unchanged. The steward's penalty decision therefore does not affect the official race outcome. Apply time penalties when deriving final classification and apply grid penalties to the applicable starting order, or reject penalty types the system cannot enforce.

3. **F-DOM-03 — P1 — Classified positions can contain gaps.** `backend/app/main.py:727-744` upserts each submitted row without validating the classified positions as a complete `1..n` set; `backend/migrations/001_initial.sql:161-165` has uniqueness for driver/session, and lines 199-200 enforce only unique classified positions. Reproduction: submit one classified result at position 2 (or positions 1 and 3) for a completed session; the API persists it. This leaves stewards and viewers with an invalid official classification. Validate the complete classified set transactionally and enforce contiguous positions when publishing/finalizing results.

4. **F-DOM-04 — P2 — Telemetry ingestion is neither idempotent nor ordered.** `backend/app/main.py:914-932` inserts every accepted packet as a new Mongo document and does not compare its timestamp/lap/sector with prior packets. Reproduction: post an identical packet twice to an active session; both are stored and broadcast. Post an older packet after a newer one; it is also stored and broadcast. Retries can duplicate telemetry and stale samples can appear as accepted live updates. Use a stable packet key with an upsert and reject or quarantine out-of-order samples per session and driver.

5. **F-DOM-05 — P2 — The running simulator does not use a reproducible random stream.** `advance_simulation_tick` falls back to process-global `random` at `backend/app/main.py:1451-1455`, and `simulation_loop` calls it without an RNG at line 1661. `Simulation` has no seed or RNG state. The fixed-seed test at `backend/tests/test_api.py:462-469` only exercises an injected RNG, not the production loop. Replaying a race from the same stored entries therefore produces different telemetry. Store a race seed and use a per-simulation PRNG for every random draw, including generated entry offsets.

## Inspected with no additional finding

- Pit reservation overlap and concurrent allocation: `backend/app/main.py`, `backend/migrations/001_initial.sql`, and `backend/tests/test_database.py` cover box locking, exclusion constraints, driver uniqueness, and serialized automatic allocation.
- Session/event lifecycle and incident decision integrity: `backend/migrations/001_initial.sql` and `backend/tests/test_database.py` cover legal session transitions, timestamp guards, incident lap limits, approved-incident penalties, immutable penalties, and duplicate decision prevention.
- Simulator lap bounds and sector coherence: `backend/app/main.py` and `backend/tests/test_api.py` cover 0/1/72-lap boundaries, sector/lap timing, and seeded helper repeatability; production reproducibility is finding F-DOM-05.
- Tie-break determinism: `backend/migrations/001_initial.sql:287-289` orders by points, wins, podiums, then driver UUID.
- Read-only support reviewed: `backend/app/database.py`; no additional domain finding.

No duplicate G11 or F-ACE01 finding is included.
