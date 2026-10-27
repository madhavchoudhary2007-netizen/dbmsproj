import { expect, test } from "./mock-platform";

const routes = [
  ["r01-root", "/"],
  ["r02-login", "/login"],
  ["r03-dashboard", "/dashboard"],
  ["r04-live", "/live"],
  ["r05-sessions", "/sessions"],
  ["r06-stewards", "/stewards"],
  ["r07-pit-wall", "/pit-wall"],
  ["r08-championships", "/championships"],
  ["r09-events", "/events"],
  ["r10-circuits", "/circuits"],
  ["r11-standings", "/standings"],
  ["r12-teams", "/teams"],
  ["r13-drivers", "/drivers"],
  ["r14-users", "/users"],
  ["r15-analytics", "/analytics"],
  ["r16-dbms", "/dbms"],
] as const;

for (const [snapshot, routePath] of routes) {
  test(`${snapshot} ${routePath} matches its visual baseline`, async ({ page }, testInfo) => {
    const unexpectedWrites: string[] = [];
    await page.route("**/api/**", async (route) => {
      const request = route.request();
      const pathname = new URL(request.url()).pathname;
      if (pathname.endsWith("/health/ready")) {
        await route.fallback();
        return;
      }
      if (request.method() !== "GET") {
        unexpectedWrites.push(`${request.method()} ${pathname}`);
        await route.fulfill({ status: 405, json: { detail: "Visual snapshots are read-only" } });
        return;
      }
      if (pathname.endsWith("/auth/me")) {
        if (routePath === "/login") {
          await route.fulfill({ status: 401, json: { detail: "Authentication required" } });
        } else {
          await route.fulfill({
            status: 200,
            json: {
              id: "visual-admin",
              email: "visual@example.test",
              full_name: "Visual Fixture",
              role: "ADMIN",
            },
          });
        }
        return;
      }
      if (pathname.endsWith("/health")) {
        await route.fulfill({
          status: 200,
          json: { status: "healthy", services: { postgres: "up", mongodb: "up" } },
        });
        return;
      }
      if (pathname.endsWith("/dashboard")) {
        await route.fulfill({
          status: 200,
          json: { active_sessions: 1, scheduled_events: 2, open_incidents: 0, drivers: 20 },
        });
        return;
      }
      if (pathname.endsWith("/championships")) {
        await route.fulfill({
          status: 200,
          json: [{ id: 1, name: "Formula Apex 2026", season: 2026 }],
        });
        return;
      }
      if (pathname.endsWith("/dbms/overview")) {
        await route.fulfill({
          status: 200,
          json: {
            active_sessions: 1,
            completed_sessions: 12,
            open_incidents: 2,
            reserved_pit_stops: 3,
            completed_pit_stops: 8,
            official_results: 12,
            telemetry_samples: 480,
            postgres: "up",
            mongodb: "up",
            updated_at: "2026-10-27T12:00:00Z",
          },
        });
        return;
      }
      await route.fulfill({ status: 200, json: [] });
    });

    await page.goto(routePath, { waitUntil: "domcontentloaded" });
    const expectedPath = routePath === "/" ? "/dashboard" : routePath;
    await expect(page).toHaveURL((url) => new URL(url).pathname === expectedPath);
    if (routePath === "/dbms") {
      const statusPanel = page.locator(".dbms-status-panel");
      await expect(statusPanel).toContainText("PostgreSQL · up");
      await expect(statusPanel).toContainText("MongoDB · up");
      await expect(statusPanel).not.toContainText("Connecting…");
    }
    const primaryScreen = page.locator("[data-primary='true']");
    await expect(primaryScreen).toHaveCount(1);
    await expect(primaryScreen).toBeVisible();
    await expect(primaryScreen).toHaveAccessibleName(/\S/);
    expect(unexpectedWrites).toEqual([]);
    await page.evaluate(async () => {
      await document.fonts.ready;
      await new Promise<void>((resolve) => {
        requestAnimationFrame(() => requestAnimationFrame(() => resolve()));
      });
    });

    // The fixed API fixtures contain no changing values, so no screenshot regions need masks.
    await expect(page).toHaveScreenshot(`${snapshot}-${testInfo.project.name}.png`, {
      animations: "disabled",
      caret: "hide",
      maxDiffPixelRatio: 0.01,
    });
  });
}
