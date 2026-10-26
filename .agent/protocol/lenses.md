# Phase C: five-lens stress test

Project routing (ADR-014): use the approved overhaul-plan.md section 2 and locked ADR-007 for project-specific visual/layout rules; examples here are generic. Preserve all existing numeric quality gates. Read only the relevant sections for the current packet. Verification cadence is delivery-workflow.md.

Read when: running Phase C of the architect protocol. Run each lens against Phase A+B. Every finding amends the document or is rejected with a written reason. Repeat all five lenses until a full pass produces zero amendments; maximum 3 passes, then list what remains under a "Risks" heading at the end of ARCHITECT.md and proceed to the lock.

## Lens 1: goal achievement

For each A.2 deliverable trace cold start to success and list every prerequisite (env vars, seed data, auth, migrations, accounts). A prerequisite with no owner task is a defect. Output a table: `Deliverable | Steps | Prerequisites | Owner task | Test ID`. Any B.2 module that serves no deliverable is removed (drift).

## Lens 2: expert output and concrete verification tests

Every acceptance criterion is an executable command with a binary result. Banned wording in criteria: "works", "looks good", "handles errors", "is fast". Use the commands in `.agent/commands.env`:

Use the project's exact commands from .agent/commands.env and existing test-runner configuration. Do not append pnpm/Vitest reporter flags to pytest or create a second test setup. Record zero errors/warnings, collected/passed/skipped counts and scoped evidence under delivery-workflow.md.

Use existing deterministic stepping/time controls for animation/simulation tests; these generic pseudocode examples are not a mandate for a second loop/invariant framework or import.meta.env in Next.js. Do not copy them into a packet unless appropriate to that runtime:

```ts
export function createLoop(step: (dt: number) => void, fixedDt = 1 / 120) {
  let acc = 0, last = -1;
  const MAX_FRAME = 0.1; // delta clamp
  return { tick(nowMs: number) {
    if (last < 0) { last = nowMs; return; }
    acc += Math.min((nowMs - last) / 1000, MAX_FRAME); last = nowMs;
    let n = 0;
    while (acc >= fixedDt && n < 8) { step(fixedDt); acc -= fixedDt; n++; }
    if (n === 8) acc = 0; // spiral-of-death guard
  } };
}
// tests: tick(0); tick(5000) calls step at most 8 times; identical tick sequences give identical results.
```

Invariants run in tests and development builds:

```ts
export function invariant(cond: unknown, msg: string): asserts cond {
  if (!cond) {
    if (import.meta.env?.DEV) throw new Error(`Invariant failed: ${msg}`);
    console.error(`Invariant failed: ${msg}`);
  }
}
```

## Lens 3: tasteful implementation and restraint

The Taste Agent (`roles.md`) answers yes or no; each "no" becomes an amendment.

1. Does each screen have exactly one primary action?
2. Approved cream/paper/red roles within unchanged A-3 bands, with at most three semantic accents under ADR-007?
3. Is each abstraction justified by reuse or an explicit correctness/domain boundary? Record a single-call-site Taste finding unless the documented boundary justifies it; do not add fake callers.
4. Does every dependency save more than 30 lines or address correctness (dates, crypto, accessibility primitives)?
5. Does decoration follow the approved motifs, texture backing and reduced-motion rules? Reject unapproved glow/glass/emoji; do not delete approved art or a working feature merely to satisfy a generic example.

## Lens 4: anticipated difficulties and technical mitigations

For each hard area the project touches record the failure mode, the formula and the guardrail. Use these rows where they apply and add project-specific ones.

| Area | Formula / rule | Guardrail |
|---|---|---|
| Explicit PDE advection | Courant number `C = abs(u)·Δt/Δx ≤ 1`; multi-D: `Δt·Σᵢ(abs(uᵢ)/Δxᵢ) ≤ C_max` | `Δt = 0.9·C_max / Σᵢ(max_abs(uᵢ)/Δxᵢ)` each step; assert `C ≤ C_max` in dev |
| Explicit diffusion | `Δt ≤ Δx² / (2·d·α)` for d dimensions, diffusivity α | Sub-step `n = ceil(Δt_frame / Δt_max)` |
| Collision tunneling | Tunnels when `abs(v)·Δt > t_min` (thinnest collider) | Sub-steps `n = ceil(abs(v)·Δt / (0.5·t_min))`, capped at 16; above the cap use swept (continuous) collision by segment cast from previous to current position |
| Transparency depth sorting | Sort transparent draws by view-space depth, far to near, every frame | Opaque pass first with depth write; transparent pass with `depthWrite=false`, sorted; intersecting objects use weighted blended order-independent transparency |
| Render-loop GC | Steady-state allocations per frame = 0 | Preallocate and pool; no closures, spreads, `map` or template strings inside rAF callbacks; verify heap growth under 1 MB over 600 frames (`performance.memory`) |
| Floating-point drift | Semi-implicit (symplectic) Euler: `v += a·Δt; x += v·Δt` | Fixed timestep (Lens 2 loop) |
| Long lists | DOM nodes proportional to visible rows | Virtualize above 200 items |
| Concurrent requests | Last request wins | `AbortController` per query key; drop responses whose `requestId` is not current |
| Money | No binary floats | Integer minor units end to end |
| Time zones | Store UTC, render in the user's zone | `Intl.DateTimeFormat` with explicit `timeZone` |

## Lens 5: edge cases and boundary guardrails

Each row needs a code guardrail and an automated test.

| Edge case | Guardrail | Test |
|---|---|---|
| Delta-t spike on tab switch or sleep | `dt = min((now - last)/1000, 0.1)`; pause when `visibilityState === "hidden"` | tick(0), tick(5000) gives at most 8 steps |
| Boundary grazing | Inside means `min ≤ x < max`; float compare with ε `1e-9` scaled by magnitude | points at `min`, `max`, `max-ε`, `min-ε` |
| Conflicting simultaneous states | State machine rejects illegal transitions (B.4) | fire `saved` while `idle`: state unchanged |
| Rapid input spam | Disable submit while saving; idempotency key per action; debounce search 250ms; throttle scroll to rAF | click submit 20 times in 1s: exactly 1 request |
| Navigation mid-request | Abort in-flight requests on route change | navigate away: no errors, no state update after unmount |
| Offline then online | Refetch on reconnect; mutations show error and retry | `context.setOffline(true/false)`, retry succeeds |
| Empty or huge data | Empty state; virtualize; truncate with title | fixtures with 0 and 10,000 rows |
| Extreme widths | Fluid from 320px; max-width on ultra-wide | 320×568 and 5120×1440 (32:9): no horizontal overflow |
| Long unbroken strings | `overflow-wrap: anywhere`; `min-w-0` on flex children | 120-character string without spaces |
| RTL | Logical properties (`margin-inline-start`) | snapshot with `dir="rtl"` |
