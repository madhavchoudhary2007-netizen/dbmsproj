# Project archetype matrix

Read when: classifying a project (architect Phase A.4) or choosing tokens, type, motion and density.

**Classify:** score the request, +1 per matching signal, and take the highest archetype. Ties go to the archetype whose primary user spends the most minutes per session (Enterprise, then Developer, Consumer, Editorial). If the top score is 0 or the tie cannot be broken, ask one question: "Is this for repeated professional work, technical users, everyday consumers, or reading and brand storytelling?" Record the result and signal counts in ARCHITECT A.4.

| | Enterprise SaaS / Analytics | Consumer / Lifestyle | Developer / Technical Tool | Editorial / Luxury |
|---|---|---|---|---|
| Signals | tables, dashboards, filters, roles, exports, multi-tenant, KPIs, audit logs, bulk actions | onboarding, social, habits, shopping, health, mobile-first, notifications, streaks | CLI, logs, API keys, code, terminals, diffs, observability, docs, keyboard-driven | articles, storytelling, portfolio, launch, brand, long-form, photography |
| Density | High: rows 32–36px, cell padding 8×12 | Low: card padding 24–32, section gap 64 | High: rows 28–32, padding 4×8 | Hero 100svh, measure 60–72ch |
| Base step | 4px | 8px | 4px | 8px |
| Palette | Neutral slate/zinc plus one desaturated accent | Warm stone/sand plus one saturated accent | Dark #0B0D10–#16181D plus one high-luminance accent | Off-white/ink or near-black/cream; accent ≤ 5% |
| Type | Sans (Geist, IBM Plex Sans); tabular-nums on all numbers, mono for IDs; ratio 1.125 | Rounded sans (Manrope, Nunito Sans); ratio 1.25 | Sans plus mono (Geist plus Geist Mono); mono numerics; ratio 1.125 | Serif display (Fraunces, Playfair) plus neutral sans; oldstyle body numerals; ratio 1.333–1.5 |
| Radius | 4–6px | 12–20px | 2–6px | 0–2px |
| Motion | 100–150ms, `cubic-bezier(0.2,0,0,1)` | 200–400ms springs (stiffness 300, damping 30) | ≤ 100ms, cuts preferred | 400–900ms reveals, `cubic-bezier(0.16,1,0.3,1)` |
| Elevation | 1px borders; shadow only on overlays | One soft shadow: `0 1px 2px rgb(0 0 0/.06), 0 4px 12px rgb(0 0 0/.06)` | 1px borders only | None; whitespace and rules |
| Primary input | Mouse plus shortcuts | Touch | Keyboard, `⌘K` command palette | Scroll |

W1 emits `src/styles/tokens.css` before any component. Every color pair carries its contrast ratio in a trailing comment (formula in `design-ux.md`, Pillar 5). Enterprise example:

```css
:root {
  --space-1: 4px; --space-2: 8px; --space-3: 12px; --space-4: 16px;
  --space-6: 24px; --space-8: 32px; --space-12: 48px; --space-16: 64px;
  --color-surface: #ffffff;       /* 60% */
  --color-surface-muted: #f4f5f7; /* 30% */
  --color-border: #e3e5e8;
  --color-text: #15171a;          /* 15.9:1 on surface */
  --color-text-muted: #5b6168;    /* 6.3:1 */
  --color-accent: #2f5bd3;        /* 10%; 6.2:1 */
  --color-accent-fg: #ffffff;
  --color-danger: #b42318; --color-success: #067647;
  --radius-sm: 4px; --radius-md: 6px;
  --dur-fast: 100ms; --dur-base: 150ms; --ease-standard: cubic-bezier(0.2, 0, 0, 1);
  --font-sans: "Geist", "IBM Plex Sans", system-ui, sans-serif;
  --font-mono: "Geist Mono", "JetBrains Mono", ui-monospace, monospace;
}
```
