import { expect, test } from "@playwright/test";
import { measurePalette } from "./palette-measure";

test("black text on black heading is measured and fails AA", async ({ page }) => {
  await page.setContent('<div style="background: black"><h1 style="color: black">Hidden</h1></div>');
  const result = await page.evaluate(measurePalette);

  expect(result.headingContrasts).toEqual([1]);
  expect(() => expect(result.headingContrasts[0]).toBeGreaterThanOrEqual(4.5)).toThrow();
});

test("contrasting real heading passes and aria-hidden duplicate is excluded", async ({ page }) => {
  await page.setContent(
    '<div style="background: black"><h1 style="color: white">Visible</h1>' +
      '<section aria-hidden="true"><h2 style="color: black">Decoration</h2></section></div>',
  );
  const result = await page.evaluate(measurePalette);

  expect(result.headingContrasts).toHaveLength(1);
  expect(result.headingContrasts[0]).toBeGreaterThanOrEqual(4.5);
});

test("transparent nested backgrounds resolve to the nearest opaque ancestor", async ({ page }) => {
  await page.setContent(
    '<div style="background: blue"><section style="background: transparent">' +
      '<h3 style="color: white">Visible</h3></section></div>',
  );
  const result = await page.evaluate(measurePalette);

  expect(result.headingContrasts).toHaveLength(1);
  expect(result.headingContrasts[0]).toBeCloseTo(8.59, 2);
  expect(result.headingContrasts[0]).toBeGreaterThanOrEqual(4.5);
});
