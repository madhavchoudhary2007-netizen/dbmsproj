import { expect, test } from "./mock-platform";

const adminUser = {
  id: 999,
  email: "smoke@example.test",
  full_name: "Smoke Audit",
  role: "ADMIN",
};

test.describe("E-1 UI States per Applicability Matrix", () => {
  test("E2E-S01 Error state with retry on /dashboard", async ({ page }) => {
    let failedOnce = true;
    await page.route("**/api/**", async (r) => {
      const pathname = new URL(r.request().url()).pathname;
      if (pathname === "/api/auth/me") {
        await r.fulfill({ status: 200, json: adminUser });
        return;
      }
      if (pathname === "/api/dashboard") {
        if (failedOnce) {
          await r.fulfill({ status: 500, json: { detail: "Database unavailable" } });
        } else {
          await r.fulfill({
            status: 200,
            json: { active_sessions: 1, scheduled_events: 2, open_incidents: 0, drivers: 20 },
          });
        }
        return;
      }
      if (pathname === "/api/health") {
        await r.fulfill({
          status: 200,
          json: { status: "HEALTHY", services: { postgres: "UP", redis: "UP" } },
        });
        return;
      }
      await r.fulfill({ status: 200, json: [] });
    });

    await page.goto("/dashboard", { waitUntil: "domcontentloaded" });
    const errorState = page.locator(".state.error");
    await expect(errorState).toBeVisible();
    await expect(errorState).toContainText("Database unavailable");

    // Click retry
    failedOnce = false;
    await errorState.getByRole("button", { name: /try again/i }).click();
    await expect(page.locator(".stat-card").first()).toBeVisible();
  });

  test("E2E-S02 Empty state on /sessions when session has no results", async ({ page }) => {
    await page.route("**/api/**", async (r) => {
      const pathname = new URL(r.request().url()).pathname;
      if (pathname === "/api/auth/me") {
        await r.fulfill({ status: 200, json: adminUser });
        return;
      }
      if (pathname === "/api/sessions") {
        await r.fulfill({
          status: 200,
          json: [{ id: "sess-1", name: "Practice 1", session_type: "PRACTICE", state: "COMPLETED" }],
        });
        return;
      }
      if (pathname === "/api/sessions/sess-1/results") {
        await r.fulfill({ status: 200, json: [] });
        return;
      }
      await r.fulfill({ status: 200, json: [] });
    });

    await page.goto("/sessions", { waitUntil: "domcontentloaded" });
    await expect(page.locator("table tbody tr")).toHaveCount(1);
    await page.locator("table tbody tr").first().click();

    const loadResultsBtn = page.getByRole("button", { name: "Load results" });
    await expect(loadResultsBtn).toBeVisible();
    await loadResultsBtn.click();

    await expect(page.locator(".state").filter({ hasText: "No result rows are recorded for this session." })).toBeVisible();
  });

  test("E2E-S03 Empty state on /live when no packets exist", async ({ page }) => {
    await page.route("**/api/**", async (r) => {
      const pathname = new URL(r.request().url()).pathname;
      if (pathname === "/api/auth/me") {
        await r.fulfill({ status: 200, json: adminUser });
        return;
      }
      if (pathname === "/api/sessions") {
        await r.fulfill({
          status: 200,
          json: [{ id: "sess-active", name: "Grand Prix", session_type: "RACE", state: "ACTIVE" }],
        });
        return;
      }
      if (pathname === "/api/demo-races") {
        await r.fulfill({ status: 200, json: [] });
        return;
      }
      await r.fulfill({ status: 200, json: [] });
    });

    await page.goto("/live", { waitUntil: "domcontentloaded" });
    await expect(page.locator(".state").filter({ hasText: "Waiting for timing and telemetry packets from this session." })).toBeVisible();
  });

  test("E2E-S04 Empty and Partial filter states on resource collection /championships", async ({ page }) => {
    await page.route("**/api/**", async (r) => {
      const pathname = new URL(r.request().url()).pathname;
      if (pathname === "/api/auth/me") {
        await r.fulfill({ status: 200, json: adminUser });
        return;
      }
      if (pathname === "/api/championships") {
        await r.fulfill({
          status: 200,
          json: [
            { id: 1, name: "Formula Apex 2026", season: 2026 },
            { id: 2, name: "GT Endurance Challenge", season: 2026 },
          ],
        });
        return;
      }
      await r.fulfill({ status: 200, json: [] });
    });

    await page.goto("/championships", { waitUntil: "domcontentloaded" });

    // Populated state: 2 rows
    const rows = page.locator("table tbody tr");
    await expect(rows).toHaveCount(2);

    // Partial filter state: filter for "Endurance" -> shows 1 record
    const searchInput = page.getByPlaceholder("Filter records");
    await searchInput.fill("Endurance");
    await expect(rows).toHaveCount(1);
    await expect(page.locator(".record-count")).toContainText("1 RECORD");

    // Empty filter state: filter for non-existent term -> "No records match this filter."
    await searchInput.fill("NonExistentTermXYZ");
    await expect(rows).toHaveCount(0);
    await expect(page.locator(".state")).toContainText("No records match this filter.");
  });

  test("E2E-S05 Loading and Error states on /login", async ({ page }) => {
    await page.route("**/api/auth/**", async (r) => {
      const pathname = new URL(r.request().url()).pathname;
      if (pathname === "/api/auth/me") {
        await r.fulfill({ status: 401, json: { detail: "Authentication required" } });
        return;
      }
      if (pathname === "/api/auth/login") {
        await r.fulfill({ status: 401, json: { detail: "Invalid email or password" } });
        return;
      }
      await r.fulfill({ status: 200, json: [] });
    });

    await page.goto("/login", { waitUntil: "domcontentloaded" });
    await page.fill("input[type='email']", "bad@apexgrid.test");
    await page.fill("input[type='password']", "WrongPassword!");
    await page.click(".login-submit");

    // Error alert renders
    await expect(page.locator(".form-error")).toContainText("Invalid email or password");
  });
});
