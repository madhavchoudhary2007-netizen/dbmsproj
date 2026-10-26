# ApexGrid Neo-Brutal Overhaul — Implementation Plan

Status: IN PROGRESS; implementation PAUSED by owner on 2026-10-26 until start work. The baseline below is historical; current evidence is in .agent/CURRENT_STATE.md.
Audience: the orchestrator model (GPT-6.1 Sol medium in Codex CLI, Sonnet 5.5 medium in Claude Code, or Gemini 3.8 Flash high thinking in Gemini CLI / Antigravity) and the W1/W2/W3 workers it dispatches.
Base branch: `perfection-loop` (HEAD `1acf8e1`). Work branch: `overhaul/neo-brutal`.
First task ID: `T-300` (T-001..T-213 are taken).

Read `AGENTS.md` first. Owner chat instructions take precedence. ADR-014 and `.agent/protocol/delivery-workflow.md` own task sizing, verification cadence and resume behavior; this plan owns product scope/design and the twelve phase requirements. `.agent/NEXT_STATE.md` is the active queue. Do not restart accepted phases or the historical setup below.

---

## 0. Ground truth before starting (measured 2026-10-23, not the claims in `FINAL_REPORT.md`)

`FINAL_REPORT.md` reports 100%. These commands disagree, and this plan starts from them:

| Check | Real result | Owner phase |
|---|---|---|
| `ruff check backend/app backend/tests` | 540 errors | Phase 1 |
| `ruff format --check` | 23 files would be reformatted | Phase 1 |
| `mypy --strict backend/app` | 222 errors | Phase 1 (baseline) → Phase 3 (zero) |
| `npm --prefix frontend run lint -- --max-warnings 0` | 2 errors (`any` in `e2e/perf-fps.spec.ts`) | Phase 1 |
| `npm --prefix frontend audit --audit-level=high` | 7 high, 2 moderate (Tailwind 3 chain, eslint-config-next) | Phase 5 (Tailwind 4) + Phase 1 |
| CI | runs only on `perfection-loop` push; no PR trigger; no `main` branch (`master` + `perfection-loop`) | Phase 1 |
| E2E | every spec mocks the API with `page.route` and runs against `next dev` | Phase 10 |

Rule for every phase: a check is passing only at exit 0 with tests collected. Database tests that skip do not count.

---

## 1. Goal and non-negotiables

Goal: rebuild the ApexGrid frontend in a light neo-brutal motorsport style, and harden and optimise the backend, without losing any working feature, route, API, copy string, test hook, animation, chart or state.

Non-negotiables (every packet repeats the ones that apply):

1. **No API break.** Every route in `docs/contracts.md` and `docs/api.md` keeps its path, method, request and response shape. New fields and routes are additive only, with one ADR per contract change (ADR-001 rule).
2. **No data loss.** Migrations are additive. Historical races, telemetry and penalties remain readable. Run migrations only on the disposable stack (`scripts/eval/test-stack.sh`) until accepted.
3. **Preserve test contracts in the UI.** Keep:
   - every existing visible copy string that a spec asserts (search `frontend/e2e/*.spec.ts` before renaming any text);
   - `data-*` attributes, ARIA roles and accessible names;
   - `.state.error` and the other state classes the specs select on;
   - exactly one `data-primary` per viewport per route;
   - hash routes on `/dbms`.
4. **Every data component renders 5 states:** empty, loading, populated, error, partial.
5. **Spacing scale only:** 0/4/8/12/16/24/32/48/64px. Targets ≥ 44×44px. WCAG AA. Reduced motion honoured everywhere.
6. **Gates are never relaxed.** Re-baselining for the new archetype (Phase 0) is allowed only through ADR-007 with owner approval, and only by swapping dark values for light values of equal strictness.
7. **Never more than 2 workers at once.**

---

## 2. Design system: "Neo-Brutal Motorsport (light)"

### 2.1 Colour tokens

| Token | Hex | Use | Contrast note |
|---|---|---|---|
| `--nb-cream` | `#FFFDF5` | page background (dominant role) | black on cream ≈ 20:1 |
| `--nb-paper` | `#FFFFFF` | cards, tables, inputs (secondary role) | |
| `--nb-ink` | `#000000` | text, borders, hard shadows | |
| `--nb-red` | `#FF6B6B` | primary action, LIVE, danger, red flag, soft tyre (accent role) | black on red ≈ 7.6:1. **Never white text on red** (≈ 2.8:1, fails AA). |
| `--nb-yellow` | `#FFD93D` | active nav, highlights, warnings, yellow flag, medium tyre, caution tape | black on yellow ≈ 15:1 |
| `--nb-violet` | `#C4B5FD` | tertiary blocks; "overall fastest" sector/lap (F1 purple convention) | black on violet ≈ 11:1 |
| `--nb-mint` | `#7CF5B0` | green flag, healthy, personal best, intermediate tyre (domain addition, justified in ADR-007) | black on mint ≈ 16:1 |
| `--nb-sky` | `#7CC4FF` | **data only**: wet tyre and second chart series | |

Tyre compound mapping: soft = red, medium = yellow, hard = paper with ink border, intermediate = mint, wet = sky. Each compound badge also shows its letter (S/M/H/I/W), so colour is never the only signal.

Banned: grays (`gray|slate|zinc|neutral|stone` utilities, any `#xxxxxx` with R=G=B other than 000/FFF), blur, gradients outside textures, mid-range radius.

### 2.2 Gate-safe palette roles (A-3)

`scripts/eval/palette.ts` assigns each pixel to its nearest role. A pixel is counted only when its squared distance to that role is ≤ 900, and shares are computed among counted pixels only.

- Roles string: `"#FFFDF5,#FFFFFF,#FF6B6B"`. Cream and white are distance² 104 apart, but nearest-role assignment still separates them.
- Ink, yellow, violet, mint and sky are excluded automatically (all are more than 30 away from every role).
- **Design targets at 1440px:** cream 55–65%, white 25–35%, red 7–12%.
  - Main red pixel source: the race-control marquee band, which is red on every authenticated route.
  - Other red sources: the primary CTA, LIVE stickers and error blocks.
- If a route misses a band, fix the layout (adjust card or marquee sizes). Never widen the bands.

### 2.3 Typography

- Load fonts via `next/font/google` in `frontend/app/layout.tsx`, with `display: "swap"` and the fallbacks listed below:
  - **Space Grotesk**, weights 500 and 700. Its maximum weight is 700, so the design's "900/black" maps to 700, and extra emphasis comes from size, uppercase and text-stroke.
  - **Space Mono**, weights 400 and 700. Used for every timing number, gap, lap time, ID, SQL and JSON, always with `font-variant-numeric: tabular-nums`.
- Fallbacks are `ui-sans-serif, system-ui` and `ui-monospace`. Never Inter, Roboto or Arial (lint A-2 bans Inter and Roboto).
- Fluid scale. Formula: slope = (max − min)/(1440 − 375); intercept = min − slope·375.

| Role | Token | clamp() | line-height |
|---|---|---|---|
| Display (hero, ≥ 48px) | `--fs-display` | `clamp(3rem, 1.944rem + 4.507vw, 6rem)` | 1.0 (ADR-007 exception for display only) |
| H1 page title | `--fs-h1` | `clamp(2rem, 1.472rem + 2.254vw, 3.5rem)` | 1.1 |
| H2 | `--fs-h2` | `clamp(1.75rem, 1.31rem + 1.878vw, 3rem)` | 1.2 |
| H3 | `--fs-h3` | `clamp(1.25rem, 1.074rem + 0.751vw, 1.75rem)` | 1.2 |
| Body | `--fs-body` | `clamp(1rem, 0.956rem + 0.1878vw, 1.125rem)` | 1.5 |
| Label/eyebrow | `--fs-label` | `clamp(0.75rem, 0.706rem + 0.188vw, 0.875rem)` | 1.2, uppercase, `letter-spacing: 0.08em`, weight 700 |
| Table data | `--fs-data` | `0.9375rem` fixed | 1.4 |

