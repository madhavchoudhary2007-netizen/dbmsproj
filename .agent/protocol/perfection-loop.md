# Perfection loop

Read when: the user starts or resumes the perfection loop. Re-read this whole file after every compaction and at the start of every session. It overrides any summary of it.

Goal: make the existing product correct, secure, accessible, well-structured, fully tested and genuinely useful for its real users. Fix every error. Redesign a feature only when evidence shows it fails a real user journey. Add no unrelated product areas. The user is not available; this file answers the questions you would ask.

This file only adds to AGENTS.md and the other protocol files. Where it names another file, that file is the authority and its rules apply unchanged; nothing here restates them.

## Priorities when rules conflict

1. Guardrails. 2. Honest reporting (never present unfinished work as done). 3. Correctness and security. 4. Code quality. 5. Real-world usefulness. 6. Visual polish.

## Guardrails

- Branch `perfection-loop` only. Never touch `master`, never merge, never force-push, never rewrite history.
- Never read, print, edit or commit `.env` or any secret. Never run recursive removal commands.
- Never modify the running databases or their volumes. Everything that needs databases runs on a disposable stack: a separate compose project (`-p apexgrid-test`) with its own ports and volumes. Check the project name before every `down -v`.
- Schema: additive migrations only, tested on the disposable stack, never dropping or rewriting existing data. Any contract or schema change follows "Changing a locked architecture" in `architect.md`.
- Workers, packets and acceptance: `roles.md` and `packets.md`. Scoring honesty: AGENTS.md rule 4 and `evaluation.md`. State files and compaction: `state-files.md` and `compaction.md`.
- Unrunnable step (Docker down, a model ID fails, missing credential): record it in `.agent/LOOP.md`, continue with everything else, stop only if nothing can progress.

## Decisions already made

- Font family and type scale may change, chosen from the archetype table with a written reason.
- The bearer token moves from localStorage to an httpOnly, Secure, SameSite cookie with CSRF protection, with backend changes and tests.
- Allowed new devDependencies: ruff, mypy, pytest-cov, hypothesis, pip-audit (backend); @playwright/test, @axe-core/playwright, vitest and @testing-library/react (frontend); Lighthouse if it runs here. Runtime dependencies follow the Taste Agent bloat rule in `roles.md`; justify each in CURRENT_STATE.md. You run installs.

## Code quality bar

