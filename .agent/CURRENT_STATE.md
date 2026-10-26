# CURRENT_STATE
updated_at: 2026-10-26
git_head: b1397e6
branch: overhaul/neo-brutal
architect_sha256: 8e8897b1a90568d13f119a810c986c42201a6603dc6eeeb53ea4953b851f49ca
harness: codex; orchestrator gpt-6.1-sol/medium; workers gpt-6-luna/high, cap2
archetype: Neo-Brutal Motorsport light, approved ADR007
last_eval_score: obsolete 51.2974; no current score; final T430

## Phase status
- Phases 0–2, 5–6 complete (5/12). Phases 3–4 and 7–11 remain. `docs/overhaul-plan.md` is authoritative. User authorized autonomous completion.
- Phase 3: T331 main.py <=120 lines and strict typing unfinished. Runtime DI/provider/lifespan and module extractions exist; strict mypy baseline 87 errors/12 files before T44558.
- Phase 7: route work through Pit Wall; T379 full gate remains 15 desktop A3 layout failures. T380–387 route flows and most browser evidence completed. T388 header/modal/strategy/grid/queue changes accepted; DBMS and Live full initial route bundles exceed unchanged 170 KiB gate (260.01 and 263.84 KiB).
- Phase 4, 8–11 remain, including DBMS showcase, Taste defects, full E2E/performance, CI/docs, final evaluation/release.

## Verified evidence
- Login, Dashboard, Resources, DBMS, Live, Sessions, Stewards and Pit Wall have accepted implementation work; see git commits and `.agent/results/` for task-level records. T44554–57 direct route imports accepted; T44557 restored Sessions client boundary after build failure.
- Latest corrected production build exits 0. Bundle gate correctly measures initial script/preload assets and fails only DBMS and Live. Recharts is present in each route's shared initial graph; optimize without changing gate or removing features.
- Backend: full suite 262 passed, 0 skipped, live acceptance passed at T44552. T44558 W2 changes are isolated and await integration: bootstrap/auth dependency/simulation pit typing only. Previous strict baseline 87 errors/12 files.
- T387 focused browser runs total 35 passing cases across five widths; T386–387 build passed. Pit Wall browser milestone still needs verification.

## Invariants / workflow
- Locked architecture hash above; verify lock and `source .agent/models.env && bash scripts/agent/boot.sh` before dispatch. Branch only `overhaul/neo-brutal`; accepted changes commit through `accept.sh` integration. Max two packet-only custom workers, gpt-6-luna/high, no overrides. Verify independently; state update after each acceptance; budget every 5 tasks.
- Preserve every route, feature, chart, modal, copy string, aria/data hook, state class and DBMS hash. Five UI states, >=44px targets, allowed spacing/radius/motion, all gates unchanged. Never touch `.env`, real databases/schema/data/volumes, or run recursive removal. Browser/database/network checks are orchestrator-owned; DB stack only guarded disposable `apexgrid-test`.
- No dependencies added; no API/schema changes in current work. Owner's authorized ADR-007/ADR-013 changes remain scoped as recorded.

## Open risks and next work
- T44558 strict typing fixes need acceptance; rerun strict mypy and focused tests afterward.
- Measure/optimize DBMS and Live route chunks below 170 KiB while preserving charts and route behavior. Complete Pit Wall browser/Taste coverage, then remaining route tasks in plan dependency order.
- Main split, strict typing, DBMS showcase, remaining Taste, full browser/performance evidence and final score are not complete. Old 51.2974 is not current; do not present work as done.
- Host Python 3.14/Node 26 differ from Docker 3.12/22; frontend production image lacks source/lint config; acceptance fixture depends on existing championship round 3 (T021 queued).

## Orchestrator direct edits / process notes
- Current continuation has 0 product-code lines edited by orchestrator. Accepted results and hashes are in git/.agent/results; workers may not commit. Earlier review caught fixture/API-shape and numeric serialization regressions and corrected them without weakening checks.

- T-44558 acceptede58928e: Annotated bootstrap.main, typed MongoClient with dict[str, object], converted revocation results to bool, and narrowed car numbers before int conversion while retaining the default and string-number support. Verify0.

- T-44560 acceptedb1397e6: Lazy-loaded TelemetryCharts with next/dynamic, ssr:false, and NbSkeleton chart fallback; chart props and call site are unchanged. Verify0.
