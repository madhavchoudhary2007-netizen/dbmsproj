import { test, expect, type Page } from "@playwright/test";

const ADMIN_CREDENTIALS = {
  email: "admin@apexgrid.test",
  password: "ApexGrid2026!",
};

async function signIn(page: Page): Promise<void> {
  await page.goto("/login");
  await expect(page.getByRole("heading", { name: "Sign in to ApexGrid" })).toBeVisible();

  await page.getByLabel("Email address").fill(ADMIN_CREDENTIALS.email);
  await page.getByLabel("Password").fill(ADMIN_CREDENTIALS.password);
  await page.getByRole("button", { name: /sign in/i }).click();

  await page.waitForURL("**/dashboard");
  await expect(page.getByRole("heading", { name: "Race operations" })).toBeVisible();
}

test.describe("Real-stack Journey Tests (Unmocked)", () => {
  test("Test 1: Sign in through UI at /login navigates to /dashboard and displays operational context", async ({
    page,
  }) => {
    const failures: string[] = [];
    page.on("pageerror", (err) => failures.push(`pageerror: ${err.message}`));
    page.on("response", (res) => {
      if (res.status() >= 500) failures.push(`${res.status()} ${res.url()}`);
    });

    await page.goto("/login");
    await expect(page.getByRole("heading", { name: "Sign in to ApexGrid" })).toBeVisible();

    await page.getByLabel("Email address").fill(ADMIN_CREDENTIALS.email);
    await page.getByLabel("Password").fill(ADMIN_CREDENTIALS.password);
    await page.getByRole("button", { name: /sign in/i }).click();

    await page.waitForURL("**/dashboard");
    await expect(page.getByRole("heading", { name: "Race operations" })).toBeVisible();
    await expect(page.locator(".dashboard-overview-grid")).toBeVisible();
    await expect(
      page.locator(".dashboard-context-card").or(page.locator(".dashboard-hero")),
    ).toBeVisible();

    expect(failures).toEqual([]);
  });

  test("Test 2: Live session & timing tower on /live with connected WebSocket status", async ({
    page,
  }) => {
    const failures: string[] = [];
    page.on("pageerror", (err) => failures.push(`pageerror: ${err.message}`));
    page.on("response", (res) => {
      if (res.status() >= 500) failures.push(`${res.status()} ${res.url()}`);
    });

    await signIn(page);

    await page.goto("/live");
    await expect(page.getByRole("heading", { name: "Live session" })).toBeVisible();

    await expect(
      page.locator(".nb-face").filter({ has: page.getByRole("heading", { name: "Live session" }) }).first(),
    ).toBeVisible();

    await expect(page.getByText("Connected · live stream", { exact: true }).first()).toBeVisible();

    expect(failures).toEqual([]);
  });

  test("Test 3: Standings recalculation on /standings with recalculate button", async ({
    page,
  }) => {
    const failures: string[] = [];
    page.on("pageerror", (err) => failures.push(`pageerror: ${err.message}`));
    page.on("response", (res) => {
      if (res.status() >= 500) failures.push(`${res.status()} ${res.url()}`);
    });

    await signIn(page);

    await page.goto("/standings");
    await expect(page.getByRole("heading", { name: "Standings" })).toBeVisible();

    await expect(page.locator("table").or(page.locator(".standings-data"))).toBeVisible();

    const recalcButton = page.locator('button[data-primary="true"]');
    await expect(recalcButton).toBeVisible();
    await recalcButton.click();

    await expect(page.getByText(/^Standings recalculated\..*"recalculated":true/)).toBeVisible();

    expect(failures).toEqual([]);
  });

  test("Test 4: Resource navigation across real database entities (/championships, /circuits, /teams, /drivers, /dbms)", async ({
    page,
  }) => {
    const failures: string[] = [];
    page.on("pageerror", (err) => failures.push(`pageerror: ${err.message}`));
    page.on("response", (res) => {
      if (res.status() >= 500) failures.push(`${res.status()} ${res.url()}`);
    });

    await signIn(page);

    await page.goto("/championships");
    await expect(page.getByRole("heading", { name: "Championships" })).toBeVisible();
    await expect(page.locator("table tbody tr").or(page.locator("article")).first()).toBeVisible();

    await page.goto("/circuits");
    await expect(page.getByRole("heading", { name: "Circuits" })).toBeVisible();
    await expect(page.locator("table tbody tr").or(page.locator("article")).first()).toBeVisible();

    await page.goto("/teams");
    await expect(page.getByRole("heading", { name: "Teams" })).toBeVisible();
    await expect(page.locator("table tbody tr").or(page.locator("article")).first()).toBeVisible();

    await page.goto("/drivers");
    await expect(page.getByRole("heading", { name: "Drivers" })).toBeVisible();
    await expect(page.locator("table tbody tr").or(page.locator("article")).first()).toBeVisible();

    await page.goto("/dbms");
    await expect(page.getByRole("heading", { name: "DBMS workspace" })).toBeVisible();
    await expect(page.getByText(/overview|postgresql/i).first()).toBeVisible();

    expect(failures).toEqual([]);
  });

  test("Test 5: Root redirects to login before authentication", async ({ page }) => {
    await page.goto("/");
    await page.waitForURL("**/login");
    await expect(page.getByRole("heading", { name: "Sign in to ApexGrid" })).toBeVisible();
    await expect(page.getByLabel("Email address")).toBeVisible();
    await expect(page.getByLabel("Password")).toBeVisible();
    await expect(page.getByRole("button", { name: /sign in/i })).toBeVisible();
  });

  test("Test 6: Session control loads API state and supports refresh", async ({ page }) => {
    await signIn(page);
    await page.goto("/sessions");
    await expect(page.getByRole("heading", { name: "Sessions" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Schedule session" })).toBeVisible();
    await page.getByRole("button", { name: "Refresh" }).last().click();
    const sessions = page.getByRole("table", { name: "Sessions" });
    await expect(sessions).toBeVisible();
    await expect(
      sessions.getByRole("row").nth(1).or(page.getByText("No records returned by the API.")),
    ).toBeVisible();
  });

  test("Test 7: Steward desk exposes incident cases and report control", async ({ page }) => {
    await signIn(page);
    await page.goto("/stewards");
    await expect(page.getByRole("heading", { name: "Steward desk" })).toBeVisible();
    await expect(page.getByRole("table", { name: "Incident case files" })).toBeVisible();
    const report = page.getByRole("button", { name: "Report incident" });
    await expect(report).toBeVisible();
    await report.click();
    await expect(page.getByRole("heading", { name: "Report incident" })).toBeVisible();
  });

  test("Test 8: Pit wall loads race control state and can refresh", async ({ page }) => {
    await signIn(page);
    await page.goto("/pit-wall");
    await expect(page.getByRole("heading", { name: "Pit Wall" })).toBeVisible();
    const refresh = page.locator('button[data-primary="true"]');
    await expect(refresh).toBeVisible();
    await refresh.click();
    await expect(page.getByRole("heading", { name: "Pit Wall" })).toBeVisible();
    await expect(page.getByLabel("Event", { exact: true })).toBeVisible();
    await expect(page.getByLabel("Session")).toBeVisible();
    await expect(page.getByText(/\d+ BOXES · \d+ PIT STOP/)).toBeVisible();
  });

  test("Test 9: Events and users resource pages filter real API records", async ({ page }) => {
    await signIn(page);
    for (const [path, heading] of [["/events", "Race calendar"], ["/users", "Users"]]) {
      await page.goto(path);
      await expect(page.getByRole("heading", { name: heading })).toBeVisible();
      const filter = page.getByRole("textbox", { name: "Filter records" });
      await expect(filter).toBeVisible();
      await filter.fill("__no_matching_record__");
      await expect(page.getByText("No records match this filter.")).toBeVisible();
      await page.getByRole("button", { name: "Clear filter" }).click();
      await expect(page.getByRole("textbox", { name: "Filter records" })).toHaveValue("");
    }
  });

  test("Test 10: Driver analytics applies filters and renders API result state", async ({ page }) => {
    await signIn(page);
    await page.goto("/analytics");
    await expect(page.getByRole("heading", { name: "Driver analytics" })).toBeVisible();
    await expect(page.getByText("Apply filters to load driver analytics.")).toBeVisible();
    await page.getByRole("button", { name: "Apply filters" }).click();
    await expect(page.getByRole("heading", { name: /\d+ driver records/ })).toBeVisible();
  });

  test("Test 11: DBMS workspace Overview control selects its real panel", async ({ page }) => {
    await signIn(page);
    await page.goto("/dbms");
    await expect(page.getByRole("heading", { name: "DBMS workspace" })).toBeVisible();
    await page.locator('button[data-primary="true"]').filter({ hasText: "Overview" }).click();
    await expect(page).toHaveURL(/#overview$/);
    await expect(page.getByText(/PostgreSQL|MongoDB/i).first()).toBeVisible();
  });
});
