# ADR-017: Audit RLS scope on restricted connections

Status: accepted under ADR-001 and ADR-007; implementation and disposable-stack validation pending.

## Context

The Phase 4 plan specifies that stewards see penalty audit rows only. Migration 008 instead allows every audit table to a restricted session with steward context. A rollback-only test against the guarded disposable stack confirmed that both championship and penalty rows were visible. Applied migration checksums must remain unchanged.

## Decision

Add a new idempotent migration that replaces the existing audit policy with a policy enforcing penalty-only scope for steward sessions, permits the established admin/director and owner behavior, and denies access when role context is missing or unrecognized. Preserve necessary writes for audit triggers and validate restricted-role reads, writes and trigger behavior on the disposable stack. Do not drop tables, rewrite data or alter migrations 001–008.

Transaction-local `apexgrid.role` is application-supplied context, not independent proof of identity for a person with arbitrary SQL access to the shared database credential. The application must set it only from validated authentication; this policy does not claim protection from a holder of that database credential who can set their own context. Do not present the metadata panel as proof of that stronger boundary.

## Consequences

An additive migration must be tested against the disposable apexgrid-test project, including rollback/replay and existing owner behavior. Real databases and volumes are not modified during implementation. Tests must preserve existing assertions and must exercise an actual restricted role rather than the table owner.

## Sections affected

ADR-001 additive migrations; ADR-007 and ADR-010 Phase 4 scope; docs/completion-plan.md T-44627/28. This decision clarifies authorized scope and does not change the locked architecture body.
