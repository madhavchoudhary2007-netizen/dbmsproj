# ADR-008 — JWT logout revocation

Status: accepted for implementation under the owner-approved overhaul plan (T-323); not a claim of completed implementation.

## Context

The existing browser and legacy login already issue an opaque string jti from secrets.token_urlsafe(32), and CSRF signatures bind to it. Logout clears cookies but does not invalidate a copied bearer token. The approved plan requires server-side revocation and an additive revoked_tokens table with UUID primary key. Existing opaque identifiers must remain usable without changing any API path, method, response shape or CSRF binding.

## Decision

- Keep the existing opaque jti generation and original claim string for JWT and CSRF. It already supplies the identity the plan requests; do not introduce another session identifier.
- Derive a deterministic UUID database key with uuid5(NAMESPACE_URL, 'apexgrid.jwt:' + jti). This is namespace mapping of an already signature-verified identity, not authentication or a substitute for JWT cryptography. It permits revocation of current opaque jti tokens and UUID-form legacy identifiers using one stable mapping without rewriting tokens.
- Add backend/migrations/004_token_revocation.sql with revoked_tokens(jti uuid primary key, expires_at timestamptz not null) and an expires_at index. Apply and test only on disposable apexgrid-test; never run this migration against the owner's running databases.
- Authentication validates JWT signature/expiry and rejects a mapped, unexpired revoked key before returning the user. WebSocket handshakes enforce the same check; revoked credentials close with the existing invalid-token code4401. Existing connections are not silently reclassified as new handshakes.
- Logout records the validated token's mapped jti and expiry using bound parameters before clearing cookies; repeat writes use ON CONFLICT idempotency. Preserve the existing logout response. Validated claims may be stored on request.state without adding fields to returned user JSON.
- Login deletes only expired revocation rows (expires_at < now()) on its existing database; no background service or dependency is introduced. Database failures fail closed using existing service-unavailable handling, never treating the store outage as an unrevoked token.
- Tokens without a jti retain the plan's explicit compatibility rule: valid until expiry; logout clears their cookies but cannot individually revoke them. Malformed non-string jti is rejected rather than coerced. Existing opaque jti tokens remain individually revocable.
- W3 writes tests first (T-320); W2 implements T-323 in bounded tasks. Preserve Origin, cookie flags, signed CSRF, role checks, login limiter and legacy bearer compatibility.

## Consequences

One indexed lookup is added to authenticated request/handshake checks. Revocation data is bounded by token lifetime plus login-triggered cleanup. A database outage may deny authentication, which preserves fail-closed semantics. The UUID key is a derived identifier rather than the literal opaque claim; logs and UI must never expose the token or signing material. The old no-jti compatibility interval is an explicit remaining limitation.

Tests must cover browser and bearer logout/reuse401, opaque-jti and UUID-form mappings, no-jti compatibility, expired-row cleanup, repeated logout recording, revoked WebSocket handshake, CSRF/Origin failures without unintended writes, and store-outage rejection. Full isolated backend/live acceptance and unchanged OpenAPI remain required.

## Sections affected

ARCHITECT.md B.3 authentication persistence contract and B.4 login state machine; API-01/API-07 acceptance. The plan's UUID storage is retained while its already-existing opaque claim format is preserved. No schema has been applied by this ADR.

## Focused Phase C

Pass1: goal lens traces login -> signature/CSRF -> logout insert -> reused HTTP401 / WS4401, owned by T-320/T-323. Expert lens requires failing-first tests and full disposable acceptance with zero skips. Taste lens adds no UI/dependency; one identity-normalization function is shared by HTTP, logout and WS. Technical lens distinguishes signature validation from UUID mapping, requires bound SQL and fail-closed lookup, and preserves old opaque-jti CSRF. Edge lens covers malformed/no-jti/expired/repeated/concurrent logout and DB outages. The existing opaque-jti/UUID mismatch amended the decision to use a stable namespaced mapping. Pass2 rechecked all five lenses with zero further amendments. Remaining no-jti limitation and lookup availability cost are recorded above.
