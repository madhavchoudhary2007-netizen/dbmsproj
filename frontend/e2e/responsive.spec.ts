import { expect, test } from "@playwright/test";

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

const viewports = [320, 375, 768, 1024, 1440, 5120] as const;

for (const [id, route] of routes) {
  for (const width of viewports) {
    test(`${id} ${route} stays usable at ${width}px`, async ({ page }) => {
      const mutations: string[] = [];
      await page.addInitScript((routePath) => {
        if (routePath !== "/login") localStorage.setItem("apexgrid_token", "responsive-audit-token");
      }, route);
      await page.route("**/api/**", async (request) => {
        const method = request.request().method();
        const pathname = new URL(request.request().url()).pathname;
        if (method === "GET") {
          const body = pathname === "/api/auth/me"
            ? { id: 999, email: "responsive@example.test", full_name: "Responsive Audit", role: "admin" }
            : {};
          await request.fulfill({ json: body });
          return;
        }
        mutations.push(`${method} ${pathname}`);
        await request.abort();
      });

      await page.setViewportSize({ width, height: width < 500 ? 812 : 1000 });
      await page.goto(route, { waitUntil: "domcontentloaded" });
      await expect(page, `${id} ${route} at ${width}px must remain on the requested route`)
        .toHaveURL((url) => new URL(url).pathname === route);
      await expect.poll(() => page.locator("body").innerText(), {
        message: `${id} ${route} at ${width}px must render content`,
      }).toMatch(/\S/);
      const extent = await page.evaluate(() => ({
        document: document.documentElement.scrollWidth,
        viewport: document.documentElement.clientWidth,
      }));
      expect(extent.document, `${id} ${route} at ${width}px must not overflow horizontally`)
        .toBeLessThanOrEqual(extent.viewport + 1);

      const action = page.locator(
        "nav a:visible, nav button:visible, .mobile-menu:visible, main a:visible, main button:visible, header a:visible, header button:visible",
      ).first();
      await expect(action, `${id} ${route} at ${width}px needs a visible navigation/action`).toBeVisible();
      await action.click({ trial: true });
      let keyboardReached = false;
      for (let tab = 0; tab < 50; tab++) {
        await page.keyboard.press("Tab");
        if (await action.evaluate((element) => element === document.activeElement)) {
          keyboardReached = true;
          break;
        }
      }
      expect(keyboardReached, `${id} ${route} at ${width}px action must be keyboard reachable`).toBe(true);
      expect(mutations, `${id} ${route} at ${width}px must not send mutations`).toEqual([]);
    });
  }
}