Measured gates (add the commands to `.agent/commands.env` in Phase 0):
- Backend: `ruff check` (rules E, F, I, B, UP, S, SIM, C90 with max complexity 10) and `ruff format --check`; `mypy --strict` on `backend/app`; pytest with coverage.
- Frontend: `tsc --noEmit` (strict), eslint with zero warnings and no explicit `any`, build.
- Functions at most 60 lines, except generated files (the file-size limit is the Taste Agent's, in `roles.md`).
- Ratchet: record each metric's baseline in LOOP.md (mypy error count, ruff violations, coverage per module, lint hits). A metric may only stay or improve. Targets: 0 mypy errors, 0 ruff violations, coverage of domain and service modules at least 90% lines, overall at least 80%.

Review every accepted diff against this checklist. Each "no" is a new task:
- Names say what things are; no dead or commented-out code; no TODO without a backlog ID.
- Domain logic lives in pure, typed functions; I/O stays at the edges (routers, repositories, hooks).
- Errors are typed and handled at boundaries; users get a cause and a next step.
- SQL is parameterized; every write is in a transaction where it needs one.
- No logic duplicated in three or more places.
- Comments explain why, not what.

## Fix protocol (test first)

1. A W3 task writes a test that reproduces the defect and marks it expected-to-fail behind a switch, so the suite stays green: pytest `@pytest.mark.xfail(strict=True, reason="<finding ID>")`, Playwright `test.fail(!process.env.RUN_XFAIL)`, vitest `it.fails`.
2. The W1 or W2 fix task verifies with the switch on (pytest `--runxfail`, `RUN_XFAIL=1`, or the matching vitest test).
3. On acceptance you remove the marker (a logged orchestrator direct edit) and run the full suite.
A fix with no reproducing test is not accepted. Before any refactor, add characterization tests that pin the current behavior of each API group (status codes and response shapes).

## Domain invariants (property-based tests with hypothesis, plus DB constraints where possible)

- Standings equal the sum of points from classified results after penalties; tie-breaks are deterministic and documented.
- Classification positions are 1..n with no gaps or duplicates per session; DNF, DSQ and penalties are applied by the documented rules.
- Pit reservations never overlap per box (also a Postgres exclusion constraint via an additive migration); cancel and rebook are safe under concurrent requests.
- Session and event state machines accept only legal transitions.
- Telemetry ingestion is idempotent, validated for units and ranges, and ordered per car and lap.
- The simulator is deterministic for a given seed and produces lap times, gaps and pit stops within plausible bounds.
- A permissions-matrix test covers every endpoint and WebSocket for every role with the expected status.
- The DBMS inspection/operation endpoints cannot run arbitrary SQL against product data: read-only or allow-listed, parameterized, role-limited, audited.

## Phases (once, in order), then cycles

- **Phase 0, safety net:** create the branch; the disposable stack (W3, in `scripts/eval/test-stack.sh up|down`); the quality tools and commands above; Playwright config and an E2E smoke test per route; a CI workflow in `.github/workflows/` running every gate; characterization tests; baselines recorded in LOOP.md. No product behavior changes in this phase.
- **Phase 1, correctness and security:** audit areas A, C and E below; fix all P0 and P1 with the fix protocol.
- **Phase 2, structure:** split `backend/app/main.py` into routers, schemas, services (pure domain logic) and repositories, and split oversized frontend files, behavior-preserving, with characterization tests green after every task. The in-memory simulator and event bus must either work correctly with more than one server process or be documented and guarded as single-process (an ADR either way).
- **Phase 3, real-world usefulness:** audit area B. Each redesign is a change proposal `.agent/proposals/CP-nnn.md` (role, job, current behavior and why it fails, new behavior, acceptance tests, contract or schema impact). At most 3 change proposals per cycle, each backed by a failing journey.
- **Phase 3 also covers unclear features:** for every route, endpoint and screen, write one line in `.agent/audit/feature-purpose.md`: who uses it, for what job, and the evidence (a journey that uses it). A feature with no clear user or job is "obscure"; decide one of: **improve** (give it a clear job and finish the journey), **merge** (fold it into the feature that owns that job), or **reposition** (keep it working but move it to an admin or demo area, labelled for what it is). Never delete a feature, endpoint or data; removal is not an option in this loop. Features that exist to demonstrate database concepts (for example the DBMS inspection views, generated or demo races) are kept and made clear and safe, because they may be required by the project's purpose. Each decision is a change proposal and counts toward the 3-per-cycle limit, except reposition-only changes, which do not.
- **Extending is allowed inside an existing capability:** when a role cannot finish a job the product already claims to support (a missing edit, search, filter, export, confirmation, audit trail, or a dead-end screen), add what is missing. New product areas are not allowed.
- **Phase 4, frontend quality:** audit area D.
- **Cycles:** then repeat audit, plan, execute, evaluate and record until DONE or a hard limit.

## Audit areas

- **A. Domain correctness:** standings, points, tie-breaks, penalties, session and event lifecycles, pit reservations, incidents and steward decisions, eligibility and memberships, championship rules, telemetry, simulator, generated races, live timing (reconnect, ordering, staleness, auth).
- **B. Real-world use:** for each route and each role, walk the real journey: create, edit, delete with confirmation, search, filter, sort, pagination, empty states with next steps, bulk actions where they save real work, export, sensible defaults, clear error text, an audit trail of who changed what.
- **C. Backend:** validation on every endpoint, status codes and error shapes, pagination limits, N+1 queries, indexes, transactions, idempotency, concurrency, migrations, health and startup, structured logging, configuration, CORS, rate limiting on login and writes, password rules, JWT expiry and refresh, role checks, WebSocket auth, an API p95 latency test with 10,000 seeded rows on the disposable stack.
- **D. Frontend:** every rule in `design-visual.md` and `design-ux.md`, and the Lens 4 and Lens 5 tables in `lenses.md`, checked on every screen and every viewport.
- **E. Security and supply chain:** OWASP top 10 pass, `npm audit` and `pip-audit` with safe upgrades, secrets never logged, `.env.example` complete with no real values.
- **F. Docs and tooling:** an accurate README, a one-command setup, Dockerfile versions matching the ones actually used, and DECISIONS.md and docs/ matching reality.

Severity: **P0** loses or corrupts data, is a security hole, or blocks a core journey. **P1** gives wrong results or makes a flow unusable for a role. **P2** is a real-world gap or meaningful quality debt. **P3** is minor polish. Every finding needs an ID, area, severity, evidence (file:line or reproduction steps) and the required fix. A finding without evidence is dropped.

## One cycle

1. **Audit:** one W3 worker with a fresh packet holds only the rubric above, the file list and the previous cycle's closed findings, not your conclusions. You audit in parallel. Both try first to break the previous cycle's fixes. Merge the results into `.agent/audit/cycle-N.md`.
2. **Plan:** atomic tasks, P0 first. NEXT_STATE.md holds the next 12 tasks or fewer; the rest go in `.agent/queue.md`. Real findings that cannot be fixed go to `.agent/backlog.md` with a reason.
3. **Execute:** apply the fix protocol, the code-quality review and the Taste Agent after UI merges. A task that fails twice is blocked; try one different approach to the same finding before giving up.
4. **Evaluate:** run `evaluation.md`, including its defect loop. Also start the disposable stack and the app and walk every A.2 deliverable as each role, keyboard only, with screenshots at the five viewports; failures become findings.
5. **Record:** update `.agent/LOOP.md` (cycle, phase, score, findings opened and closed by severity, ratchet metrics, blocked items) and commit.

## DONE (all true, each with evidence in LOOP.md)

- `scripts/eval/score.sh` exits 0 (the presentable condition in `evaluation.md`).
- Two consecutive audits, each with a fresh auditor, with zero P0, zero P1 and no fixable P2.
- Every code-quality gate passes and every ratchet target is met.
- Backend tests have zero failures and zero skips on the disposable stack, and the acceptance script passes there with its own fixture.
- The role-by-role keyboard walkthrough of every A.2 deliverable passes at all five viewports.
- No known high or critical vulnerability that has a fix.
- The CI workflow runs every gate.
- The working tree is clean on `perfection-loop`.

## Hard limits

- At most 8 cycles after the phases. If two cycles in a row end with the same set of failed checks, or cycle 8 ends without DONE, escalate as `evaluation.md` describes and write the final report with Verdict ESCALATED.
- If DONE is reached, stop at once; do not invent work.

## Resume (every new session)

Run "After a compaction" in `compaction.md` (it applies to every new session too), confirm the branch is `perfection-loop`, re-read this file and `.agent/LOOP.md`, and continue from the phase and cycle recorded there.

## Final report (`.agent/FINAL_REPORT.md`; the first line is exactly `Verdict: DONE` or `Verdict: ESCALATED`)

1. Branch and final commit hash, with the commit tagged `perfection-loop-final`.
2. Final score summary: the four dimensions, the aggregate, the hard gates, and NOT_RUN checks with reasons.
3. Cycle table: score and findings opened and closed by severity.
4. Ratchet metrics, baseline against final.
5. Changes grouped by: correctness, security, backend structure, frontend, usefulness (each change proposal, before and after in one line), tests and tooling, docs.
6. Dependencies, ADRs and migrations added.
7. Backlog and known limits, with reasons.
8. Exact commands to run the app, run every gate, review the branch, and merge it.
