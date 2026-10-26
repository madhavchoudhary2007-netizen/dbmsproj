> HISTORICAL AUDIT EVIDENCE ONLY (2026-10-06). Findings/commands below do not establish current verification, authorize mutations or override AGENTS.md/DOC_AUTHORITY.md. Current work is in CURRENT_STATE/NEXT_STATE.

# ApexGrid flow audit — 2026-10-06

## Scope

Reviewed every primary frontend route in the deployed local app, the matching FastAPI read and write paths, PostgreSQL and MongoDB synchronization, and the live demo lifecycle. The review included form behavior, record counts, selectors, archived race access, pit records, incident validation, and keyboard use.

## Findings fixed

| Area | Finding | Change |
|---|---|---|
| Resource pages | Drivers and Users displayed 200 records although the database held over 800; search and related selectors silently missed later pages. | Load all API pages, search the complete set, render 50 rows per page, and show accurate counts. |
| Sessions, stewardship, pit wall, analytics | Shared selectors inherited the 200-row cap. | Load all pages for their source lists. Analytics now supports API offsets and paged results. |
| Live timing | The generated race list and every saved lap could create very large pages. | Show live and five recent races initially; show the latest 100 laps with an explicit full-history control. |
| Race archive | Every-driver lap table rendered all archived rows at once. | Page 100 saved laps at a time while keeping the full comparison data. |
| Pit wall | Five-second pit polling also reloaded entire event, session, team, and driver directories. Repeated names were hard to distinguish. | Poll only pit boxes and reservations; identify events by date and short ID; identify sessions by date. |
| Modal and tables | Selectable table rows had no keyboard action; dialogs did not identify themselves to assistive technology or respond to Escape. | Add row keyboard actions and visible focus, dialog semantics, Escape handling, and focus restoration. |
| Incidents | A generated race accepted an unrelated driver and an incident lap beyond its length. | Validate session laps and generated race entries before storing incidents. |
| Results | Team names on old results were joined to current membership, so a transfer could rewrite historical presentation. | Resolve membership on the race session date. |
| Forms | The Drivers form offered accounts already linked to driver profiles, and a blank optional number became zero. | Hide linked accounts for new profiles and preserve blank optional numeric values. |

## Verification

- All fourteen primary routes rendered without load errors in the local browser.
- PostgreSQL and MongoDB health endpoints reported up.
- Backend tests, API acceptance, frontend typecheck, lint, and production build were run after the changes.
- Deployed browser checks confirmed 984 drivers and 987 users, search finding a driver beyond the old 200-record cap, and resource pagination advancing to page 2.
- The active generated race streamed changing per-driver telemetry in the DBMS race view. Its PostgreSQL demo record remained ACTIVE with auto-repeat enabled after the local Docker restart.
- A completed race showed 12 final results and 744 saved driver laps. The lap archive advanced from page 1 to page 2 of 8 while the comparison view retained per-driver sector and lap times.
- Pit wall displayed the active event and session with date and short ID, four available boxes, and its auto-allocated queue. Analytics returned 21 pages of driver records with working filters and paging.
- The restarted stack had healthy PostgreSQL and MongoDB services, a successful API health response, and no recent backend error log entries.

The local app remains a demo environment. A manual session can be marked ACTIVE without a simulator and therefore show no telemetry; the automatically generated race is separately active and streaming.

## Follow-up implementation deployed and verified

These changes extend the previous reviewed flows and are deployed:

| Area | Current implementation |
|---|---|
| API lifecycle and errors | FastAPI lifespan awaits simulator cancellation before closing database clients. API validation errors use readable response details. |
| Modal and navigation access | Dialogs trap focus and lock body scrolling; SearchBox has an accessible input label and focus cue. Mobile navigation has accessible labels and closes with Escape. |
| Live and analytics requests | Stale-response guards and completion-scheduled polling protect Pit Wall and Live Timing updates. Live Timing loads initial packets from the session snapshot and uses WebSocket for new packets. Completed timing remains visible, manually selected archives stay selected, and lap-record failures show automatic recovery status. Analytics prompts before its first query and ignores stale filter results. |
| Race and DBMS workspace | Selected props synchronize with view state, self-comparison uses identical A/B series and a zero delta, penalties use names, and session states have clearer labels. |
| Local services | All four Compose services use `restart: unless-stopped` so Docker resumes them after a desktop restart unless explicitly stopped. |

## Follow-up verification status

- Configured backend suite: **41 passed** in 52.85 seconds. Frontend lint and typecheck passed. Production backend and frontend images built and deployed. All four containers are running with `restart: unless-stopped`; PostgreSQL and MongoDB health checks pass. `docker compose config --quiet` passed.
- API acceptance passed login, session, simulator, MongoDB, WebSocket, pit conflict, penalty trigger and ban, results, standings, DBMS, and generated-race flows before the final UTC serializer fix. The final fix has focused BSON regression coverage and deployed API/browser proof; acceptance was not rerun after that fix.
- Browser verified modal Tab/Shift+Tab focus trapping, body overflow restoration, Escape close and focus return; 390px mobile navigation Escape behavior; DBMS completed-race self-comparison with matching A/B values and zero delta plus selection persistence after SQL view changes; and manual archive selection across refresh.
- After UTC serialization deployed, Live Timing showed the archived race's 12 cars and 12 named drivers, 768 saved laps, and 100 final samples. The deployed snapshot returned 100 packets with `Z` timestamps. Analytics displayed an initial prompt, a readable 422 season error, recovered to 30 pages of driver results with names, averages, and seconds. Pit Wall showed the selected completed race, four boxes, 33 named automatic stops, and a disabled start control.
