# CURRENT_STATE
updated_at: 2026-10-26
git_head: b0b12af
branch: overhaul/neo-brutal
architect_sha256: 8e8897b1a90568d13f119a810c986c42201a6603dc6eeeb53ea4953b851f49ca
harness: codex; orchestrator gpt-6.1-sol/medium; workers gpt-6-luna/high, cap2
archetype: Neo-Brutal Motorsport light, approved ADR007
last_eval_score: obsolete 51.2974; no current score; final T430

## Phase status
- Phases 0–2, 5–6 complete (5/12). Phases 3–4 and 7–11 remain. `docs/overhaul-plan.md` is authoritative. User authorized autonomous completion.
- Phase 3: T331 main.py <=120 lines remains; runtime DI/provider/lifespan and module extractions exist. T44565 brought `.venv/bin/mypy --strict backend/app` to exit 0; the three DBMS routers and main application now pass strict mypy.
- Phase 7: T380–389 route work accepted through Standings; T389 root browser gate passed 85/85 across five viewport profiles, including the unchanged desktop palette band. T379 full gate still retains 15 desktop A3 layout failures. Initial route assets: Live passes at 161.29 KiB after T44560; DBMS remains 260.10 KiB against unchanged 170 KiB.
- Phase 4, 8–11 remain, including DBMS showcase, Taste defects, full E2E/performance, CI/docs, final evaluation/release.

## Verified evidence
- Login, Dashboard, Resources, DBMS, Live, Sessions, Stewards and Pit Wall have accepted implementation work; see git commits and `.agent/results/` for task-level records. T44554–57 direct route imports accepted; T44557 restored Sessions client boundary after build failure.
- Production build after T44560 exits 0. Full initial-script bundle gate passes Live at 161.29 KiB and fails DBMS at 260.10 KiB; limit remains 170 KiB. T44560 uses the plan-prescribed dynamic chart import and skeleton fallback.
- Backend: the disposable apexgrid-test full suite and live acceptance passed after T44558 (262 passed, 0 skipped); the full suite and live acceptance passed after T44559 (262 passed, 0 failed, 0 skipped). T44565 acceptance passed strict mypy, contract snapshot and route-registration checks (11 tests).
- T387 focused browser runs total 35 passing cases across five widths; T386–387 build passed. The latest post-fix Live/Pit Wall run passed 100/100 route, state, responsive, touch, accessibility, primary and palette checks across five projects.

## Invariants / workflow
- Locked architecture hash above; verify lock and `source .agent/models.env && bash scripts/agent/boot.sh` before dispatch. Branch only `overhaul/neo-brutal`; accepted changes commit through `accept.sh` integration. Max two packet-only custom workers, gpt-6-luna/high, no overrides. Verify independently; state update after each acceptance; budget every 5 tasks.
- Preserve every route, feature, chart, modal, copy string, aria/data hook, state class and DBMS hash. Five UI states, >=44px targets, allowed spacing/radius/motion, all gates unchanged. Never touch `.env`, real databases/schema/data/volumes, or run recursive removal. Browser/database/network checks are orchestrator-owned; DB stack only guarded disposable `apexgrid-test`.
- No dependencies added; no API/schema changes in current work. Owner's authorized ADR-007/ADR-013 changes remain scoped as recorded.

## Open risks and next work
- T44565 is accepted with behavior-preserving annotations and strict mypy at zero; continue the separate T331 size/split work.
- T389 worker clone could not resolve Next through its external node_modules symlink; root-owned browser rerun passed after a palette repair. Continue browser checks in the root workspace.
- DBMS initial bundle remains above 170 KiB; identify and split its heavy lazy views after required Phase 4/route dependencies. Complete Pit Wall automatic-allocation/history coverage and broader Taste review, then proceed in plan order.
- Main split, strict typing, DBMS showcase, remaining Taste, full browser/performance evidence and final score are not complete. The standings plan requests delta arrows, but driver_standings stores only current rank/points/wins/podiums and the API has no prior-rank field; T389 must not fabricate deltas or change the API. Old 51.2974 is not current; do not present work as done.
- Host Python 3.14/Node 26 differ from Docker 3.12/22; frontend production image lacks source/lint config; acceptance fixture depends on existing championship round 3 (T021 queued).

## Orchestrator direct edits / process notes
- Current continuation has 0 product-code lines edited by orchestrator. Accepted results and hashes are in git/.agent/results; workers may not commit. Earlier review caught fixture/API-shape and numeric serialization regressions and corrected them without weakening checks.

- T-44566 accepted01edfca: Moved create_automatic_reservation into pit_repository.py and imported it in main.py, preserving its signature and behavior. Verify0.

- T-44566 root acceptance: OpenAPI snapshot/route registration 11 passed, strict mypy and Ruff passed. Full backend pytest NOT_RUN because DB URL environment variables are unset; no database was contacted.

- T-44567 acceptedb0b12af: Reduced podium typography to three sizes by matching rank to heading size and the points label to body size; retained the winner card styling and existing weights. Verify0.
- T-44567 root checks: Standings E2E-R11 passed at all five configured viewports; frontend lint and four design lint scripts passed. Taste review confirms three type sizes, two weights, unchanged focal action/palette, and no new bloat.
