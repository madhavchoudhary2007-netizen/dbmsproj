import { expect, test } from "@playwright/test";

const adminUser = {
  id: 999,
  email: "admin@apexgrid.test",
  full_name: "Admin User",
  role: "ADMIN",
};

test("E-4 rapid input spam fires exactly one request", async ({ page }) => {
  let loginRequests = 0;
  await page.route("**/api/**", async (route) => {
    const pathname = new URL(route.request().url()).pathname;
    if (pathname === "/api/auth/me") {
      await route.fulfill({ status: 401, json: { detail: "Authentication required" } });
      return;
    }
    if (pathname === "/api/auth/login") {
      loginRequests++;
      await new Promise((r) => setTimeout(r, 150));
      await route.fulfill({ status: 200, json: { user: adminUser } });
      return;
    }
    await route.fulfill({ status: 200, json: {} });
  });

  await page.goto("/login", { waitUntil: "domcontentloaded" });
  await page.getByPlaceholder("name@team.com").fill("admin@apexgrid.test");
  await page.getByPlaceholder("Enter your password").fill("secret123");

  const button = page.getByRole("button", { name: /sign in/i });

  await Promise.all([
    button.click({ force: true }).catch(() => {}),
    button.click({ force: true }).catch(() => {}),
    button.click({ force: true }).catch(() => {}),
    button.click({ force: true }).catch(() => {}),
    button.click({ force: true }).catch(() => {}),
    button.click({ force: true }).catch(() => {}),
  ]);

  await page.waitForTimeout(300);
  expect(loginRequests).toBe(1);
});

test("E-5 offline to online recovery passes with retry", async ({ page, context }) => {
  let isOffline = false;
  await page.route("**/api/**", async (route) => {
    const pathname = new URL(route.request().url()).pathname;
    if (pathname === "/api/auth/me") {
      await route.fulfill({ status: 200, json: adminUser });
      return;
    }
    if (isOffline) {
      await route.abort("failed");
      return;
    }
    if (pathname === "/api/dashboard") {
      await route.fulfill({
        status: 200,
        json: {
          active_sessions: 2,
          scheduled_events: 5,
          open_incidents: 1,
          drivers: 20,
          active_session: { id: "s-1", name: "Grand Prix", circuit_name: "Silverstone", status: "RUNNING" },
        },
      });
      return;
    }
    if (pathname === "/api/health") {
      await route.fulfill({
        status: 200,
        json: { status: "healthy", services: { postgres: "healthy", mongodb: "healthy" } },
      });
      return;
    }
    await route.fulfill({ status: 200, json: [] });
  });

  await page.goto("/dashboard", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { name: "Race operations" })).toBeVisible();

  // Simulate network offline via route abort and context offline
  isOffline = true;
  await context.setOffline(true);

  // Trigger Refresh
  const refreshButton = page.getByRole("button", { name: "Refresh" });
  await refreshButton.click();

  // StateMessage renders role="alert" with "Try again" button
  const errorAlert = page.locator(".state.error");
  await expect(errorAlert).toBeVisible({ timeout: 5000 });
  const tryAgain = errorAlert.getByRole("button", { name: "Try again" });
  await expect(tryAgain).toBeVisible();

  // Restore network online
  isOffline = false;
  await context.setOffline(false);

  // Click Try again
  await tryAgain.click();

  // Error alert disappears and stats are visible
  await expect(errorAlert).not.toBeVisible({ timeout: 5000 });
  await expect(page.getByText("scheduled events")).toBeVisible();
});

test("E-2 Lens 5 navigation mid-request aborts cleanly without errors", async ({ page }) => {
  const failures: string[] = [];
  page.on("pageerror", (err) => failures.push(`pageerror: ${err.message}`));
  page.on("console", (msg) => {
    if (msg.type() === "error") failures.push(`console: ${msg.text()}`);
  });

  await page.route("**/api/**", async (route) => {
    const pathname = new URL(route.request().url()).pathname;
    if (pathname === "/api/auth/me") {
      await route.fulfill({ status: 200, json: adminUser });
      return;
    }
    await new Promise((r) => setTimeout(r, 1000));
    await route.fulfill({ status: 200, json: {} });
  });

  void page.goto("/dashboard");
  await page.waitForTimeout(50);
  await page.goto("/sessions", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { name: "Sessions" })).toBeVisible();

  expect(failures).toEqual([]);
});

test("E-2 Lens 5 long unbroken string wraps without horizontal overflow", async ({ page }) => {
  const longString = "A".repeat(140);
  await page.route("**/api/**", async (route) => {
    const pathname = new URL(route.request().url()).pathname;
    if (pathname === "/api/auth/me") {
      await route.fulfill({ status: 200, json: adminUser });
      return;
    }
    if (pathname === "/api/championships") {
      await route.fulfill({ status: 200, json: [{ id: 1, name: longString, season: 2026 }] });
      return;
    }
    await route.fulfill({ status: 200, json: [] });
  });

  await page.goto("/championships", { waitUntil: "domcontentloaded" });
  await expect(page.getByText(longString)).toBeVisible();

  const extent = await page.evaluate(() => ({
    document: document.documentElement.scrollWidth,
    viewport: document.documentElement.clientWidth,
  }));
  expect(extent.document).toBeLessThanOrEqual(extent.viewport + 1);
});