The 9px labels and 13px Arial body in the current `globals.css` go away. Prose is capped at a measure of 68ch.

### 2.4 Borders, radius, shadows

- Borders:
  - `--nb-border: 4px solid #000` on cards, buttons, inputs, modals, the sidebar edge and the top bar edge.
  - `2px` is allowed only on table cell dividers and chart grid.
  - At ≤ 620px, card borders drop to 3px. Buttons and inputs stay at 4px.
- Radius: `0` everywhere. `9999px` (`rounded-full`) is allowed only for tyre badges, status dots, avatar circles, the LIVE pill and toggles.
- Hard shadows, always zero blur and pure black:
  - Tailwind names `shadow-nb-4`, `shadow-nb-8`, `shadow-nb-12`, `shadow-nb-16` map to `Npx Npx 0 0 #000`.
  - Use numeric names: `shadow-xl` and `shadow-2xl` are banned by A-2, and `shadow-nb-*` avoids them.
  - Mobile (< 620px): no shadow above 8px.

### 2.5 The plinth: push/lift motion that passes lint A-7

`lint-motion.sh` bans transitions on `box-shadow`, `top`, `left`, `margin`, `width`, `height` and `all`. So the shadow never animates. Instead, the shadow is a separate static block under the element:

```css
/* frontend/app/styles/components.css, @layer components */
.nb-plinth { position: relative; isolation: isolate; }
.nb-plinth::before {            /* the shadow: never moves */
  content: ""; position: absolute; inset: 0;
  transform: translate(var(--nb-sh, 4px), var(--nb-sh, 4px));
  background: var(--nb-ink); z-index: -1;
}
.nb-plinth > .nb-face {         /* the face: moves */
  transition: transform 120ms ease-out;
}
@media (hover: hover) {
  .nb-plinth:hover > .nb-face { transform: translate(-2px, -2px); }            /* lift */
}
.nb-plinth:active > .nb-face { transform: translate(var(--nb-sh, 4px), var(--nb-sh, 4px)); } /* push flush */
.nb-plinth:has(> .nb-face:focus-visible) > .nb-face { outline: 4px solid var(--nb-ink); outline-offset: 4px; }
@media (prefers-reduced-motion: reduce) { .nb-plinth > .nb-face { transition: none; } }
```

- Do **not** use `.nb-plinth::before` with a `transform` transition.
- Static (non-interactive) cards use a plain, non-transitioned `box-shadow: var(--shadow-nb-8)`.
- `<button>` cannot hold block children in every browser. For buttons, put the plinth on the `<button>` itself and the face on an inner `<span class="nb-face">`. The 44px minimum hit area applies to the button.

### 2.6 Textures and motifs (decorative only, `aria-hidden`)

`frontend/app/styles/textures.css` is the only file allowed to contain `gradient(`. A new lint enforces this.

- `.tx-halftone`: `radial-gradient(#000 1px, transparent 1.5px) 0 0 / 12px 12px`, at opacity 0.12 behind hero blocks.
- `.tx-grid`: two `linear-gradient` lines with 1px hard stops, at a 24px pitch, on the login left panel and the DBMS EER canvas.
- `.tx-noise`: a static SVG `feTurbulence` data URI, at opacity ≤ 0.06. Use only on the hero and login panels, never behind data tables (it hurts contrast and the palette scorer).
- `.tx-caution`: `repeating-linear-gradient(-45deg, #000 0 12px, #FFD93D 12px 24px)`, a 12px-high strip on partial-state banners.
- `.tx-checker`: an 8×8px black/white checker strip, the chequered-flag motif.

`frontend/components/nb/motifs.tsx` holds inline SVGs, each `aria-hidden="true" focusable="false"` with a 3px black stroke:
- `StarBurst` (8- and 12-point);
- `Arrow` (right and diagonal);
- `CheckerStrip`;
- `SpeedLines` (3 horizontal bars);
- `RaceFlag` (green/yellow/red/chequered, colour plus pattern).

Use lucide-react icons at `strokeWidth={2.5}`, 20/24px. No emoji (A-2 bans U+1F300–1FAFF).

**Text-stroke display type.** An outlined duplicate is decorative and must be `aria-hidden`, because axe can flag transparent text. The real heading stays solid black.

```tsx
<h1 className="nb-display">RACE OPERATIONS</h1>
<span aria-hidden="true" className="nb-display nb-stroke">RACE OPERATIONS</span>
```

`.nb-stroke { color: transparent; -webkit-text-stroke: 2px #000; }`

**Stickers.**
- `.nb-sticker` uses `rotate(var(--tilt))` with `--tilt` from {-3deg, -2deg, 2deg, 3deg}.
- Allowed on badges, eyebrow labels and empty-state sticker cards only.
- Never on inputs or table cells: rotation must never touch text the user reads as data.

### 2.7 Motion catalogue

All motion uses only `transform`, `opacity` or `background-color`, with named properties, at 100–300ms, `ease-out` or `linear`. Every item has a reduced-motion fallback in the same file.

| # | Motion | Where | Spec | Reduced motion |
|---|---|---|---|---|
| M1 | Page enter | `<main>` children | translateY(8px) + opacity 0 → 0/1, 200ms ease-out, 40ms stagger, max 6 items | instant |
| M2 | Lift/push | buttons, nav items, clickable cards | plinth, 120ms (2.5) | no transition; press still shows the flush state |
| M3 | Sticker wiggle | empty-state sticker, season sticker on hover | rotate ±2deg, 2 × 150ms | none |
| M4 | Marquee | top-bar race-control ticker, standings ticker, login | static wrapped feed; newly changed content reveals with opacity over 200ms, no duplicated track or automatic scrolling | static wrapped list, no duplicate (duplicate also `aria-hidden`) |
| M5 | Live row reorder (FLIP) | live timing tower, standings after recalculation | measure → invert translateY → play 300ms ease-out | instant reorder |
| M6 | Cell update flash | gap/interval/lap-time cells on change | one background-color highlight settling over 200ms; coalesce rapid updates to avoid repeated flashing | none (value still updates) |
| M7 | LIVE dot | LIVE sticker, WS connected | solid dot; opacity transition over 200ms only when connection state changes, no blinking loop | solid dot |
| M8 | Loading skeleton | every loading state | static 45° ink/paper hard-stripe block; opacity reveal over 200ms, no repeating overlay motion | static stripes |
| M9 | Spinner replacement | inline busy buttons | static square/star with 200ms opacity entry (replaces `@keyframes spin` ring without a repeating rotation) | static star + "Working…" text |
| M10 | Modal | `Modal` | scrim opacity 150ms; panel translateY(16px) → 0 + opacity, 200ms ease-out | instant |
| M11 | Mobile drawer | shell | translateX(-100%) → 0, 200ms ease-out | instant |
| M12 | Toast/notice | action success/error | slide translateY(-8px) + opacity, 150ms | instant |
| M13 | Chart draw-in | recharts lines on first data | recharts `isAnimationActive`, 300ms, false on updates | `isAnimationActive={false}` |
| M14 | Podium rise | standings top 3 | translateY(16px) → 0, 250ms, staggered | instant |

Implementation rules:
- T-440 reconciliation: the owner's 100–300ms limit takes precedence over the former long-loop catalogue. M4/M7/M8/M9 use static ongoing content with event-triggered entry or state transitions, preserving data and busy/status meaning without rapid repeating motion. Display minimum is 48px wherever leading is 1.0.
- `frontend/lib/use-reduced-motion.ts`: a 10-line `matchMedia` hook (W2 owns it).
- Every JS-driven motion (M5, M13) reads the hook.
- CSS motion lives in `@layer components` with one global `@media (prefers-reduced-motion: reduce)` block that sets durations to 0.
- No motion library. Framer Motion would cost ~35KB gzip against the 170KB per-route P-3 budget.
- `will-change: transform` is added only while an animation runs (M5 adds and removes it in JS), never globally. This protects P-5.
- Never animate more than 30 rows at once in M5. Above that, reorder instantly.

