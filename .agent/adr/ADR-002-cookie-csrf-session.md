# ADR-002: Browser authentication through session cookies

## Context

G11 records an access token in browser localStorage (`frontend/components/auth.tsx`, `frontend/lib/api.ts`, and the live WebSocket client). A script running in that origin can read and export it. ADR-001 authorizes a coordinated httpOnly cookie and CSRF migration. The browser and API are on different ports in local development, while production may use HTTPS. Existing API clients and acceptance tests use bearer headers and the `apexgrid.jwt` WebSocket subprotocol.

## Decision

- `POST /api/auth/login` will return `{user}` and set host-only `apexgrid_session` (JWT; HttpOnly; SameSite=Lax; Secure outside the local HTTP demo) and `apexgrid_csrf` (readable; SameSite=Lax; same Secure policy). Both cookies use `Path=/` and no Domain. The JWT has a random `jti` in addition to existing `sub`, `role`, and `exp`.
- The CSRF cookie contains a random nonce and HMAC-SHA256 over that nonce bound to the session `jti`. Browser writes send its exact value in `X-CSRF-Token`. The backend compares cookie/header in constant time and validates the signed value against the authenticated JWT on every unsafe cookie-authenticated API method. Bearer-only clients do not use browser cookies and retain their existing write behavior during migration.
- Browser fetches use `credentials: include`. The auth provider checks `/api/auth/me` on startup, never reads or writes the JWT in localStorage, and calls `POST /api/auth/logout` to clear both cookies. Login and logout require an allowed Origin when Origin is present; CORS remains a fixed allow-list with credentials.
- The live WebSocket authenticates via the session cookie and validates Origin against the same allow-list. The browser no longer puts JWTs in a subprotocol. Existing bearer/API and `apexgrid.jwt` WebSocket clients remain temporarily accepted for compatibility; a later removal needs its own contract review.
- Production must run HTTPS for Secure cookies. `APP_ENV=local` may omit Secure solely for the existing HTTP demo and isolated acceptance stack; its weak fallback JWT secret remains confined to local mode.

## Consequences

- The login JSON shape changes; frontend, browser fixtures, acceptance script, and auth characterization tests change in coordinated packets. `/api/auth/logout` and CSRF rejection cases gain tests. The new runtime code can use Python standard-library `hmac`/`secrets`; no new dependency or database migration is required.
- Refresh keeps a browser session until JWT expiry; logout clears cookies client-side. Cross-origin deployment needs the configured allowed origin and credentialed requests. A shared-site deployment with different registrable domains would require `SameSite=None; Secure` and a separate threat review.
- This follows OWASP's signed session-bound double-submit cookie pattern and credentialed CORS guidance: https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html

## Sections affected and proof

- `.agent/ARCHITECT.md` B.3/B.4, G11, R03 and Phase C focused review.
- Test-first packets: cookie flags and login shape; `/me` cookie auth; signed CSRF missing/wrong/valid; logout; WebSocket cookie and Origin; browser reload/login/logout/live; isolated acceptance. Backend and frontend change only after the new security tests reproduce the old behavior. Full suites, zero-skip DB acceptance, and security audit are required before closing G11.
