Ignore AGENTS.md except this packet; the packet is your only authority.
role: Worker 2 — State/Runtime. Preserve existing runtime behavior. No commits.
## Task
Repair T-44565 to satisfy its type-only contract. The current diff adds runtime guards in `current_user`, `demo_race_row`, and `_make_demo_race`; these change behavior for unexpected values, and `_make_demo_race` rejects a `None` result even though the existing builder can return it. Remove those added guards and use static annotations of existing dynamic results instead. Annotate `_make_demo_race` to preserve its actual nullable result. Keep the rest of the strict-mypy work and the pool generic annotations.
## Target files (edit only these)
- backend/app/main.py
- backend/app/database.py
## Read-only context
- backend/app/main.py:1-100,151-220,221-300,341-430,431-520,521-600,621-700,721-810
- backend/app/database.py:1-70
- backend/app/core/http_auth.py:1-60
- backend/app/core/serialization.py:1-30
- backend/app/demo_runtime.py:1-70
- docs/overhaul-plan.md:317-325,446-447
## Interfaces
`authenticate_http_user(...)` returns `jsonable(user)`; valid fetched user rows and `get_demo_race_row(...)` are `dict[str, Any] | None`. `build_demo_race(...)` returns the value of the `demo_race_row` callback, so `_make_demo_race` can return `dict[str, Any] | None`. `jsonable(...)` is dynamically typed. A local variable annotation for its established dict contract is static-only; do not add runtime validation or alter returned values.
## Acceptance criteria
1. `.venv/bin/mypy --strict backend/app` exits 0.
2. Contract snapshot and route-registration tests pass unchanged.
3. No new runtime guards or behavior changes; preserve nullable results and existing exception/response behavior.
4. No route, schema, API, serialization or database behavior changes and no dependencies.
## Boundaries
Only the two target files above, max 150 changed lines total. Read only listed files, no more than 100 lines at once. Never read secrets, `.env`, or database contents; no real database/schema/data/volume writes, network, fixed-port server, recursive removal, casts, ignores, broad `Any` additions, API changes, or test changes. Preserve other work. No commits.
## Verify (exit 0 required for PASSED)
.venv/bin/mypy --strict backend/app && env APP_ENV=local PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_contract_snapshot.py backend/tests/test_route_registration.py && .venv/bin/ruff check backend/app/main.py && .venv/bin/ruff format --check backend/app/main.py
## Output
Return only one JSON envelope matching `.agent/envelope.schema.json`: task_id `T-44565`, status PASSED|FAILED, files_modified, diff_summary, verification, unresolved_blockers. Use the exact Verify command above and report only observed counts.