### 2.8 Component inventory (`frontend/components/nb/`)

Each component is typed, takes `className`, forwards `ref` where it is interactive, and has no single-call-site abstraction (A-6). The `cn()` helper is 6 lines in `frontend/lib/cn.ts`, with no `clsx` or `tailwind-merge` dependency.

| Component | Replaces / wraps | Notes |
|---|---|---|
| `NbButton` | `Button` in `ui.tsx` | variants: `primary` (red), `secondary` (paper), `accent` (yellow), `danger` (red with "!" icon), `ghost` (cream, border only). Sizes `md` (44px) and `lg` (56px). `busy` shows M9. Keeps `data-primary` passthrough. |
| `NbCard` | `.panel` | `tone` = paper/cream/yellow/violet/mint/red; `shadow` = 4/8/12; optional `interactive` adds plinth |
| `NbSticker` | badges/eyebrows | `tilt`, `tone`; `aria-hidden` when decorative |
| `NbBadge` | status pills | session states (SCHEDULED, LIVE, PAUSED, FINISHED, ARCHIVED), incident states (OPEN, APPROVED, REJECTED), pit states (RESERVED, ACTIVE, COMPLETED, CANCELLED); text + colour |
| `TyreBadge` | — | `rounded-full` 28px circle, letter, compound colour |
| `NbInput`, `NbSelect`, `NbTextarea`, `NbField` | inputs in `ResourceEditor` | 4px border, 48px height, label above, error text below with `aria-describedby`; focus gets a 4px yellow ring plus a black outline |
| `NbTable` | `DataTable` | sticky header (ink background, paper text), 2px row dividers, zebra cream/paper, Space Mono numeric columns right-aligned; horizontal scroll inside a `min-w-0` wrapper with a visible edge shadow block |
| `NbTabs` | `/dbms` and `/live` view switches | folder tabs: active tab is raised with yellow fill and joins the panel border; roving tabindex; keeps hash sync |
| `NbModal` | `Modal` | panel 4px border + shadow-nb-12, ink title bar; focus trap and Escape kept from the current implementation |
| `NbMarquee` | — | M4; props `items`, `tone`; `aria-live="off"`; full list also exposed once for screen readers |
| `NbStat` | dashboard stats | big Space Mono number, label sticker, delta arrow |
| `NbState` | `StateMessage`, `PartialStateNotice` | the 5 states (2.9) with identical copy props |
| `NbSkeleton` | spinners | M8 |
| `motifs.tsx` | — | 2.6 |
| `NbChartFrame` + `chart-theme.ts` | recharts wrappers | 2.10 |

### 2.9 The five states (look, not copy)

Copy strings stay exactly as they are today. Only the presentation changes.

- **Empty:** paper `NbCard` with a tilted yellow `NbSticker` "NO DATA ON TRACK" (decorative, `aria-hidden`), a `StarBurst`, the existing empty copy as the real text, and the primary action if the route has one.
- **Loading:** `NbSkeleton` blocks matching the populated layout (row count = page size capped at 8), so CLS stays 0, plus `aria-busy="true"` on the region.
- **Error:** red `NbCard` with ink text, an "!" block icon, the existing error copy and a `Retry` `NbButton secondary`. Keep the `.state.error` classes.
- **Partial:** `.tx-caution` strip on top, yellow body, the existing partial copy, and which source is missing (SQL vs Mongo).
- **Populated:** normal content.

### 2.10 Charts (recharts, kept)

`frontend/components/nb/chart-theme.ts` exports:
- line stroke `#000`, width 3, `dot={false}`, active dot an 8px square;
- secondary series `#7CC4FF` and tertiary `#FF6B6B`, also distinguished by `strokeDasharray` (colour is never the only signal);
- CartesianGrid `stroke="#000" strokeDasharray="4 4" strokeOpacity={0.25}`;
- axes in Space Mono 12px with a 2px black axis line;
- a tooltip component: paper, 4px border, shadow-nb-4, no blur;
- no gradient `<defs>` and no area gradients.

Load recharts with `next/dynamic(() => import(...), { ssr: false, loading: () => <NbSkeleton variant="chart" /> })` so it leaves the initial bundle (P-3).

Keep every existing chart:
- the `/live` selected-driver telemetry `LineChart`s (height 190, raised to 220 at ≥ 1000px);
- the tyre temperatures chart;
- every analytics chart.

---

## 3. Phases, tasks and owners

Legend:
- **Owner:** O = orchestrator; W1 UI; W2 state/runtime/backend; W3 eval/QA.
- **Par:** tasks with the same letter in one phase can run as 2 workers at once (disjoint files).
- **Verify:** the task or parent milestone acceptance requirement. A child packet records the exact applicable task command; the complete parent gate runs at its domain/milestone boundary under `delivery-workflow.md`. The orchestrator reruns every candidate packet command through `accept.sh`.

Scope note: in this repo W2 owns `backend/app/**` and `backend/migrations/**` as well as `frontend/lib/**`. W3 owns `backend/tests/**`, `frontend/e2e/**` and `scripts/eval/**`.

### Phase 0 — Architecture amendment (orchestrator only, STOP for owner approval)

| ID | Owner | Task | Verify |
|---|---|---|---|
| T-300 | O | Create branch `overhaul/neo-brutal` from `perfection-loop`. `.agent/models.env` hard-codes `export HARNESS="antigravity"`, which ignores the caller's choice; change that line to `export HARNESS="${HARNESS:-claude}"` (agent-kit file, not product source). Then run `HARNESS=<claude\|codex\|gemini\|antigravity> source .agent/models.env && bash scripts/agent/boot.sh`; fix any failure first. | `bash scripts/agent/boot.sh` exit 0 |
| T-301 | O | Run `/architect` to draft **ADR-007 "Neo-brutal motorsport (light) overhaul"** (contents below). Unlock ARCHITECT.md, amend A.4/A.5/B.5, re-run Phase C five lenses for the amendment, and re-lock. | `bash scripts/agent/verify-lock.sh` exit 0 |
| T-302 | O | **STOP.** Post an ADR-007 summary in chat and wait for an explicit owner "approved". Do not dispatch any product task before that. | owner message |

ADR-007 must say:
1. **Archetype.** A.4 changes from "dark motorsport identity" to "Neo-Brutal Motorsport (light)". A.5 drops "no visual redesign" for the frontend only; "no wholesale rewrite of race flows, SQL rules, API routes or persisted IDs" stays.
2. **Re-baselined gates, equal strictness:**
   - `palette.spec.ts`: dark `bgLum <= 0.12` becomes light `bgLum >= 0.85`; heading contrast stays ≥ 4.5.
   - A-3 roles become `#FFFDF5,#FFFFFF,#FF6B6B`; the bands are unchanged.
3. **Shadow exception.** Hard shadows with **zero blur** are the archetype signature and are allowed at any offset ≤ 16px. Any blur > 0 is banned (stricter than the old "blur > 16px" rule).
4. **New lints (A-2 extension):**
   - gradients only in `textures.css`;
   - no gray-family utilities or neutral hexes;
   - radius only 0 or 9999px;
   - no `blur(`;
   - no `font-weight: 900` (the font has no 900);
   - text must not be white on `#FF6B6B`.
5. **Display line-height** 1.0 is allowed for display type ≥ 48px only.
6. **Additive API changes** listed in Phases 2–4, each with its own ADR (ADR-008.. as needed).
7. **CI** runs on push to `perfection-loop`, `master` and `overhaul/**`, and on every PR.
8. **Honest scoring.** ruff, ruff format, mypy and audit join the Functional dimension as F-7 (lint-py, weight 2), F-8 (types-py, weight 2) and F-9 (audit, weight 1). The hard gates gain F-2. Thresholds are never lowered.

### Phase 1 — Honest green baseline (before any visual work)

