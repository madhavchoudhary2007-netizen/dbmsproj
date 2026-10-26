# NEXT_STATE
updated_at: 2026-10-26
phase: 3 T331 + 7 route redesign; Phases0–2,5–6 COMPLETE; no current score

## Queue
### T-44558 W2 — OPEN
- target_files: backend/app/bootstrap.py, backend/app/core/auth_dependencies.py, backend/app/simulation_pit.py
- contract: Clear five strict typing errors in bootstrap, auth origin dependencies and simulation pit counters, preserving values/contracts.
- verify: env APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_contract_snapshot.py backend/tests/test_request_dependencies.py backend/tests/test_runtime_dependencies.py && .venv/bin/mypy --strict backend/app/bootstrap.py backend/app/core/auth_dependencies.py backend/app/simulation_pit.py && .venv/bin/ruff check backend/app backend/tests && .venv/bin/ruff format --check backend/app/bootstrap.py backend/app/core/auth_dependencies.py backend/app/simulation_pit.py

### T-44557 W1 — OPEN
- target_files: frontend/components/pages/sessions.tsx
- contract: Restore the client boundary required by Sessions after route stopped importing the client compatibility barrel.
- verify: npm --prefix frontend run typecheck && npm --prefix frontend run lint -- --max-warnings 0 && bash scripts/eval/lint-spacing.sh && bash scripts/eval/lint-motion.sh && bash scripts/eval/lint-banned.sh && bash scripts/eval/lint-neobrutal.sh

## Blocked
- T379 parent final gate: exact split complete, build/static0 and1020/1100mockedPASS; remaining15desktopA3layouts requirePhase7. Body/reducedmotion repaired; never mark fullsuitepassed. Proceed Phase7layouttasks as parentgate repairs, retain fullgate for finalrerun.

## Deferred
- TASTE-382-BLOAT: resource-page.tsx >300lines; split genuine reusable presentation/runtime responsibilities after T382 flow coverage, no single-call fake wrappers.

- TASTE-381-1: four KPIface accents followT381 but exceedT400 max3; consolidate supportingcolourbeforeA5, preserve data/features and thresholds.
- T-44132 (W3, before claiming P-3): bundle checker counts only rootMainFiles+page chunk, omitting layout/shared dependency assets; add fixture regression and measure fullinitial asset graph with unchanged170KB threshold.

## Done
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
- T387 official records API/source/UI implemented under ADR013; focused browser milestone/build pending. Then T388 Pit Wall.
- T385/M13 first chart draw animation remains for T400; actual stream updates remain animation-free.
