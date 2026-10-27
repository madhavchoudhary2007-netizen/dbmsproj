# ADR-018: Serialize standings recalculation per championship

Status: accepted under ADR-001; implementation and disposable-stack validation pending.

## Context

The existing standings function deletes and reinserts rows. An owned, disposable PostgreSQL/Mongo fixture with two independently synchronized recalculations reproduced SQLSTATE 23505. The owned databases were removed after the probe. Concurrent callers should not receive a uniqueness conflict solely because they recalculate the same championship.

## Decision

Add a new replay-safe migration that acquires a transaction-scoped row lock on the championship before the existing standings calculation. Calls for the same championship serialize; calls for different championships need not block each other. Retain the current points, ranking, missing-championship error and public API behavior. Do not alter applied migrations, drop tables or rewrite existing data as part of the migration.

## Consequences

Rerun the deterministic concurrent probe on a newly owned disposable database, compare the final standings with the serial baseline, and verify migration replay and existing tests. Row locks may make a concurrent caller wait until the preceding calculation commits; database transaction timeout policy remains unchanged. Do not migrate the real stack during implementation.

## Sections affected

ADR-001 additive, non-destructive migrations; the existing standings and DBMS contracts in the locked architecture; the completion plan's race-data and integration gates. This clarifies an authorized implementation and does not alter the locked architecture body or API shape.
