# Head Architect protocol (Phases A, B, D)

Read when: starting a project or feature with no locked architecture, or when the user's instruction contradicts a locked one. Phase C is in `lenses.md`.

**Rule:** no product source (the directories in `PRODUCT_DIRS` in `.agent/commands.env`, including scaffold commands) until `.agent/ARCHITECT.md` carries `STATUS: LOCKED`.

## Phase A: discovery

- **A.1 Problem:** who, which job, what outcome.
- **A.2 Deliverables contract:** numbered artifacts (routes, screens, commands, endpoints), each with an acceptance test ID.
- **A.3 Top-1% baseline vs amateur demo:** at least 8 rows. Start from:

| Amateur demo | Top-1% baseline |
|---|---|
| Spinner everywhere | Layout-stable skeletons; CLS ≤ 0.05 |
| Errors in console | User-facing error with cause and a working retry |
| Works at 1440px | Verified at 320, 375, 768, 1440 and 5120 (32:9), per the approved project matrix |
| Mouse only | Full keyboard path, visible focus, screen-reader labels |
| Fetch on every mount | Cached, deduped, stale-while-revalidate |
| Optimistic update, no rollback | Snapshot, optimistic write, rollback on error, retry toast |
| Magic numbers | Every dimension from tokens |
| "Works on my machine" | One-command install, typecheck, lint, test, build green in CI |

- **A.4 Archetype:** classify with `archetypes.md`; record signal counts.
- **A.5 Non-goals:** explicit list.
- **A.6 Unknowns:** if they change the architecture and the user is present, ask at most 4 multiple-choice questions. Otherwise take the most reversible option and record it as an assumption.

## Phase B: system architecture

- **B.1 Stack** with a one-line reason per choice (framework, language version, package manager, styling, state, data, test, deploy).
- **B.2 Module map:** directory tree with the owner worker per directory.
- **B.3 Contracts:** TypeScript types for every cross-module boundary (API request/response, store shape, shared component props). Workers may rely on these without reading other files.
- **B.4 State machines** for every async or multi-step flow:

```ts
type SaveState =
  | { kind: "idle" }
  | { kind: "saving"; requestId: string; snapshot: Draft }
  | { kind: "saved"; at: number }
  | { kind: "error"; error: AppError; snapshot: Draft };
// legal: idle→saving; saving→saved|error; saved→saving|idle; error→saving|idle.
// Anything else throws in dev and is ignored in production.
```

- **B.5 Layout** per screen at 375/768/1440: grid, primary action, content priority order, what collapses or moves.
- **B.6 Data flow** for the three most important user tasks.
- **B.7 Performance budget:** LCP ≤ 2.5s on mid-tier mobile, INP ≤ 200ms, CLS ≤ 0.05, initial JS ≤ 170 KB gzip per route, 60fps (frame ≤ 16.7ms) for animation or simulation.

Then run Phase C (`lenses.md`) before locking.

## Phase D: lock

When Phase C yields zero amendments (or reaches its 3-pass cap), run `bash scripts/agent/lock.sh`. It prepends this banner; the SHA-256 covers everything after `LOCK:END`.

```markdown
<!-- LOCK:BEGIN -->
> STATUS: LOCKED
> SHA256: <64-hex sha256 of the body below>
> LOCKED_AT: <UTC ISO-8601 timestamp>
> LOCKED_BY: orchestrator
<!-- LOCK:END -->
```

`bash scripts/agent/verify-lock.sh` runs at session boot (via `boot.sh`) and before dispatch. Do not repeat full boot per task or call budget again immediately after boot. It fails if the body changed after locking.

**Changing a locked architecture:** write `.agent/adr/ADR-<NNN>-<slug>.md` (Context, Decision, Consequences, sections affected), edit ARCHITECT.md, rerun Phase C on the affected sections only, then regenerate the lock banner and verify it. In this repo lock.sh includes a direct Git commit; reproduce only its canonical banner/hash operation and use accept.sh for the commit, as already recorded by ADR-007. Do not execute its Git tail. A user instruction that contradicts the lock triggers this automatically and wins.
