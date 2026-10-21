# ADR-001 — Perfection loop authorizations

Status: Accepted
Date: 2026-10-21

## Context

The locked architecture preserves the existing ApexGrid schema, API contracts, and visual identity. The perfection loop needs explicit permission to address findings involving typography, authentication transport, additive schema changes, and narrowly justified API changes. This ADR records the user's decision; it does not implement any of those changes.

## Decision

1. The font family and type scale may change. Choose them from the Enterprise SaaS / Analytics archetype table and record the reason in writing.
2. Migrate the bearer token from `localStorage` to an `httpOnly`, `Secure`, `SameSite` cookie with CSRF protection. Make matching backend changes and tests.
3. Additive schema migrations are allowed. Test them only on the disposable stack; never drop or rewrite existing data.
4. Change an API contract only when a finding or change proposal requires it. Write a separate ADR for each such change.

These authorizations supersede the earlier requirement to ask before changing the font family. They permit future scoped work; current code, database contents, and API behavior remain as built until separately implemented and verified.

## Consequences

- Typography work must cite the archetype table and explain its choice while preserving the product's motorsport identity.
- The auth migration needs coordinated frontend/backend implementation, CSRF protection, and tests before acceptance. Keep existing user roles and session behavior accounted for.
- Schema work requires a disposable stack and non-destructive migration evidence. Running database data must remain untouched during this reconciliation.
- Every necessary API contract change gets its own ADR tied to a finding or change proposal, with affected clients and tests identified before implementation.
- Existing architecture and task descriptions may state these paths are permitted, but this ADR alone does not mark any implementation or quality gate complete.

## Sections affected

- `.agent/ARCHITECT.md` A.5 and A.6: scope and assumptions.
- `.agent/ARCHITECT.md` B.3 and B.4: current contracts and auth state machine.
- `.agent/ARCHITECT.md` Gap List G10 and G11; Phase C focused review; Risks R03.
- `.agent/NEXT_STATE.md` T-014 and its blocked reason; `.agent/CURRENT_STATE.md` open auth risk.
