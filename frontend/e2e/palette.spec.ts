import { expect, test } from "@playwright/test";
import sharp from "sharp";
import { scorePixels } from "../../scripts/eval/palette-core";
import { measurePalette } from "./palette-measure";

const adminUser = {
  id: 999,
  email: "smoke@example.test",
  full_name: "Smoke Audit",
  role: "ADMIN",
};

const routes = [
  ["E2E-R01", "/"],
  ["E2E-R02", "/login"],
  ["E2E-R03", "/dashboard"],
  ["E2E-R04", "/live"],
  ["E2E-R05", "/sessions"],
  ["E2E-R06", "/stewards"],
  ["E2E-R07", "/pit-wall"],
  ["E2E-R08", "/championships"],
  ["E2E-R09", "/events"],
  ["E2E-R10", "/circuits"],
  ["E2E-R11", "/standings"],
  ["E2E-R12", "/teams"],
  ["E2E-R13", "/drivers"],
  ["E2E-R14", "/users"],
  ["E2E-R15", "/analytics"],
  ["E2E-R16", "/dbms"],
] as const;

for (const [id, route] of routes) {
  test(`${id} ${route} colour discipline at 1440px matches light archetype`, async ({ page }, testInfo) => {
    await page.route("**/api/**", async (routeRequest) => {
      const pathname = new URL(routeRequest.request().url()).pathname;
      if (pathname === "/api/auth/me") {
        if (route === "/login") {
          await routeRequest.fulfill({ status: 401, json: { detail: "Authentication required" } });
        } else {
          await routeRequest.fulfill({ status: 200, json: adminUser });
        }
        return;
      }
      if (pathname === "/api/dashboard") {
        await routeRequest.fulfill({
          status: 200,
          json: { active_sessions: 1, scheduled_events: 2, open_incidents: 0, drivers: 20 },
        });
        return;
      }
      if (pathname === "/api/health") {
        await routeRequest.fulfill({ status: 200, json: { status: "healthy" } });
        return;
      }
      if (pathname === "/api/championships") {
        await routeRequest.fulfill({
          status: 200,
          json: [{ id: 1, name: "Formula Apex 2026", season: 2026 }],
        });
        return;
      }
      if (pathname === "/api/dbms/overview") {
        await routeRequest.fulfill({
          status: 200,
          json: { postgres: { status: "connected" }, mongodb: { status: "connected" } },
        });
        return;
      }
      await routeRequest.fulfill({ status: 200, json: [] });
    });

    await page.goto(route, { waitUntil: "domcontentloaded" });

    if (page.viewportSize()?.width === 1440) {
      await page.evaluate(async () => {
        await document.fonts.ready;
        await new Promise<void>((resolve) => {
          requestAnimationFrame(() => requestAnimationFrame(() => resolve()));
        });
      });
      const screenshot = await page.screenshot({ fullPage: true });
      const { data, info } = await sharp(screenshot)
        .removeAlpha()
        .raw()
        .toBuffer({ resolveWithObject: true });
      const roleScore = scorePixels(data, info.channels);
      await testInfo.attach("palette-screenshot-1440", {
        body: screenshot,
        contentType: "image/png",
      });
      await testInfo.attach("palette-role-shares-1440", {
        body: Buffer.from(JSON.stringify({ ...roleScore, width: info.width, height: info.height, channels: info.channels }, null, 2)),
        contentType: "application/json",
      });
      expect(roleScore.ok, `A3 screenshot role shares: ${JSON.stringify(roleScore.share)}`).toBe(true);
    }

    const result = await page.evaluate(measurePalette);

    // Light archetype: background luminance >= 0.85
    expect(result.bgLum).toBeGreaterThanOrEqual(0.85);

    // Headings pass AA (>= 4.5:1) against parent when present
    for (const contrast of result.headingContrasts) {
      expect(contrast).toBeGreaterThanOrEqual(4.5);
    }
  });
}