| ID | Owner | Par | Task | Verify |
|---|---|---|---|---|
| T-310 | W2 | a | `ruff format backend/app` (mechanical) then fix `ruff check` in `backend/app` without behaviour changes. List any rule you disable with a reason in `pyproject.toml`; ban blanket `noqa`. | `.venv/bin/ruff check backend/app && .venv/bin/ruff format --check backend/app` |
| T-311 | W3 | a | Same for `backend/tests` and `scripts/eval/*.py`. Fix the 2 eslint `any` errors in `frontend/e2e/perf-fps.spec.ts` with real types. | `.venv/bin/ruff check backend/tests && npm --prefix frontend run lint -- --max-warnings 0` |
| T-312 | W2 | b | mypy strict baseline. Add precise types to `database.py`, `config.py`, `auth_cookie.py`, `runtime_lease.py` and `schemas_*.py` first. Record the remaining count in CURRENT_STATE; Phase 3 takes it to 0. No `# type: ignore` without an error code and reason. | `.venv/bin/mypy --strict backend/app 2>&1 \| tail -1` shows a lower count than 222 |
| T-313 | W3 | b | CI: `.github/workflows/*.yml` triggers per ADR-007. Jobs: ruff, mypy (allowed to fail until T-339, labelled), pytest against service containers (postgres:16, mongo:7), typecheck, lint, build, Playwright mocked suite. Cache npm and pip. | `actionlint` exit 0 (or `npx --yes @action-validator/cli`) |
| T-314 | W3 | — | Add F-7/F-8/F-9 to `scripts/eval/score.sh` and `evaluation.md` per ADR-007, and record the real score in `.agent/eval/`. Expect it to drop; that is the point. | `bash scripts/eval/score.sh` runs; output saved |

### Phase 2 — Security (backend first, frontend glue after)

