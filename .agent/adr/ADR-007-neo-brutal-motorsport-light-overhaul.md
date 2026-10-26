# ADR-007 — Neo-brutal motorsport (light) overhaul

Status: ACCEPTED — owner approved in chat on 2026-10-23
Execution clarification: ADR-014/015/016 supersede historical packet-size/cadence instructions below. Decision-time implementation/approval observations are history; current state determines remaining work. Visual, API, safety and scoring decisions remain active.
Date: 2026-10-23
Branch: overhaul/neo-brutal, based on perfection-loop 1acf8e1

## Context

The owner supplied docs/overhaul-plan.md and explicitly requested a frontend redesign plus backend hardening in place. The locked architecture currently retains the dark identity and forbids visual redesign. Its old score and state are historical; the plan records Ruff 540, format 23 files, mypy 222, frontend lint 2 errors and npm audit 7 high/2 moderate. No fresh overhaul quality score is claimed. T-300 boot passed on the Codex harness. No frontend/backend file has changed in Phase 0.

Approval evidence: owner message "ok approved continue", followed by "dont stop you have all permissions". T-302 is satisfied. Proceed through the plan with individual ADRs, contract preservation, isolated database testing and unchanged thresholds; no destructive or production action is authorized by this record.

## Decision

1. **Archetype and scope.** Adopt **Neo-Brutal Motorsport (light)** as the visual identity, retaining Enterprise SaaS/Analytics interaction density and the Developer Tool DBMS sub-area. Permit frontend visual redesign. Preserve all race flows, SQL rules, routes, methods, response contracts and persisted IDs; retain every feature, chart, modal, tested copy string, data hook, aria name, state class and /dbms hash route. No wholesale rewrite or data reset.
2. **Palette gate with unchanged bands.** In palette.spec.ts replace body background luminance <=0.12 with >=0.85; heading contrast remains >=4.5. A-3 role string becomes `#FFFDF5,#FFFFFF,#FF6B6B`. Keep the current scorer's exact bands: dominant 50–70%, secondary 20–40%, accent 5–15%, nearest-role distance-squared <=900. The plan's 55–65/25–35/7–12 design targets are tighter layout targets, not replacement/widened gates. Change layout when a route misses a band.
3. **Colour and type.** Cream/paper surfaces, black text/borders, red primary action; yellow, violet and mint communicate domain/status, sky is data-only. At most three accent colours per viewport. Black text on #FF6B6B; never white. Tyres retain S/M/H/I/W text. Space Grotesk 500/700 gives a motorsport display face; Space Mono 400/700 makes timing, IDs, SQL and JSON readable with tabular numbers. No 900 weight. Fonts load through next/font and self-hosted production output.
4. **Borders, radius, shadows.** Radius only 0 or 9999px for the specified circular/pill controls. Pure black hard shadows with zero blur and offsets <=16px are permitted; mobile offsets <=8px. Any blur >0 is banned, stricter than the old >16px rule. A deliberate border + hard shadow + solid surface is allowed for the archetype; redundant layers remain a Taste defect. Shadows never animate: only the .nb-face moves over a static plinth.
5. **A-2 lint additions.** Gradients only in frontend/app/styles/textures.css; no gray-family utilities or neutral hexes except black/white; no midrange radius, blur(), or font-weight:900; no white text on #FF6B6B. Decorative textures/outlined duplicates are aria-hidden, never under data or readable text without solid backing. No new motion library.
6. **Typography and motion limits.** Display line-height 1.0 is allowed only when computed size >=48px; smaller display text uses heading leading >=1.2. Body stays 1.5. Owner hard rules restrict animated properties to transform, opacity and background-color, durations 100–300ms, each with reduced-motion fallback. The longer M4/M6/M7/M8/M9 durations in plan section2.7 and the 40px display minimum conflict with those rules: T-440 must align those specifications before their packets are dispatched. No duration/contrast/spacing threshold is relaxed.
7. **States and accessibility.** Every data region retains empty/loading/populated/error/partial states and copy. Exactly one data-primary per viewport/route; targets >=44x44; keyboard/focus/dialog return retained; no overflow at 320,375,768,1440,5120. Existing tests stay; T-441 closes the heading-contrast assertion's >1 filter gap without ignoring real headings or weakening 4.5.
8. **Additive backend work only.** Plan Phases 2–4 may propose security/health additions, JWT revocation migration004 (ADR-008), configurable points migration005 (ADR-009), and DBMS showcase migrations/routes (ADR-010). Each change receives its own ADR; any path/method/response-shape alteration hits the owner's approval stop before implementation. Migrations run only on disposable apexgrid-test; no drop/rewrite/real database change. Existing OpenAPI snapshot becomes a permanent gate after T-330.
9. **CI and honest scoring.** CI triggers push on perfection-loop, master and overhaul/** plus every PR. T-314 adds Functional F-7 Ruff check+format weight2, F-8 strict mypy weight2, F-9 audit weight1. Add F-2 to hard gates alongside F-1/F-3/F-4/F-5/P-6. Aggregate >=95, zero failed hard gates, tests actually collected, no skipped DB tests, and no NOT_RUN are required. Score changes are implemented only after approval; no threshold is lowered.
10. **Execution.** At most two packet-isolated workers; W1 markup/styles, W2 runtime/backend, W3 tests/eval. Split oversized plan rows into <=3-file/150-line packets; separate logic and markup moves. T-325 is test-only and routes to W3 despite its plan W2 label. Orchestrator verifies and commits through accept.sh only. T-432 opens a PR and waits; never merge or force-push.

## Consequences

- T-301 amends and relocks A.4/A.5/B.5 plus this focused review. T-302 stops for owner approval; no worker/product task, gate change, font install or migration precedes it.
- After approval, Phase 1 establishes a measured baseline before visual work; security, API snapshot and DBMS/backend phases follow the dependency graph. Frontend foundation may interleave only where the plan permits disjoint worker targets.
- Existing palette tests will deliberately fail during a transition once T-360 activates the approved light gate. They remain failing checks until layouts pass; no skip/rebaseline shortcut.
- Historical score100 is not the overhaul score. Results must include command exit codes/counts and F-7..F-9; unavailable checks count as failed for delivery.
- scripts/agent/lock.sh unconditionally commits. The owner's accept.sh-only instruction therefore requires producing the same canonical SHA256 lock banner without its Git tail, then verifying and committing through accept.sh. The script itself is unchanged.

## Focused Phase C (A.4, A.5, B.5 and gate proposal)

| Lens | Trace/finding and amendment | Owner / binary evidence |
|---|---|---|
| 1 Goal | Preserve R01–R16 and API01–12; create/operate/inspect/archive flows survive. No route removed; later contract additions separately approved. | T-330 snapshot before refactors; T-380..393 route suites; T-411 real-stack journeys |
| 2 Verification | Old100 omits backend quality. Add F-7..F-9, hard F-2, collected-test and no-NOT_RUN delivery rules; preserve exact palette bands and contrast. | T-314 score.sh; T-360 lint self-tests; T-414 matrix; T-430 evaluation |
| 3 Restraint | New light palette, font, zero-blur shadows and limited textures conflict with generic visual protocol. Define narrow archetype exceptions, one red primary, max3 accents, no motion library. | T-400 Taste screenshots; A-1..A-7 and bundle gate |
| 4 Technical | Preserve API/storage and isolate migrations. Existing lock helper commits outside accept; generate identical banner directly. Large mixed plan rows need atomic role-respecting splits. | verify-lock.sh; T-330 snapshot; disposable full pytest; accept.sh per packet |
| 5 Boundaries | Display clamp falls below48 and M4/M6..9 exceed300ms. Enforce owner limits; T-440 aligns plan before motion packets. Palette test's >1 filter can hide failed real-heading contrast; T-441 closes it. | T-440 doc alignment; T-441 regression fixture; T-413/414 at five widths/reduced motion |

Pass1 amended the proposal for the palette-band distinction, motion/display conflicts, heading test gap and W3 test ownership. Pass2 reviewed all five lenses with those amendments and produced zero additional architecture amendments. T-440/T-441 are implementation prerequisites, not passing test claims.

## Risks and approval boundary

- Owner approval was received at T-302; future implementation still needs the scoped verification and ADRs required by this decision.
- Motion catalogue needs alignment (T-440); retaining long durations would violate the owner rule. The draft authorizes no exception for them.
- Semantic colours/textures can reduce counted palette pixels; routes must still meet unchanged role bands through layout.
- Large refactors, changed response models and Docker/CI changes require scoped proof and applicable approval; the plan's desired end state is not a passing baseline.

## Sections affected

- ARCHITECT.md A.4, A.5, B.5 and focused ADR-007 Phase C/Risks.
- After approval only: design-visual/archetype interpretation, palette/lint tests at T-360, CI at T-313, evaluation.md/score.sh at T-314. These files are unchanged in T-301.
