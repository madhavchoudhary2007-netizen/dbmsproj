# ADR-006 — Persisted generated-race replay seed

Status: Accepted for F-DOM-05 implementation
Date: 2026-10-23

## Context

Generated races choose names, track, grid, pace and every sector's jitter from process-global random state. An active race can restore its stored telemetry after restart, but cannot reproduce the same future sector values from a known seed. F-DOM-05 requires a persisted seed so the same recorded roster, initial state, timestamps and external pit/safety-car inputs can be replayed deterministically. ADR-001 authorizes additive migrations on the disposable stack.

## Decision

- Add a nullable, nonnegative `simulation_seed bigint` to `demo_races` in numbered migration 003. Existing rows remain untouched; null retains legacy nondeterministic behavior. New generated races generate a 63-bit seed and persist it in the same transaction as the race row.
- Use a dedicated `random.Random(seed)` for generated race selection. Persisted driver IDs, names, numbers, teams and pace offsets remain the authoritative replay roster; passwords and UUIDs remain generated securely, outside deterministic simulation randomness.
- Load the stored seed when restoring an active generated race. Generated telemetry uses a stable, per-driver, per-progress random stream derived from that seed and recorded driver ID rather than the process-global RNG. An explicit RNG supplied by a test keeps precedence. Given the same roster, starting simulation state, timestamps, safety-car and pit assignments, sector pace/control values and positions repeat across a fresh process.
- Replay is a deterministic engine capability against the existing stored race, not a new API route or a rewrite of stored telemetry. A restart continues from persisted telemetry; historical rows are retained. Wall-clock timestamps, manual actions and external pit assignments must be supplied as replay inputs and are not promised identical by seed alone.

## Consequences

- Migration 003 is additive and idempotent on the disposable `apexgrid-test` stack; no production volume or current database is modified in this loop.
- W3 first proves a fixed seed plus roster produces the same telemetry despite unrelated global random draws and proves seed carry-through on create/restore. W2 then persists/loads it and uses a stable driver/progress RNG. Full isolated backend and live acceptance run after marker retirement.
- Existing API response shapes remain unchanged. Legacy demo races with a null seed continue to run.

## Sections affected

- `.agent/ARCHITECT.md` B.3 generated-race internal contract, B.4 simulation transition, G15, Phase C ADR-006, Risks R08.