| ID | Owner | Par | Task | Verify |
|---|---|---|---|---|
| T-320 | W3 | a | Failing tests first:<br>• CORS rejects unknown origin with credentials;<br>• security headers present;<br>• logout revokes the JWT (a reused token returns 401);<br>• `/health/live` and `/health/ready`;<br>• WS rejects a revoked token. | `.venv/bin/pytest -q backend/tests/test_security_headers.py backend/tests/test_logout_revocation.py` fails for the right reason (record the output) |
| T-321 | W2 | — | **CORS:** replace `*` with an allow-list from `CORS_ORIGINS` (comma list, default `http://localhost:3000,http://127.0.0.1:3000`). Fail startup if `*` is combined with credentials. | T-320 CORS tests pass |
| T-322 | W2 | — | **Security headers middleware** (pure ASGI, no dependency):<br>• `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, `X-Frame-Options: DENY`, `Permissions-Policy` (camera/mic/geo off);<br>• `Strict-Transport-Security` only when `COOKIE_SECURE=1`;<br>• API CSP `default-src 'none'; frame-ancestors 'none'`. | header tests pass |
| T-323 | W2 | — | **JWT revocation:**<br>• Add a `jti` claim. Additive migration `004_token_revocation.sql`, with table `revoked_tokens(jti uuid primary key, expires_at timestamptz not null)` and an index on `expires_at`.<br>• Logout inserts the jti. The auth dependency and WS handshake check it.<br>• A cleanup runs on login, deleting rows where `expires_at < now()`.<br>• Old tokens without a jti stay valid until expiry (compatibility). Document this in ADR-008. | revocation tests pass; `pytest -q backend/tests` all green |
| T-324 | W1 | — | Next.js headers in `next.config.*`: CSP with `default-src 'self'`; `connect-src 'self'` plus the API origin and its `ws(s)` origin from env; `font-src 'self'` (next/font self-hosts); `img-src 'self' data:`; `style-src 'self' 'unsafe-inline'` (Next requirement, documented); `frame-ancestors 'none'`. | `npm --prefix frontend run build` + accessibility spec green |
| T-325 | W2 | — | Rate limiter keeps current behaviour. Add a unit test proving the limiter key cannot be spoofed via `X-Forwarded-For` unless `TRUST_PROXY=1`. | `pytest -q backend/tests/test_login_throttle.py` |

### Phase 3 — Backend structure and performance (no API change)

Before any refactor, W3 adds the snapshot test T-330. Every later task must keep it green.

| ID | Owner | Par | Task | Verify |
|---|---|---|---|---|
| T-330 | W3 | — | **Contract snapshot test.** Boot the app and dump `app.openapi()` to `backend/tests/snapshots/openapi.json`. The test fails on any removed path, method, or required response field (additions allowed). Also add golden JSON responses for 10 key GET routes on the seeded test stack. | `pytest -q backend/tests/test_contract_snapshot.py` |
| T-331 | W2 | — | **Backend structure, delivered jointly with T-332 by domain.** Move domain logic/routers into `backend/app/api/` and runtime/security/lifespan into `core/`. Reuse completed extractions and characterization tests. Move each domain toward its final DI ownership once; do not create temporary assembly/forwarding modules solely to lower a file count. `main.py` must be <=120 lines at the completed structural milestone, containing app creation, middleware, router inclusion and lifespan. Mechanical moves do not mix unrelated behavior changes. Bounded structural packets follow ADR-014. | T-330 + full disposable pytest at each completed domain tranche; task-focused checks through accept.sh |
| T-332 | W2 | — | **Dependency injection, same structural milestone as T-331.** Replace positional router factories with domain `APIRouter` modules using `Depends(get_pool)`, `Depends(get_mongo)`, `Depends(current_user)` and `Depends(require_roles(...))`. Reuse existing request providers. Shared pool/Mongo/bus/simulations/lease live on `app.state` and are set in lifespan; remove module globals. Finish one domain before the next; fold intermediate assembly-only glue into final ownership. Preserve API and compatibility behavior through existing regression tests. | T-330 + full disposable pytest at each completed domain tranche; task-focused checks through accept.sh |
| T-333 | W2 | — | **Typed CRUD.** Replace `dict` payloads with Pydantic v2 models per resource (`ChampionshipIn/Out`, `CircuitIn/Out`, `TeamIn/Out`, `DriverIn/Out`, `EventIn/Out`, `SessionIn/Out`, `UserIn/Out`, `MembershipIn/Out`). Field names and optionality are identical to the current wire shape (read `docs/contracts.md` and `crud_repository.py`). Responses use `response_model` with `model_config = ConfigDict(extra="allow")` during migration, then tighten once the snapshot passes. | T-330 + `pytest -q backend/tests/test_api.py` |
| T-334 | W2 | — | **Simulator loop off the event loop.** The tick currently calls `insert_one` per packet inside async code (around `main.py:1136`). Instead, collect the tick's packets and write them with one `insert_many(ordered=False)` inside `await anyio.to_thread.run_sync(...)`. SQL writes per tick also run in the threadpool, or use `psycopg` async if the pool is converted (choose threadpool: smaller change). Keep the ADR-005 ordering and idempotency checks per packet before the batch, and keep WS publish order identical. | `pytest -q backend/tests/test_simulation_replay.py backend/tests/test_telemetry_ordering.py backend/tests/test_telemetry_ingest_contract.py` |
| T-335 | W2 | — | **Migration ledger.** Table `schema_migrations(version text primary key, checksum text not null, applied_at timestamptz default now())`. `bootstrap.py` applies each file once, in a transaction, in version order. A changed checksum for an applied file stops startup with a clear error. The seed runs only when `SEED_DEMO=1` and is idempotent (`ON CONFLICT DO NOTHING`). Existing databases: if tables exist and the ledger does not, back-fill 001–003 as applied after verifying a sentinel object from each. | new `test_migrations.py`: fresh DB, re-run (no-op), existing-DB back-fill, checksum tamper |
| T-336 | W2 | — | **Query fixes:**<br>• `/api/dbms/races/{id}` N+1 `find_one` per driver → one `$in` query, or a `$group` aggregation taking the latest packet per driver with `$sort` + `$first`. Add an index `{session_id:1, driver_id:1, recorded_at:-1}` if missing (additive, created in bootstrap with `background`-equivalent default).<br>• Overview `count_documents({})` → `estimated_document_count()`.<br>• Audit every list endpoint for missing `LIMIT`/pagination; add server caps (max 200), keeping the current default page sizes. | T-330 goldens + an `EXPLAIN` assertion test that the new query uses the index |
| T-337 | W2 | — | **Points system as data.** Additive migration `005_points_systems.sql`:<br>• tables `points_systems(id, name)` and `points_system_positions(system_id, position, points)`;<br>• nullable `championships.points_system_id` with the default system seeded to exactly the current CASE values.<br>The standings function uses the table when the column is set, else the CASE. Do not delete the CASE in this phase. ADR-009. | `test_database.py -k standings` plus a new equality test: every existing championship's recalculated standings are identical before and after |
| T-338 | W2 | — | **Observability:**<br>• JSON logs (stdlib `logging` + a 20-line formatter) with request id (`X-Request-ID` in/out), method, path, status, duration_ms and user id.<br>• Never log tokens, passwords, cookies or CSRF.<br>• `/health/live` (process up) and `/health/ready` (pool ping + Mongo ping + lease held). Keep the existing health route unchanged. | T-320 health tests + log redaction test |
| T-339 | W2 | — | **mypy strict to zero** across `backend/app`. Flip the CI mypy job to required. | `.venv/bin/mypy --strict backend/app` exit 0 |
| T-340 | W2 | — | **Docker:**<br>• backend image runs as non-root `app` (uid 10001), multi-stage, `HEALTHCHECK` against `/health/live`, `PYTHONDONTWRITEBYTECODE=1`;<br>• hashed lock file `backend/requirements.lock` from `uv pip compile --generate-hashes`, installed with `--require-hashes`;<br>• frontend image uses `next build` standalone output and runs as a non-root user;<br>• compose gets healthchecks and `depends_on: condition: service_healthy`. | `docker compose build && docker compose up -d && curl -fsS localhost:8000/health/ready` (record if Docker unavailable: then `hadolint` + `uv pip compile --dry-run`) |

### Phase 4 — DBMS showcase (additive; the course's strongest marks)

Each item is a backend route plus a `/dbms` panel. Admin only, read-mostly. Every write demo runs inside a transaction that is rolled back, or on demo-scoped rows. Write ADR-010 "DBMS showcase routes" once for the group.

| ID | Owner | Task | Verify |
|---|---|---|---|
| T-350 | W3 | Failing API tests for T-351..T-357 on the seeded test stack. | tests fail for the right reason |
| T-351 | W2 | `GET /api/dbms/isolation-demo?level=read_committed\|repeatable_read\|serializable`: two connections run a scripted interleaving on a demo row; return the observed reads, any anomaly (non-repeatable read, phantom, serialization failure) and a timeline. Roll back both. | test |
| T-352 | W2 | `POST /api/dbms/deadlock-demo`: two connections lock rows in opposite order with `lock_timeout` and `deadlock_timeout` set low; return which transaction Postgres aborted plus the error code `40P01`. | test |
| T-353 | W2 | Views:<br>• `v_driver_season_summary` (regular view);<br>• `mv_championship_standings` (materialized, with a unique index), plus `POST /api/dbms/refresh-standings-mv` using `REFRESH MATERIALIZED VIEW CONCURRENTLY`;<br>• `GET /api/dbms/views` lists them with definitions (`pg_get_viewdef`).<br>Migration 006. | test |
| T-354 | W2 | Window-function analytics: `GET /api/analytics/gaps?session_id=` returns per lap position (`RANK() OVER`), gap to leader (`elapsed - FIRST_VALUE(elapsed) OVER (PARTITION BY lap ORDER BY elapsed)`), interval (`LAG`) and rolling 3-lap average. Add the SQL text to the response under `sql` for display. | test + EXPLAIN uses index |
| T-355 | W2 | EXPLAIN toggle: the existing query-plans route gains `?analyze=true` (additive), allowed only for a fixed allow-list of named demo queries, never user SQL. Runs inside `BEGIN; EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) ...; ROLLBACK;`. | test |
| T-356 | W2 | Audit trail: migration 007 adds `audit_log(id bigserial, table_name, op, row_pk jsonb, old jsonb, new jsonb, actor text, at timestamptz)`, generic trigger `audit_row()` on `penalties`, `results`, `pit_reservations`, `championships`. The actor comes from `current_setting('apexgrid.actor', true)`, which the API sets per transaction with `SET LOCAL`. Add `GET /api/dbms/audit?table=&limit=`. | test: approve a penalty → one audit row with the actor |
| T-357 | W2 | Least privilege and RLS:<br>• migration 008 creates role `apexgrid_app` (DML on app tables, no DDL) and `apexgrid_readonly`, grants and a RLS demo policy on `audit_log` (stewards see only `penalties` rows);<br>• `GET /api/dbms/security` lists roles, grants (`information_schema.role_table_grants`) and policies (`pg_policies`).<br>Document switching the runtime DSN to `apexgrid_app` in `docs/database.md`; keep the owner DSN the default so nothing breaks. | test |
| T-358 | O | Docs: `docs/database.md` gains a normalisation section (each table's key, FDs and the 3NF/BCNF argument, plus the deliberate denormalisations: telemetry in Mongo, the standings MV), a backup/restore runbook (`pg_dump -Fc`, `pg_restore`, `mongodump --gzip`), and an index rationale table. | file exists, links valid |

### Phase 5 — Frontend foundation (tokens, Tailwind 4, fonts, primitives' CSS)

| ID | Owner | Par | Task | Verify |
|---|---|---|---|---|
| T-360 | W3 | a | New lints in `scripts/eval/`:<br>• `lint-neobrutal.sh` (rules from ADR-007 §4) with self-tests (`scripts/eval/rules/` fixtures: one good, one bad file per rule);<br>• extend `lint-motion.sh` to allow the plinth pattern only (transform on `.nb-face`).<br>Update `palette.spec.ts` to light per ADR-007. Before the redesign lands, the palette spec is expected to fail on light; mark it in CURRENT_STATE, never `skip`. | `bash scripts/eval/lint-neobrutal.sh --self-test` |
| T-361 | W1 | a | **Tailwind 3.4 → 4:**<br>• Remove `tailwind.config.ts` and `autoprefixer`; add `@tailwindcss/postcss`. The PostCSS config is `{ plugins: { "@tailwindcss/postcss": {} } }`.<br>• `frontend/app/styles/tokens.css` uses `@import "tailwindcss";` and `@theme { ... }` containing:<br>&nbsp;&nbsp;– colours 2.1;<br>&nbsp;&nbsp;– `--spacing-*: initial` plus only `--spacing-0: 0; -1: 4px; -2: 8px; -3: 12px; -4: 16px; -6: 24px; -8: 32px; -12: 48px; -16: 64px;`;<br>&nbsp;&nbsp;– `--radius-*: initial` plus `--radius-none: 0; --radius-full: 9999px;`;<br>&nbsp;&nbsp;– `--shadow-*: initial` plus `--shadow-nb-4..16`;<br>&nbsp;&nbsp;– `--font-sans: var(--font-space-grotesk), ui-sans-serif, system-ui;` and `--font-mono: var(--font-space-mono), ui-monospace;`;<br>&nbsp;&nbsp;– fluid type tokens 2.3;<br>&nbsp;&nbsp;– `--ease-mech: cubic-bezier(0.2, 0, 0, 1)`.<br>• Keep the old `globals.css` classes working: import order is `tokens.css`, `textures.css`, `components.css`, then legacy `globals.css`. The legacy file shrinks route by route (Phase 7–8) and is deleted at the end. | `npm --prefix frontend run build && npm --prefix frontend audit --audit-level=high` (Tailwind chain fixed) + all existing E2E still green except the palette spec |
| T-362 | W1 | — | `layout.tsx`:<br>• `next/font/google` Space Grotesk (500, 700) and Space Mono (400, 700) as CSS variables;<br>• `<html lang="en">` with `bg-cream text-ink`;<br>• `<body>` font-sans, antialiased off (brutal look keeps default);<br>• skip link "Skip to content" as a yellow block visible on focus. | build + accessibility spec |
| T-363 | W1 | — | `textures.css` (2.6) and `components.css`: plinth, sticker, marquee, stroke text, skeleton, caution strip, focus ring, and the reduced-motion block. Spacing only from tokens. | `lint-spacing.sh`, `lint-motion.sh`, `lint-banned.sh`, `lint-neobrutal.sh` |
| T-364 | W2 | — | `frontend/lib/use-reduced-motion.ts`, `frontend/lib/cn.ts`, `frontend/lib/use-flip.ts` (M5: takes a keyed list ref, returns nothing, respects reduced motion, adds and removes `will-change`), `frontend/lib/use-flash-on-change.ts` (M6). No dependency. | `npm --prefix frontend run typecheck` + a new unit test via Playwright component-free page `e2e/motion-hooks.spec.ts` (W3 writes it in T-366) |
| T-365 | W1 | — | `frontend/components/nb/*` per 2.8. No route uses them yet, except a hidden `/__nb` style-guide route, gated by `process.env.NODE_ENV !== "production"`, which renders every component in every state. | build + `/__nb` axe clean at 375 and 1440 |
| T-366 | W3 | — | `e2e/nb-primitives.spec.ts` on `/__nb`:<br>• focus visible on every interactive element;<br>• 44px targets;<br>• plinth active state flush;<br>• reduced motion (`page.emulateMedia({ reducedMotion: "reduce" })`) gives zero running animations (`document.getAnimations().length === 0`);<br>• marquee duplicate is `aria-hidden`;<br>• no `rounded-[^nf]` classes in the DOM. | spec green on all 5 projects |

### Phase 6 — Shell

| ID | Owner | Task | Verify |
|---|---|---|---|
| T-370 | W1 | Rewrite `shell.tsx` markup only (keep auth redirect effects, `menuButtonRef`, nav arrays and routes, focus return on drawer close):<br>• **Sidebar** (≥ 1000px, 264px; 232px at 1000–1199px):<br>&nbsp;&nbsp;– cream, `border-r-4`; brand block at top: black square with a yellow "AG" monogram plus the "APEXGRID" wordmark in Space Grotesk 700;<br>&nbsp;&nbsp;– group labels as small ink-on-yellow stickers (RACE CONTROL, CHAMPIONSHIP, PEOPLE & TEAMS, PLATFORM);<br>&nbsp;&nbsp;– nav items are 48px blocks with icon + label; hover lift (plinth 4);<br>&nbsp;&nbsp;– active item: yellow fill, 4px border, shadow-nb-4, `aria-current="page"`;<br>&nbsp;&nbsp;– footer: user chip (role badge) and a Sign out button (secondary).<br>• **Top bar** (sticky, 64px, paper, `border-b-4`):<br>&nbsp;&nbsp;– page breadcrumb in label style;<br>&nbsp;&nbsp;– season sticker (`2026 SEASON`, tilt -2deg);<br>&nbsp;&nbsp;– WS/health status pill (LIVE / RECONNECTING / OFFLINE using M7);<br>&nbsp;&nbsp;– on mobile, the menu button (48px).<br>• **Race-control marquee** under the top bar: a red band, 40px, ink text, built from `/api/dashboard` (active session, open incidents count, next event). Hidden when there is no data (no empty band). M4.<br>• **Mobile drawer** (< 1000px): M11 transform, scrim cream at 0.9 (no blur), focus trap, Escape closes, 4px right border.<br>• Main content: `min-w-0`, padding 16px mobile / 24px tablet / 32px desktop, max width none (data app), 32:9 safe (content grid caps at 1600px centred only for prose pages). | routes, responsive, touch-targets, accessibility, data-primary specs green; no horizontal overflow at 320 and 32:9 |
| T-371 | W2 | Marquee data hook `use-race-control-feed.ts` (polls `/api/dashboard` every 30s while visible via `document.visibilityState`, aborts on unmount, and shares with the dashboard to avoid a double fetch through a tiny module-level cache with 10s TTL). | typecheck + E-4 spam spec still 1 request |

### Phase 7 — Route redesigns (W1 markup; W2 only where data hooks change)

Rules for every route task:
1. Keep component logic; change markup and classes only. If logic must move, that part becomes a W2 sub-task.
2. Before editing, `rg -n` the route's copy strings in `frontend/e2e/` and list them in the packet as "must remain verbatim".
3. Five states per data region using `NbState`.
4. Exactly one `data-primary` per viewport.
5. Delete the legacy `globals.css` selectors that the route no longer uses, in the same task.
6. Each task's Verify runs the routes, states-matrix, responsive, touch-targets, accessibility and data-primary specs for that route via `--grep`, plus the 4 lints.

Order:
- Login and dashboard first (they set the tone).
- Then the resource pages (largest surface, one component).
- Then live, sessions, stewards, pit wall, standings, analytics and DBMS.
- Live and DBMS are the largest; give them their own packets split by section.

| ID | Route | Design |
|---|---|---|
| T-380 | `/login` | 60/40 split (stacks at < 1000px, art panel first but shorter, 240px):<br>• **Left (60%):** cream with `.tx-grid`; giant "APEXGRID" display word with an outlined `aria-hidden` duplicate offset 8px behind it; `CheckerStrip` across the bottom; a static M4 feed "RACE CONTROL · TELEMETRY · STEWARDS · PIT WALL · STANDINGS"; a yellow `StarBurst` sticker "DBMS EDITION".<br>• **Right (40%):** paper `NbCard` shadow-nb-12, eyebrow "AUTHENTICATED ACCESS", title "Sign in to ApexGrid" (verbatim), `NbField`s, a full-width primary button (`data-primary`), and an error block using the error state with the current 401 copy. Loading: button busy (M9) with fields disabled. |
| T-381 | `/dashboard` | • Hero row (60/40):<br>&nbsp;&nbsp;– left: label "CURRENT CONTEXT", display "RACE OPERATIONS" (the real h1 text stays "Race operations"; CSS uppercase) plus the stroke duplicate, and a "Race weekend" card for the active event (circuit, session, status badge, CTA "Open live timing" as `data-primary`);<br>&nbsp;&nbsp;– right: a violet "SERVICE HEALTH / Platform status" card with Postgres/Mongo/WS/lease rows, each a mint/red block + text.<br>• KPI row: 4 `NbStat` tiles (active_sessions red, scheduled_events yellow, open_incidents violet, drivers mint) with Space Mono 48px numbers; sticker tilt alternates.<br>• Below: "Next up" event list and "Latest incidents" mini-table. |
| T-382 | Resource pages: `/championships`, `/events`, `/circuits`, `/teams`, `/drivers`, `/users` via `resource-page.tsx` | • Header: eyebrow + h1 + count sticker + Add (primary, `data-primary`) + Reload (secondary).<br>• Toolbar: `SearchBox` as `NbInput` with a search icon (44px), result count, and "Showing 1–50 of N".<br>• `NbTable` with row actions (Edit/Delete as 44px icon buttons with `aria-label`).<br>• Pagination: Previous/Next blocks plus a "Page x / y" mono label.<br>• `ResourceEditor` in `NbModal` with `NbField`s, inline validation and a disabled-while-saving primary.<br>• Delete confirm modal with a red danger button.<br>• Team memberships modal: two columns (current roster / add driver).<br>• Drivers table shows an eligibility badge.<br>• Users table shows a role badge and is admin only.<br>Keep `pageSize = 50`, the user-role filter, the drivers `user_id` uniqueness message and `actionError`. |
| T-383 | `/live` part A: header, demo controls, race list | • Header: h1 "Live session" + LIVE sticker (M7, red pill) + connection pill.<br>• "LIVE DEMO / Put a full grid on track" as a yellow `NbCard` with the create-race primary (`data-primary`).<br>• "GENERATED SESSIONS / Live race demos" list as paper cards with status badge, lap counter "L 12/56" mono, and Select/Delete; "Show recent races" toggle. Delete modal "Delete generated race?" with "Keep race" kept verbatim. |
| T-384 | `/live` part B: timing tower | "LIVE TIMING / RUNNING ORDER" + "{n} cars on timing".<br>• Columns: position (black square, white mono numeral), team colour stripe (4px left bar), driver code + name, `TyreBadge` + tyre age, last lap, best lap, gap, interval, S1/S2/S3 cells, pit count.<br>• Sector cell colours: violet = overall best, mint = personal best, yellow = slower; letters/icons provide the non-colour cue.<br>• Fastest-lap holder gets a violet "FL" sticker.<br>• M5 FLIP reorder on position change; M6 flash on gap change. Row height 48px; click selects the driver (keyboard: Enter/Space, `aria-selected`).<br>• < 768px: show POS, DRIVER, GAP, TYRE plus an expand row for the rest (no horizontal page scroll; table scrolls inside its wrapper). |
| T-385 | `/live` part C: driver telemetry and records | • "SELECTED DRIVER TELEMETRY" in `NbChartFrame`s (speed, throttle/brake, gear, ERS as present today; plus "Tire temperatures · °C" with 4 corner tiles mono plus a chart).<br>• "RECORDED LAPS / Driver lap and sector history" `NbTable`.<br>• "RACE CONTROL RECORDS / Incidents and pit stops" as a timeline with flag motifs.<br>• "LATEST TELEMETRY / {n} samples in view" as a mono JSON-ish table.<br>• Empty copy "Waiting for timing and telemetry packets from this session." verbatim. |
| T-386 | `/sessions` | • Left 40%: session list with status badges, plus lifecycle buttons (Start/Pause/Resume/Finish as a segmented control with 48px blocks; current state yellow).<br>• Right 60%: "SELECTED SESSION" card, results table "{n} classified entries" with podium highlight, provisional badge (ADR-003), "Add or update session result" modal, and "TELEMETRY SIMULATOR" panel with controls.<br>• Empty copy "No result rows are recorded for this session." verbatim. |
| T-387 | `/stewards` | • Incidents are "case files": paper card, top tab "CASE #id", lap/turn, drivers involved, description, status sticker (OPEN yellow, APPROVED mint, REJECTED red).<br>• Decision form in the card footer: penalty type select, value, reason; Approve (primary) and Reject (danger). Keep the ADR-003 422 explanation block for time/grid sanctions.<br>• Penalties and sanctions tables.<br>• Licence points: segmented 12-cell meter per driver (filled cells red, `aria-valuenow`). |
| T-388 | `/pit-wall` | • Header "RACE CONTROL / PIT WALL".<br>• "AUTOMATIC STRATEGY / Driver pit decisions" cards with recommended lap and compound `TyreBadge` arrow `TyreBadge`.<br>• "PIT BOXES" as a physical grid of numbered boxes (box number huge mono, team colour stripe, status badge, time window); a reserved box is yellow and an active box is red with M7.<br>• "AUTOMATIC ALLOCATIONS / Pit stop queue" as a horizontal timeline (scrolls inside its wrapper on mobile), each item selectable.<br>• "RACE HISTORY / Completed pit stops" table.<br>• "Pit reservation" modal with "Cancel reservation" and "Mark completed" (MANUAL + RESERVED + canManage rule kept). |
| T-389 | `/standings` | • Stepped podium: P2 left, P1 centre (tallest, yellow), P3 right, as blocks with position numerals in stroke display type; M14.<br>• Full table below with points, wins, podiums and delta arrows.<br>• Championship selector (`NbSelect`).<br>• Recalculate is the `data-primary` button with busy state; after recalculation the table rows use M5.<br>• A standings marquee of the top 10 with points (M4). |
| T-390 | `/analytics` | 40/60:<br>• left: a sticky query form card (filters, sort, page size; Apply primary);<br>• right: "API RESULTS / {n} driver records" table plus 2 charts (points by driver bar chart with a black bar fill pattern; a consistency line);<br>• Previous/Next kept.<br>• New optional tab "Race gaps" using T-354 (window functions), showing the SQL in a mono "paper" block. |
| T-391 | `/dbms` part A: shell and overview | • Non-admin copy kept.<br>• Admin: eyebrow "PLATFORM / DATABASE ENGINEERING", h1 "DBMS workspace", Overview button `data-primary` (hash "overview").<br>• `NbTabs` folder tabs bound to hash routes (Overview, Tables, Schema, Indexes, Plans, Locks, Mongo, Cross-store, Actions, Archive, EER, plus new Showcase).<br>• "CONNECTED DATABASES / Live system state" with 2 big cards (PostgreSQL ink-on-mint, MongoDB ink-on-violet) showing version, size, connections, table and collection counts. |
| T-392 | `/dbms` part B: workspace views | • Table browser with Previous/Next offset 50.<br>• Column and index definitions as `NbTable`s.<br>• Query plans: mono plan tree on a paper card with a 2px left rule per depth and node cost bars (black blocks, width by cost share, transform-scaled, not width-animated). New ANALYZE toggle (T-355).<br>• Locks table.<br>• Mongo collections, indexes and documents (filter form + Apply + pagination); documents shown as collapsible mono JSON.<br>• Cross-store results.<br>• "DATABASE ACTIONS / Transaction and rule demonstrations" as a grid of action cards: each has a title, a one-line "what this proves", a Run button (`runOperation(key, path)` kept) and a result panel (success mint, rejected red, with the SQLSTATE code). "Recalculate standings" kept. |
| T-393 | `/dbms` part C: race archive, EER, showcase | • `race-database.tsx`: "RACE DATABASE EXPLORER / Live records & race archive", view switch as `NbTabs`, and every section kept ("Last recorded telemetry", "Every driver lap" + "Retry lap archive", incident reports, penalties, named pit stops). Keep the 15s refresh but pause it when the tab is hidden.<br>• `EerDiagram` restyle: entity boxes 4px border, shadow-nb-4, ink header with paper text, PK/FK markers as stickers, 3px black relationship lines with crow's-foot ends; `.tx-grid` canvas; pan by scroll container; "Foreign key relationships" list kept.<br>• **Showcase tab:** panels for isolation demo (timeline of T1/T2 reads), deadlock demo, views/MV refresh, audit log, security (roles, grants, policies), each with the SQL shown. |

Concurrency for Phase 7: W1 takes two routes at a time only if they share no files. `special-pages.tsx` (1,746 lines) is one file, so first run:

- **T-379 (W1 then W2, before T-381):** split `special-pages.tsx` into one file per page under `frontend/components/pages/` (`dashboard.tsx`, `sessions.tsx`, `stewards.tsx`, `live/*.tsx`, `pit-wall.tsx`, `analytics.tsx`, `dbms-center.tsx`).
  - Move only; no edits.
  - Route files keep their re-exports.
  - Verify: typecheck, build and the full mocked E2E.
  - After T-379, route tasks touch disjoint files and two W1 packets may run in parallel (still at most 2 workers total).

### Phase 8 — Visual polish and motion pass (Taste Agent)

| ID | Owner | Task | Verify |
|---|---|---|---|
| T-400 | O (Taste Agent) | Screenshot every route at 375 and 1440 (`scripts/eval/capture-screenshots.mjs`). Score A-5 against this plan's sections 2.1–2.10. List each defect as a W1 task T-401..T-4nn. Must check:<br>• rhythm (one card/shadow scale per region);<br>• max 3 accent colours visible per viewport besides cream/paper/ink;<br>• sticker rotation used ≤ 3 times per viewport;<br>• one display headline per route;<br>• no text on textures without a solid backing;<br>• no orphan grays. | defect list in `.agent/eval/taste.json` |
| T-401+ | W1 | Fix the taste defects. | lints + route specs |

### Phase 9 — Tests and visual regression

| ID | Owner | Task | Verify |
|---|---|---|---|
| T-410 | W3 | Playwright `webServer` uses `next build && next start -p 3100` for CI (keep `next dev` locally via an env flag). | full mocked suite green |
| T-411 | W3 | **Real-stack project** `real-stack` in `playwright.config.ts`:<br>• uses `scripts/eval/test-stack.sh up`, the API on 18000 with `SEED_DEMO=1`, and logs in through the UI;<br>• covers E2E-R01..R16 happy paths without `page.route` mocks, including WS live updates (assert the timing tower changes within 10s), steward approval and standings recalculation;<br>• runs at desktop-1440 and mobile-375 only (time budget). | `PLAYWRIGHT_PROJECT=real-stack ...` green; tests collected > 0 |
| T-412 | W3 | **Visual regression:** `toHaveScreenshot()` per route × {375, 1440}, with `mask` on live-changing regions (timing tower values, marquee, timestamps, charts) and `animations: "disabled"`. Baselines are committed after T-400 fixes. Threshold `maxDiffPixelRatio: 0.01`. | green against baselines |
| T-413 | W3 | **Motion specs:**<br>• reduced-motion gives zero running animations on every route;<br>• with motion on, the marquee animates only transform (`getAnimations()[i].effect.getKeyframes()` contains only `transform`);<br>• FLIP finishes in ≤ 350ms;<br>• P-5 perf-fps on `/live` with 20 cars updating at 4Hz stays at p95 ≤ 16.7ms and heap growth < 1MB. | green |
| T-414 | W3 | Re-run palette (light), states-matrix, touch-targets, accessibility (axe at all 5 viewports), responsive (no overflow 320 / 32:9), data-primary, edge-resilience (E-4 spam gives 1 request, E-5 offline recovery shows partial then recovers). | green |
| T-415 | W3 | Backend: coverage report (`pytest --cov=backend/app --cov-fail-under=80`); new tests for every Phase 2–4 route; property tests for standings tie-breaks (hypothesis is optional, only if added via ADR; otherwise table-driven). | green |

### Phase 10 — DevOps finish

| ID | Owner | Task | Verify |
|---|---|---|---|
| T-420 | W3 | CI adds the real-stack job (service containers), visual regression job (Linux baselines, generated in CI via an `update-snapshots` workflow_dispatch), `npm audit` + `pip-audit` jobs, Lighthouse CI on `next start` for 16 routes (P-1/P-2 assertions) and a bundle-size job (`verify-bundle-size.py`, 170KB). | workflow lint + a green run on the PR |
| T-421 | O | `README.md` quick start (compose up, seed, login demo accounts from the seed file, URLs), `docs/architecture.md` updated diagram, and a `docs/demo-guide.md` script for the course demo (which `/dbms` showcase panels to click, in order). | links valid |

### Phase 11 — Final evaluation

| ID | Owner | Task |
|---|---|---|
| T-430 | O | Run `/evaluate`. All checks run (no NOT_RUN in the denominator). Hard gates F-1, F-2, F-3, F-4, F-5, P-6 pass. Aggregate ≥ 95. At most 5 repair iterations, then escalate with the honest numbers. Write `.agent/FINAL_REPORT.md` from command output only (paste exit codes and counts, no adjectives). |
| T-431 | O | Delete legacy `frontend/app/globals.css` (should be empty by now) or reduce it to ≤ 50 lines of base resets. Confirm `rg -n "#0b0e12\|#11161c\|#d9ff3f\|Arial" frontend` finds nothing. |
| T-432 | O | Open a PR `overhaul/neo-brutal` → `perfection-loop` with the scorecard. Do not merge without the owner. |

---

## 4. Dependency graph and worker schedule

```
T-300 → T-301 → T-302 (owner approval)
          ↓
Phase 1: (T-310 ‖ T-311) → (T-312 ‖ T-313) → T-314
Phase 2: T-320 → T-321 → T-322 → T-323 → T-325   ‖   T-324 (W1, after T-322)
Phase 3: T-330 → [T-331 + T-332 by domain] → T-333 → T-334..T-338 by actual prerequisites → T-339 → T-340
Phase 4: T-350 → T-351..T-357 by actual prerequisites → T-358
Phase 5: (T-360 ‖ T-361) → T-362 → T-363 → (T-364 W2 ‖ T-365 W1) → T-366
Phase 6: (T-370 W1 ‖ T-371 W2)
Phase 7: T-379 → T-380..T-393 (2 W1 packets at once when files are disjoint, or W1 ‖ W2)
Phase 8: T-400 → T-401+
Phase 9: T-410 → T-411 → T-412 → T-413 → T-414 → T-415
Phase 10–11: T-420 → T-421 → T-430 → T-431 → T-432
```

Backend and independent frontend/QA tasks can interleave under the two-worker cap when target files are disjoint and true prerequisites are satisfied. Phase 7 still requires Phases 5–6; T-390/T-391/T-393 still require Phase 4. Serial phase arrows express required outcomes, not a reason to idle an independent lane. Read delivery-workflow.md for packet sizing and evidence reuse. Accepted task rows are not repeated merely because this historical table still lists them.

---

## 5. Acceptance and verification schedule

The authoritative schedule is `.agent/protocol/delivery-workflow.md` (ADR-014). Per task: review the diff/envelope/boundaries, rerun the relevant Verify independently through accept.sh, and update state once. An identical command already covered by accept.sh is not run a third time.

Full backend disposable tests (zero DB skips), snapshot, strict mypy and Ruff/format run at each completed domain/structural milestone; auth/schema/persistence/provider-sensitive tasks also require their relevant integration proof before verification is complete. Frontend route milestones run typecheck, zero-warning lint, four design lints, production build and affected route/state/keyboard/axe/viewport checks. Focused Taste review follows UI acceptance. Missing evidence stays unverified.

The complete release checklist and all numeric thresholds below remain mandatory. Evidence can satisfy multiple overlapping checks only when its revision, command, scope, environment and fixtures match. Final evaluation runs the complete candidate gate set; no test, assertion or threshold is removed.

---

## 6. Definition of done

- Every route in A.2 renders the neo-brutal design at 320, 375, 768, 1440 and 32:9 without overflow, with all five states, and with all existing features, copy strings, hooks, charts and modals.
- Motion M1–M14 exist and are each disabled under reduced motion.
- Backend:
  - `main.py` ≤ 120 lines;
  - ruff, ruff format and mypy strict all exit 0;
  - pytest coverage ≥ 80% with no skipped DB tests;
  - migration ledger in place;
  - JWT revocation, CORS allow-list and security headers in place;
  - simulator writes batched off the event loop;
  - N+1 removed;
  - DBMS showcase (isolation, deadlock, views/MV, window functions, EXPLAIN ANALYZE, audit trigger, roles/RLS) live on `/dbms`.
- `npm audit --audit-level=high` and `pip-audit` clean.
- The real-stack E2E project and visual regression are green in CI.
- The aggregate score is ≥ 95, every hard gate passes and nothing is NOT_RUN, as shown by `bash scripts/eval/score.sh` output pasted into `FINAL_REPORT.md`.

---

## Appendix A — Resume without duplicating the protocol

New models start at `.agent/START_HERE.md`; it identifies the current pause and first bounded domain action.

1. Read AGENTS.md, .agent/CURRENT_STATE.md and .agent/NEXT_STATE.md. Respect the recorded pause; the owner must say start work before implementation resumes.
2. Use .agent/protocol/delivery-workflow.md for execution, roles.md for configured workers, packets.md for isolation/acceptance, and evaluation.md for scoring. Do not paste a second copy of those rules into this plan.
3. Confirm overhaul/neo-brutal, inspect dirty/in-flight work and run boot.sh once. Keep user-owned scripts and unrelated edits untouched.
4. Read only the architecture/contracts and plan sections needed for the next coherent domain task. Use final T-331/T-332 boundaries; do not resume the superseded T-44573 assembly-only packet.
5. Dispatch at most two configured workers with disjoint target files. Preserve every requirement in sections 1–3 and the final gates in section 6.
6. Report accepted outcomes and evidence at a milestone; do not claim completion before the final score and hard gates pass. T-432 still opens a PR and waits for the owner.
