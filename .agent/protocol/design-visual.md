# ApexGrid visual rules — approved light overhaul

Read only for UI/style/token work. This protocol adopts docs/overhaul-plan.md section 2 and ADR-007 as the project design contract; it replaces generic kit examples. delivery-workflow.md owns verification cadence. No generic dark palette, font, radius or soft-shadow alternative is active.

## Tokens and palette
- Use existing approved token files; do not generate a new src/styles/tokens.css or Tailwind setup. Fonts: Space Grotesk 500/700 and Space Mono 400/700, with current next/font loading. No 900 weight.
- Spacing only 0/4/8/12/16/24/32/48/64px. Border widths and shadow offsets follow their separate approved tokens, not spacing exemptions. Do not add 1px/128px spacing from generic examples.
- Palette roles: cream #FFFDF5, paper #FFFFFF, red #FF6B6B. A-3 bands remain 50–70 / 20–40 / 5–15 with the existing scorer; meet them through layout. The plan's tighter targets do not replace gates.
- Ink #000000 for text/borders. Yellow/violet/mint communicate domain/status; sky is data-only. Maximum three accent colours per viewport. Never white text on #FF6B6B. Preserve tyre letters and other non-colour signals.
- No gray-family utilities, neutral hexes other than black/white, blur or gradients outside frontend/app/styles/textures.css. Approved textures/outlined duplicates are aria-hidden; readable content needs solid backing.
- Radius only 0 or 9999px. Static pure-black hard shadows have zero blur, offset <=16px (<=8px mobile). Border + hard shadow + solid surface is permitted by the archetype. Do not apply a generic ban on that combination.

## Typography, hierarchy and restraint
- Exactly one data-primary per viewport/route; visible primary action and accessible name are distinct from mere accent-coloured status information. Preserve existing copy/hooks/ARIA/state classes.
- Display leading 1.0 only at computed size >=48px; smaller headings leading >=1.2; body 1.5. Use existing approved type tokens, not a new generic scale.
- Retain approved decorative motifs; assess texture backing, accent limits, sticker counts and hierarchy against the plan. Do not remove approved features/art solely to satisfy a generic anti-decoration rule.
- Taste file-size/single-call-site findings use roles.md and become bounded review tasks. A structural move never completes a gate merely by reducing line count.

## Motion
- Only transform, opacity or background-color; durations 100–300ms with reduced-motion fallback. No color, shadow, dimensions or positional-property animations. No transition:all.
- Shadows stay static on the plinth; only its face moves. Use the reconciled M1–M14 catalogue; no old long-running loop or 40px/leading-1.0 example overrides the owner limits.
- Reduced motion disables moving/ongoing animations; preserve information using static states. Existing reduced-motion tests remain mandatory; do not substitute short ongoing animation for a zero-running-animation assertion.

## Verification
Workers run only the packet's approved offline commands. Root runs affected route/state/keyboard/axe/viewport/browser checks at the required boundary. Apply spacing, banned, motion and neo-brutal lints as scoped by the packet; no prose claim asserts a lint covers a rule it does not check. No threshold, test or assertion may be weakened. UI acceptance gets focused Taste review; route milestones/final evaluation get screenshots under delivery-workflow.md.
