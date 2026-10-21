# Visual design: art direction, tokens, motion (Pillars 1, 2, 4)

Read when: writing or reviewing `.tsx`, `.jsx`, `.css`, tokens or animation. UX states, accessibility and viewport checks are in `design-ux.md`.

## Pillar 1: art direction and anti-AI-slop

| Banned | Instead |
|---|---|
| Unstyled Inter or Roboto as the only face | Archetype face (`archetypes.md`); a deliberate Inter needs a defined pairing and `font-feature-settings: "cv11","ss01"` |
| Purple-on-black gradients | Solid surface, one accent |
| Heavy shadows (`shadow-xl/2xl`, blur over 16px off overlays) | `1px solid var(--color-border)` |
| Glassmorphism on content | Opaque surface (sticky headers excepted) |
| Emoji as UI icons | Archetype icon set |
| Generic copy ("unlock the power", "seamless", "supercharge") | A concrete statement of what the product does |
| Everything centered (Taste Agent) | Left-align any text over 2 lines |

`bash scripts/eval/lint-banned.sh` enforces the first six and exits 1 on any hit (check A-2).

**60-30-10:** in a full-page screenshot the dominant surface covers 50–70%, secondary surfaces 20–40%, the accent 5–15%; text and imagery pixels are excluded. Check: `npx tsx scripts/eval/palette.ts shot.png "#ffffff,#f4f5f7,#2f5bd3"` (needs `sharp`). Separation hierarchy: whitespace, then 1px border, then background tint, then shadow (floating elements only).

## Pillar 2: mathematical tokens

The only legal spacing values are **4, 8, 12, 16, 24, 32, 48 and 64px** (`--space-1` to `--space-16`); larger gaps are multiples of 64. `bash scripts/eval/lint-spacing.sh` flags any other pixel value in spacing properties and Tailwind arbitrary values like `p-[10px]` (check A-1). Restrict Tailwind to the same scale:

```js
// tailwind.config.js
export default { theme: { spacing: { 0: "0", px: "1px", 1: "4px", 2: "8px", 3: "12px", 4: "16px", 6: "24px", 8: "32px", 12: "48px", 16: "64px", 32: "128px" } } };
```

**Fluid type.** Size grows from `minPx` at viewport `vwMin` to `maxPx` at `vwMax`:

```
slope     = (maxPx − minPx) / (vwMax − vwMin)
intercept = minPx − slope · vwMin
font-size: clamp(minPx/16 rem, intercept/16 rem + slope·100 vw, maxPx/16 rem)
```

Worked example, body 16px to 20px across 375px to 1440px: slope 0.003756, intercept 14.592px = 0.912rem, so `--text-body: clamp(1rem, 0.912rem + 0.3756vw, 1.25rem);` gives 16.00px at 375px and 20.00px at 1440px. For other steps compute `minPx = base · ratio^step` with the archetype ratio and let each step grow 20% from smallest to largest viewport. Line height: body 1.5, headings of 24px or more 1.2, otherwise 1.35. Body measure `max-width: 68ch`.

## Pillar 4: tactile motion

1. Pressable elements use `active:scale-[0.98]` with `transition: transform var(--dur-fast) var(--ease-standard)`.
2. Transition named properties only; `transition: all` and `transition-all` are banned.
3. Animate only `transform` and `opacity`. Never animate width, height, top, left, margin or box-shadow on interaction.
4. Every animation sits inside a reduced-motion guard. JS animation reads `useReducedMotion()` and swaps movement for opacity fades of 150ms or less.

```css
.btn {
  transition:
    transform var(--dur-fast) var(--ease-standard),
    background-color var(--dur-base) var(--ease-standard),
    color var(--dur-base) var(--ease-standard);
}
.btn:active { transform: scale(0.98); }

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

`bash scripts/eval/lint-motion.sh` enforces rules 2 and 3 and requires a reduced-motion guard whenever transitions or animations exist (check A-7).
