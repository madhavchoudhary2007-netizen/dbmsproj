# CURRENT_STATE
updated_at: 2026-10-26
git_head: 19cbe5e
branch: overhaul/neo-brutal
architect_sha256: 8e8897b1a90568d13f119a810c986c42201a6603dc6eeeb53ea4953b851f49ca
harness: codex; orchestrator gpt-6.1-sol/medium; workers gpt-6-luna/high, cap2
archetype: Neo-Brutal Motorsport light, approved ADR007
last_eval_score: obsolete 51.2974; no current score; final T430

## Phase status
- Phases 0–2, 5–6 complete (5/12). Phases 3–4 and 7–11 remain. `docs/overhaul-plan.md` is authoritative. User authorized autonomous completion.
- Phase 3: T331 main.py <=120 lines and strict typing unfinished. Runtime DI/provider/lifespan and module extractions exist; strict mypy is 56 errors/4 files after T44561 (latest full run; remaining files: `main.py`, `api/dbms_mongo.py`, `api/dbms_lock.py`, `api/race_archive.py`).
- Phase 7: T380–388 route work accepted through Pit Wall; T379 full gate retains 15 desktop A3 layout failures. A route-focused palette run now reports 153 passing and 2 failing checks: Live paper share 42.69% (>40%) and red 4.96% (<5%); Pit Wall red 3.94% (<5%). Initial route assets: Live passes at 161.29 KiB after T44560; DBMS remains 260.10 KiB against unchanged 170 KiB.
- Phase 4, 8–11 remain, including DBMS showcase, Taste defects, full E2E/performance, CI/docs, final evaluation/release.

## Verified evidence
- Login, Dashboard, Resources, DBMS, Live, Sessions, Stewards and Pit Wall have accepted implementation work; see git commits and `.agent/results/` for task-level records. T44554–57 direct route imports accepted; T44557 restored Sessions client boundary after build failure.
- Production build after T44560 exits 0. Full initial-script bundle gate passes Live at 161.29 KiB and fails DBMS at 260.10 KiB; limit remains 170 KiB. T44560 uses the plan-prescribed dynamic chart import and skeleton fallback.
- Backend: the disposable apexgrid-test full suite and live acceptance passed after T44558 (262 passed, 0 skipped); the full suite and live acceptance passed after T44559 (262 passed, 0 failed, 0 skipped). T44561 is annotation-only; latest strict count is 56 errors across 4 files.
- T387 focused browser runs total 35 passing cases across five widths; T386–387 build passed. The latest Live/Pit Wall focused browser run passed 153 and failed 2 only on palette shares; all responsive, touch, primary, accessibility and live data-flow assertions in that run passed.

## Invariants / workflow
- Locked architecture hash above; verify lock and `source .agent/models.env && bash scripts/agent/boot.sh` before dispatch. Branch only `overhaul/neo-brutal`; accepted changes commit through `accept.sh` integration. Max two packet-only custom workers, gpt-6-luna/high, no overrides. Verify independently; state update after each acceptance; budget every 5 tasks.
- Preserve every route, feature, chart, modal, copy string, aria/data hook, state class and DBMS hash. Five UI states, >=44px targets, allowed spacing/radius/motion, all gates unchanged. Never touch `.env`, real databases/schema/data/volumes, or run recursive removal. Browser/database/network checks are orchestrator-owned; DB stack only guarded disposable `apexgrid-test`.
- No dependencies added; no API/schema changes in current work. Owner's authorized ADR-007/ADR-013 changes remain scoped as recorded.

## Open risks and next work
- T44561 onward: continue reducing the remaining strict mypy errors in small module groups.
- DBMS initial bundle remains above 170 KiB; identify and split its heavy lazy views after required Phase 4/route dependencies. Fix the two measured palette shares in route layouts, then rerun palette and route checks. Complete Pit Wall browser/Taste coverage, then proceed in plan order.
- Main split, strict typing, DBMS showcase, remaining Taste, full browser/performance evidence and final score are not complete. Old 51.2974 is not current; do not present work as done.
- Host Python 3.14/Node 26 differ from Docker 3.12/22; frontend production image lacks source/lint config; acceptance fixture depends on existing championship round 3 (T021 queued).

## Orchestrator direct edits / process notes
- Current continuation has 0 product-code lines edited by orchestrator. Accepted results and hashes are in git/.agent/results; workers may not commit. Earlier review caught fixture/API-shape and numeric serialization regressions and corrected them without weakening checks.

- T-44558 acceptede58928e: Annotated bootstrap.main, typed MongoClient with dict[str, object], converted revocation results to bool, and narrowed car numbers before int conversion while retaining the default and string-number support. Verify0.

- T-44560 acceptedb1397e6: Lazy-loaded TelemetryCharts with next/dynamic, ssr:false, and NbSkeleton chart fallback; chart props and call site are unchanged. Verify0.

- T-44559 accepted888002c: Added strict parameter and return annotations to the user, simulation, and WebSocket route handlers. Preserved route behavior and dependency defaults. Verify0.

- T-44561 accepted640f46a: Added parameter and return annotations to lap measurement and route handlers; preserved route behavior. Formatted both files. Verify0.

- T-44562 accepted19cbe5e: Kept the LIVE DEMO hero yellow. Applied cream and a named red token to the existing generated-sessions card with a 4px top border. Verify0.
