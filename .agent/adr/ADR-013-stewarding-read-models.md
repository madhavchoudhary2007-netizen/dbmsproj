# ADR-013 — Read-only stewarding history and licence points
Date: 2026-10-25
Status: Accepted under owner automatic approval for completion of the overhaul

## Context
T-387 requires penalties/sanctions tables and a 12-cell seasonal licence-point meter. Existing incident and driver reads contain neither official penalty history nor seasonal penalty totals. Database tables already hold both. Inferring totals from the currently loaded incident page, treating missing values as zero, or exposing the admin-only DBMS browser to all roles would be incorrect. ADR-001 and the owner's subsequent autonomous-completion instructions permit separately documented finding-backed additive contracts.

## Decision
Add two authenticated read-only endpoints, accessible to the same authenticated roles as existing incident/driver reads. Keep every existing path, method, payload, response and auth rule unchanged. Both use the existing request DatabaseSession and current_user providers, no new dependencies or storage.
- GET /api/stewarding/penalties?limit=50&offset=0 returns an array of {id,incident_id,driver_id,driver_name,session_id,lap,points,time_seconds,grid_places,created_at}. Read official penalties joined to incident, driver and existing user name; order created_at DESC,id DESC. Null driver_name remains null. No report is presented as an official penalty before an actual row exists.
- GET /api/stewarding/licences?season=YYYY&limit=50&offset=0 returns an array of {driver_id,driver_name,licence_number,eligibility,season,points}. Season defaults to the current UTC calendar year and must be 1..9999. Left join penalty_points for that explicit season; points=0 only when the authoritative join has no row. Keep the driver's current eligibility distinct from historical season points. Order drivers.id ASC.
- Both pagination parameters are validated: limit 1..200, offset >=0; defaults 50/0. Invalid queries return standard422. Use bound SQL parameters. Return UTC ISO strings, JSON numeric points, nullable names; no response envelopes or changes to other endpoints.
- UI displays the returned season and true point total; fill at most12 meter cells, retain the actual number in accessible text if it exceeds12. An unavailable source renders an error/partial state, never a fabricated zero. Page through reads with existing bounded list helper; refresh after actual steward decisions and on explicit retry.

## Consequences
The existing database becomes inspectable from the planned stewarding screen without schema migrations or writes. Existing clients continue unchanged. Authenticated read scope matches existing incident/driver information. Seasonal totals require a separate source rather than adding ambiguous fields to the driver contract. New route limits, auth, stable ordering, season selection, zero-vs-unavailable, exact fields and serialization need regression coverage. No real database data or schema is changed.

## Sections affected
ARCHITECT A.2 API-13, B.3 typed read contracts and focused Phase C; T-387 UI dependencies. API acceptance: backend/tests/test_stewarding_reads.py; browser acceptance: stewarding flow/resilience specs, plus route/accessibility/palette gates. Implementation and verification are pending.

## Focused Phase C
Pass1 goal: authenticated stewarding -> official SQL reads -> penalties/history and licence meters, W2 API/state, W1 presentation, W3 tests/root disposable checks. Expert: exact-field/auth/422/pagination/ordering/season/zero tests and unchanged OpenAPI snapshot/full pytest. Taste: two required data regions, no invented totals, no dependencies, actual season label and non-colour meter text. Technical: existing pool/provider, bound parameters, deterministic ordering, UTC season, read-only SELECTs; no runtime globals or migrations. Edge: anonymous401, empty arrays, missing names, no season row0, historical season/current eligibility distinction, >12 points, invalid year/limit/offset, DB unavailable503 path, navigation cancellation and partial recovery. Pass2 all five lenses: zero additional amendments; implementation risks remain unverified.
