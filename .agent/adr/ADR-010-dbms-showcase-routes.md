# ADR-010: DBMS showcase routes

Status: accepted for the scope already authorized by ADR-007 and the owner; implementation remains incomplete.

## Context

Phase 4 of docs/overhaul-plan.md requires an admin-only database teaching showcase. The current implementation includes canned isolation and deadlock responses and formerly returned fabricated rows or refresh success on failures. The analytics SQL references a relational `lap_telemetry` relation that is not present in the current migrations. Completed-lap telemetry is held in MongoDB, with per-driver/lap records selected by `race_lap_measurements`; historical demo records must retain their existing provenance.

## Decision

- Preserve existing routes, methods and response fields; use the existing administrator dependency and CSRF enforcement. Errors must be explicit and must not contain fabricated database results.
- Isolation and deadlock demonstrations must use real independent PostgreSQL transactions, deterministic coordination and bounded waits, with rollback or cleanup of owned demonstration records. Report observations and SQLSTATE from PostgreSQL rather than scripted results. Validate on the disposable `apexgrid-test` stack; never mutate real database data for tests.
- Views, materialized view refresh, EXPLAIN, audit and security panels must reflect actual PostgreSQL operations and metadata. Attribute writes through transaction-local actor context and test restricted-role behavior explicitly. Never rewrite applied migration files; any required additive migration has a separate decision and disposable-stack tests.
- Race-gap analysis must use actually recorded completed laps and elapsed times scoped to the requested race, preserving missing data and ties. A parameterized, bounded PostgreSQL values/CTE bridge from the existing Mongo lap archive is a candidate; finalize only after validating stored telemetry semantics and query plans. Never infer race elapsed from best-lap times or synthesize laps. Missing or unavailable source data must be represented honestly.

## Consequences

The showcase requires database integration tests in addition to isolated tests, and real concurrency requires cleanup and timeouts. Normal app database data must never be altered by a test. These decisions do not create a schema migration, authorize changed response shapes, or establish that prior implementations are correct. This records the pre-existing Phase 4 scope; no locked architecture section is altered.

## Sections affected

ADR-007 additive backend scope; docs/overhaul-plan.md Phase 4; docs/completion-plan.md T-44623 through T-44629.
