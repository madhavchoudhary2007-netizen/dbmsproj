# NEXT_STATE
updated_at: 2026-10-26
phase: 3 T331 + 7 route redesign; Phases0–2,5–6 COMPLETE; no current score

## Queue
### T-44572 — Extract incident and pit route assembly
- worker: W2 | priority: P1 | origin: T-331 main.py split
- target_files: backend/app/main.py, backend/app/api/operations_routes.py
- read_only_context: docs/overhaul-plan.md (Phase 3 T-331, 314–319); backend/app/main.py (305–356); backend/app/api/stewards.py (82–105, 145–156); backend/app/api/pit_write.py (17–74); backend/app/pit_router.py (1–18)
- contract: Move-only registration of steward, existing pit-read router, and pit-write router. Preserve order, dependency lambdas, router/handler variables, and main aliases for incident and reservation handlers.
- boundaries: No endpoint/API/schema/dependency/test/DB changes; max 150 changed lines; target files only.
- verify: APP_ENV=local .venv/bin/pytest -q backend/tests/test_contract_snapshot.py backend/tests/test_route_registration.py && APP_ENV=local .venv/bin/mypy --strict backend/app && APP_ENV=local .venv/bin/ruff check backend/app && APP_ENV=local .venv/bin/ruff format --check backend/app

## Blocked
- T379 parent final gate: exact split complete, build/static0 and1020/1100mockedPASS; remaining15desktopA3layouts requirePhase7. Body/reducedmotion repaired; never mark fullsuitepassed. Proceed Phase7layouttasks as parentgate repairs, retain fullgate for finalrerun.

## Deferred
- TASTE-382-BLOAT: resource-page.tsx >300lines; split genuine reusable presentation/runtime responsibilities after T382 flow coverage, no single-call fake wrappers.

- TASTE-381-1: four KPIface accents followT381 but exceedT400 max3; consolidate supportingcolourbeforeA5, preserve data/features and thresholds.
- P-3 DBMS: full-route initial-asset measurement is fixed; Live now passes at 161.29 KiB, DBMS remains 260.10 KiB (170 KiB limit). Reduce DBMS initial bundle after Phase 4 and T-393 dependencies; never change the threshold.

## Done
- T-44571 accepteddb57c59; verify0.
- T-44570 acceptedd134e39; verify0.
- T-44569 accepteded947dd; verify0.
- T-44568 acceptedb5f7f0e; verify0.
- T-44567 acceptedb0b12af; verify0.
- T-44566 accepted01edfca; verify0.
- T-389 acceptede5ebfeb; verify0.
- T-44565 accepted669f39e; verify0.
- T-44564 accepted8b064db; verify0.
- T-44563 accepted917fe55; verify0.
- T-44562 accepted19cbe5e; verify0.
- T-44561 accepted640f46a; verify0.
- T-44559 accepted888002c; verify0.
- T-44560 acceptedb1397e6; verify0.
- T-44558 acceptede58928e; verify0.
- T-44557 accepted48d841a; verify0.
- T-44556 acceptedce4189e; verify0.
- T-44555 accepted1f43fcd; verify0.
- T-44554 accepted55f447f; verify0.
- T-44553 accepted800ce8e; verify0.
- T-44552 accepted41c7c3e; verify0.
- T-44551 acceptedc42b3f0; verify0.
- T-44550 accepted9c8841e; verify0.
- T-44549 accepted1cd40f8; verify0.
- T-44548 acceptedf1a5c17; verify0.
- T-44547 accepteddbb62d5; verify0.
- T-44546 accepteda4ef7b6; verify0.
- T-44545 accepted290d2e7; verify0.
- T-44544 acceptedc09bfdd; verify0.
- T-44543 accepted19c41c6; verify0.
- T-44542 accepted1800077; verify0.
- T-44541 accepted95cc69c; verify0.
- T-44540 acceptedf4e0e36; verify0.
- T-44539 acceptede6dfc57; verify0.
- T-44538 accepted8f08922; verify0.
- T-44537 accepted779e680; verify0.
- T-44536 accepted823c270; verify0.
- T-44534 accepted01e561c; verify0.
- T-44533 accepted7c1a7c7; verify0.
- T-44535 accepted09c2730; verify0.
- T-44531 accepted2e88c3d; verify0.
- T-44532 acceptedf92abda; verify0.
- T-44529 accepted82138ba; verify0.
- T-44527 accepted378faa0; verify0.
- T-44530 accepted8e83f3c; verify0.
- T-44528 accepted885b8ac; verify0.
- T-44526 accepted7897a78; verify0.
- T-44525 acceptedb301b9c; verify0.
- T-44524 accepted4666958; verify0.
- T-44522 accepted0935ce7; verify0.
- T-44523 accepted9a68302; verify0.
- T-44520 accepted2e68037; verify0.
- T-44521 accepted3f2d1fc; verify0.
- T-44519 acceptedd868cac; verify0.
- T-44517 accepteddede5cd; verify0.
- T-44516 accepted7023bc4; verify0.
- T-44518 acceptedeffb424; verify0.
- T-44515 accepted51b8121; verify0.
- T-44514 acceptedc48443f; verify0.
- T-44512 acceptedbe6cc11; verify0.
- T-44511 acceptedad39af5; verify0.
- T-44509 accepted1b65d17; verify0.
- T-44510 accepted1d3180f; verify0.
- T-44508 accepted040cb67; verify0.
- T-44505 accepted38165fc; verify0.
- T-44507 acceptedab9660e; verify0.
- T-44506 acceptedc96573a; verify0.
- T-44504 acceptedd13765d; verify0.
- T-44503 accepteda8a1741; verify0.
- T-44502 accepted1d24522; verify0.
- Earlier tasks: Git/.agent/results; parent milestones require full gates.

## Plan dependencies still required
- T387 official records API/source/UI and focused browser/build milestone complete. T388 Pit Wall implementation is accepted; root route/browser/Taste verification pending before T389.
- T385/M13 first chart draw animation remains for T400; actual stream updates remain animation-free. T44560 dynamic chart split verified by production build; Live passes P-3.
