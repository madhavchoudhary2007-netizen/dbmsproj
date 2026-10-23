# E-1 Route-by-Route Applicability Matrix

This matrix defines the authoritative contract for which of the five UI states (`empty`, `loading`, `populated`, `error`, `partial`) apply to each route in ApexGrid, resolving the blocker on T-006.

| Route | Primary Component | Loading | Populated | Error | Empty | Partial | Rationale & Applicable Visual Elements |
|---|---|:---:|:---:|:---:|:---:|:---:|---|
| `/` | `app/page.tsx` (redirect) | Yes | Yes | — | — | — | Redirect landing. Renders "Checking session…" then transitions to `/dashboard` or `/login`. No collection to be empty or filtered. |
| `/login` | `login/page.tsx` | Yes | Yes | Yes | — | — | Authentication form. Renders "Authenticating…" busy state, populated input fields, and `.form-error` alert on invalid credentials. No list to be empty or partially filtered. |
| `/dashboard` | `Dashboard` (`special-pages.tsx`) | Yes | Yes | Yes | — | — | KPI aggregate overview. Renders `<StateMessage loading />`, populated metric cards, and `<StateMessage error />` with retry button. Fixed KPI cards, no search filter. |
| `/live` | `LiveTiming` (`special-pages.tsx`) | Yes | Yes | Yes | Yes | — | Live telemetry & timing. Shows demo race creation busy state, live timing rows, error notice, and empty state (`StateMessage empty="Waiting for timing and telemetry packets from this session."`). |
| `/sessions` | `SessionsView` (`special-pages.tsx`) | Yes | Yes | Yes | Yes | — | Session lifecycle & results. Shows loading spinner, session results table, error alert with retry, and empty state (`StateMessage empty="No result rows are recorded for this session."`). |
| `/stewards` | `StewardsDesk` (`special-pages.tsx`) | Yes | Yes | Yes | Yes | — | Incidents review desk. Shows loading spinner, incident review cards, error alert with retry, and empty state when 0 incidents exist. |
| `/pit-wall` | `PitWall` (`special-pages.tsx`) | Yes | Yes | Yes | Yes | — | Pit strategy & box allocation. Shows loading spinner, box allocation cards, error alert with retry, and record count with empty notice. |
| `/championships` | `ResourcePage` (`resource-page.tsx`) | Yes | Yes | Yes | Yes | Yes | CRUD resource collection. Full 5 states: `<StateMessage loading />`, populated `<DataTable>`, `<StateMessage error />` with retry, empty state when API returns empty array, and partial state when search filter matches subset of records. |
| `/events` | `ResourcePage` (`resource-page.tsx`) | Yes | Yes | Yes | Yes | Yes | CRUD resource collection. Full 5 states supported. |
| `/circuits` | `ResourcePage` (`resource-page.tsx`) | Yes | Yes | Yes | Yes | Yes | CRUD resource collection. Full 5 states supported. |
| `/standings` | `StandingsView` (`standings/page.tsx`) | Yes | Yes | Yes | Yes | — | Championship standings table. Shows loading spinner, driver standings table, error alert with retry, and empty state when no results exist. |
| `/teams` | `ResourcePage` (`resource-page.tsx`) | Yes | Yes | Yes | Yes | Yes | CRUD resource collection. Full 5 states supported. |
| `/drivers` | `ResourcePage` (`resource-page.tsx`) | Yes | Yes | Yes | Yes | Yes | CRUD resource collection. Full 5 states supported. |
| `/users` | `ResourcePage` (`resource-page.tsx`) | Yes | Yes | Yes | Yes | Yes | CRUD resource collection. Full 5 states supported. |
| `/analytics` | `Analytics` (`special-pages.tsx`) | Yes | Yes | Yes | — | — | Filterable driver analytics. Shows loading spinner, populated analytics cards, and error notice on failure. |
| `/dbms` | `DbmsCenter` (`dbms-workspace.tsx`) | Yes | Yes | Yes | Yes | — | DBMS operations workspace. Shows loading spinner, populated SQL/Mongo tables, error alert, and empty table state ("No rows returned"). |

## Summary
- **Universal States (all data components):** Loading, Populated, Error.
- **Collection Empty States:** Supported on `/live`, `/sessions`, `/stewards`, `/pit-wall`, `/championships`, `/events`, `/circuits`, `/standings`, `/teams`, `/drivers`, `/users`, and `/dbms`.
- **Partial Filter States:** Supported on all filterable CRUD resource routes: `/championships`, `/events`, `/circuits`, `/teams`, `/drivers`, and `/users`.
