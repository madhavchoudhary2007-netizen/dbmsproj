# Phase 1 backend audit: A/C/E

Source reviewed at committed `HEAD`; concurrent working-tree edits were excluded.

## Findings

### F-ACE01 — C/E — P2 — Login has no throttling

- **Evidence:** `backend/app/main.py:509-529` performs account lookup and bcrypt verification for each `/api/auth/login` request, with no limiter, lockout, or retry delay in the handler. `backend/app/config.py:1-30` has no rate-limit configuration. Reproduction: submit repeated invalid login requests for one account; each reaches the same 401 response with no throttling response or enforced wait.
- **Affected job:** Sign in to an account when an attacker can repeatedly guess its password.
- **Required fix:** Add an enforced per-account and per-source login attempt limit with a bounded recovery window; cover valid and invalid account names.

## Examined paths with no finding

- **Role checks:** `backend/app/main.py:355-452, 484-505, 539-590, 595-690, 1816-1848, 1999-2045` — CRUD identifiers are fixed by route registration, CRUD writes require ADMIN, and DBMS reads require admin. Values use parameters; DBMS dynamic identifiers use `psycopg.sql.Identifier` after table allowlisting.
- **User-controlled SQL / collection names:** `backend/app/main.py:1816-1848, 2021-2045, 1954-1957` — table names are checked against public tables, collection names against listed collections, filters are constructed from typed query parameters, and explain accepts a `Literal` selecting fixed SQL.
- **Transactional SQL writes:** `backend/app/main.py:374-408, 666-682, 291-298` and `backend/app/database.py:16-22` — connection context commits/rolls back; multi-statement CRUD, result, and reservation writes share a connection transaction. Generated-race creation likewise uses one connection transaction (`main.py:1064-1110`).
- **Input validation:** `backend/app/main.py:181-230, 258-343, 347-353, 595-625, 653-681, 853-873`; `backend/migrations/001_initial.sql:15-38, 46-79, 107-126, 148-189` — typed request models and DB constraints cover the examined user, session, telemetry, membership, and reservation inputs.
- **WebSocket role/origin:** `backend/app/main.py:1734-1753` authenticates a signed JWT against an existing user before accepting. Existing `G11` tests identify the separate cookie-authenticated transport/origin gap; it is not duplicated here. No distinct role or origin defect is established by this committed path.
- **Existing test coverage:** `backend/tests/test_api.py:151-178, 249-285, 878-880, 911-972` covers bearer WebSocket authentication, cookie transport characterization, origin characterization, and Mongo collection allowlisting. `backend/tests/test_database.py:478-535` covers session transition and membership constraints.
