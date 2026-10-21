# Evaluation and the autonomous quality loop

Read when: a milestone's tasks are all VERIFIED, before presenting anything to the user, and whenever a score or defect loop is involved.

## Dispatch

Send one W3 packet per dimension (four), at most 2 running at once; start the next when one returns. Each writes `.agent/eval/<dimension>.json` (`functional`, `aesthetic`, `performance`, `edge`):

```json
{ "checks": [{ "id": "F-1", "weight": 3, "passed": true, "detail": "tsc exit 0" }] }
```

`passed` is `true`, `false`, or `null` (NOT_RUN, see below). The orchestrator scores A-5 and A-6 itself in Taste Agent mode because they need architecture context workers do not have. Dimension score = 100 × passed weight ÷ weight of the checks that ran.

## Rubric

| Dimension (weight) | Checks (check weight) |
|---|---|
| **Functional (30%)** | F-1 typecheck exit 0 (3) · F-2 lint with zero warnings (2) · F-3 all unit tests pass (4) · F-4 every A.2 acceptance test passes in E2E (6) · F-5 production build succeeds (3) · F-6 no console errors or unhandled rejections in E2E (2) |
| **Aesthetic (25%)** | A-1 `lint-spacing.sh` clean (2) · A-2 `lint-banned.sh` clean (2) · A-3 60-30-10 passes on every route at 1440 (2) · A-4 one `data-primary` per viewport per route (2) · A-5 no high-severity TASTE defects (3) · A-6 no single-call-site abstraction or unjustified dependency (2) · A-7 `lint-motion.sh` clean and the `reducedMotion: "reduce"` E2E passes (2) |
| **Performance & Invariants (25%)** | P-1 Lighthouse mobile score ≥ 90 per route (3) · P-2 LCP ≤ 2.5s, CLS ≤ 0.05, TBT ≤ 200ms (3) · P-3 initial JS ≤ 170 KB gzip per route (2) · P-4 every CURRENT_STATE invariant holds (3) · P-5 animated scenes: p95 frame ≤ 16.7ms over 600 frames and heap growth under 1 MB (2) · P-6 axe finds zero violations at every viewport (2) |
| **Edge-Case Resilience (20%)** | E-1 five UI states render for every data component (3) · E-2 every Lens 5 test passes (4) · E-3 no horizontal overflow at 320 and 32:9 (2) · E-4 input spam gives one request per action (2) · E-5 offline-to-online recovery passes (2) |

`aggregate = 0.30·Functional + 0.25·Aesthetic + 0.25·Performance + 0.20·Edge`

**Hard gates**, which block delivery whatever the aggregate: F-1, F-3, F-4, F-5, P-6. A hard gate that is `false` or `null` fails.

**Present only if the aggregate is ≥ 95 and no hard gate failed.**

## NOT_RUN

Use `passed: null` with `detail: "NOT_RUN: <missing tool>"` only when a check's tool cannot run in this environment (for example no Lighthouse or no browser in a sandbox). Never use it for a check that ran and failed. NOT_RUN checks are left out of the dimension denominator but are listed in `score.json` under `not_run`, and the orchestrator MUST list them to the user when presenting so they can be run elsewhere. A NOT_RUN hard gate always fails.

## Scoring

```bash
bash scripts/eval/score.sh        # writes .agent/eval/score.json; exit 0 only when presentable
```

## Defect loop

```
iteration = 0
loop:
  run the evaluation, then score.sh
  presentable: present and stop
  iteration += 1; iteration > 5: escalate and stop
  for each failed check (hard gates first, then by weight descending):
      enqueue an atomic task in NEXT_STATE.md with origin "EVAL <timestamp>, <check id>"
  failed-check set identical to the previous iteration: escalate and stop
  dispatch the queue, accept envelopes (packets.md), commit, repeat
```

**Escalation:** stop dispatching. Give the user `score.json`, every failing check with its evidence, what was tried for each, and the two most plausible ways forward. Never present an escalated build as finished. Never relax a threshold, delete a test or mark a check passed to exit the loop.
