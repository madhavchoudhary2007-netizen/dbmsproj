# UX, accessibility and viewports (Pillars 3, 5, 6)

Read when: building data components, forms, dialogs or navigation, auditing accessibility, or checking responsive behavior. Visual rules are in `design-visual.md`.

## Pillar 3: the 5 mandatory UI states

Every data component takes this union and renders every variant; the exhaustive `switch` turns a missing state into a type error.

```ts
export type ViewState<T> =
  | { status: "empty"; reason: "no-data" | "first-use" }
  | { status: "loading" }
  | { status: "populated"; data: T }
  | { status: "error"; error: { message: string; retryable: boolean }; retry: () => void }
  | { status: "partial"; data: T; filter: { label: string; clear: () => void }; totalCount: number };

function assertNever(x: never): never { throw new Error(`Unhandled state: ${JSON.stringify(x)}`); }
// switch (state.status) { case "empty": … case "partial": …; default: return assertNever(state); }
```

| State | Requirement |
|---|---|
| Empty | Explains why it is empty; one next-action button; first-use and no-results are different messages |
| Loading skeleton | Same dimensions as the final content (CLS ≤ 0.05); appears only after 150ms; `aria-busy="true"` |
| Populated | Real content; tabular numbers where numeric |
| Error with retry | Human-readable cause; retry re-issues the same request; `role="alert"`; non-retryable errors give a next step instead |
| Partial/filtered | "Showing N of M" with a one-click clear; filter state in the URL query |

Each component gets a fixture route `/__fixtures/<name>?state=<status>` and a test per state asserting `data-testid="state-<status>"` is visible (check E-1).

**Forms:** label above the field, never placeholder-as-label; correct `type`, `inputmode` and `autocomplete`; validate on blur, then on change after the first error; link errors with `aria-describedby`; disable submit only while submitting, never for invalid input; preserve input on error.

**Touch targets:** every interactive element is at least 44×44px (padding or `::after` expansion allowed; inline paragraph links exempt).

```ts
test("touch targets ≥ 44×44 at 375px", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto("/");
  const small = await page.$$eval(
    "a:not(p a), button, input, select, textarea, [role=button], [tabindex='0']",
    els => els
      .filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && (r.width < 44 || r.height < 44); })
      .map(e => e.outerHTML.slice(0, 80)));
  expect(small).toEqual([]);
});
```

## Pillar 5: semantic DOM and WCAG 2.1 AA

- Landmarks: one `<header>`, labelled `<nav>` regions, one `<main id="main">`, `<footer>`. The first focusable element is a "Skip to content" link. One `<h1>` per page, no skipped heading levels.
- Dialogs use native `<dialog>` opened with `showModal()` (top layer, Escape to close, inert background, focus trap). Return focus to the trigger on close.
- Custom widgets follow WAI-ARIA Authoring Practices keyboard patterns (tabs: arrow keys; menus: arrows plus Escape; listbox: type-ahead).
- Focus: `:focus-visible { outline: 2px solid var(--color-accent); outline-offset: 2px; }`. Never `outline: none` without a replacement.
- Contrast: body text at least 4.5:1; large text (24px or more, or 18.66px bold) and UI component boundaries at least 3:1.

```ts
export function contrast(a: string, b: string): number {
  const L = (h: string) => {
    const [r, g, bl] = [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16) / 255)
      .map(c => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
    return 0.2126 * r + 0.7152 * g + 0.0722 * bl;
  };
  const [x, y] = [L(a), L(b)].sort((p, q) => q - p);
  return (x + 0.05) / (y + 0.05);
}
```

Automated audit on every route at every viewport (check P-6) and a keyboard check:

```ts
import AxeBuilder from "@axe-core/playwright";
test("no WCAG 2.1 AA violations", async ({ page }) => {
  await page.goto("/");
  const r = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
  expect(r.violations).toEqual([]);
});
test("keyboard reaches the primary action", async ({ page }) => {
  await page.goto("/");
  for (let i = 0; i < 30; i++) {
    await page.keyboard.press("Tab");
    if (await page.evaluate(() => document.activeElement?.getAttribute("data-primary") === "true")) return;
  }
  throw new Error("Primary action not reachable within 30 Tab presses");
});
```

Automated checks find only part of the accessibility defects, so the orchestrator also walks every A.2 path using the keyboard alone.

## Pillar 6: cross-viewport inspection

Copy `.agent/templates/playwright.config.ts` to the repo root. It defines five projects: 320×568, 375×812, 768×1024, 1440×900 and 5120×1440 (32:9). Per route per project:

```ts
test("no horizontal overflow", async ({ page }) => {
  await page.goto("/");
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow).toBeLessThanOrEqual(0);
});
test("screenshot baseline", async ({ page }, info) => {
  await page.goto("/");
  await expect(page).toHaveScreenshot(`home-${info.project.name}.png`, { fullPage: true, maxDiffPixelRatio: 0.01 });
});
```

**The `min-w-0` fix:** flex items default to `min-width: auto` and refuse to shrink below their content width, so a long string or wide table overflows. Give every flex child that holds user content or a scroller `min-w-0`, and write grid tracks as `minmax(0, 1fr)` instead of `1fr`:

```tsx
<div className="flex gap-4">
  <aside className="w-64 shrink-0" />
  <main className="min-w-0 flex-1"><DataTable /></main>
</div>
```

On ultra-wide screens use `max-width: 1440px; margin-inline: auto` for app shells and `68ch` for prose; go full-bleed only for media and data canvases.
