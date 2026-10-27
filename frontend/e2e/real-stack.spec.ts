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

type TimingUpdate = {
  type?: string;
  session_id?: string;
  data?: { cars?: Array<Record<string, unknown>> };
};

function watchTimingUpdates(page: Page): TimingUpdate[] {
  const updates: TimingUpdate[] = [];
  page.on("websocket", (socket) => {
    if (!new URL(socket.url()).pathname.includes("/api/ws/sessions/")) return;
    socket.on("framereceived", ({ payload }) => {
      try {
        const message = JSON.parse(String(payload)) as TimingUpdate;
        if (message.type === "timing.update") updates.push(message);
      } catch {
        // Ignore non-JSON WebSocket frames.
      }
    });
  });
  return updates;
}

async function waitForTimingUpdate(
  updates: TimingUpdate[],
  sessionId: string,
): Promise<TimingUpdate> {
  await expect.poll(() => updates.some(
    (update) => update.session_id === sessionId && Boolean(update.data?.cars?.length),
  )).toBe(true);
  const update = updates.find(
    (message) => message.session_id === sessionId && Boolean(message.data?.cars?.length),
  );
  if (!update) throw new Error(`No timing update received for generated session ${sessionId}`);
  return update;
}

async function createGeneratedRace(page: Page): Promise<string> {
  const responsePromise = page.waitForResponse((response) =>
    response.request().method() === "POST" &&
    new URL(response.url()).pathname.endsWith("/api/demo-races"),
  );
  await page.getByRole("button", { name: "Create live race" }).click();
  const response = await responsePromise;
  expect(response.status()).toBe(201);
  const created = await response.json() as { session_id?: unknown };
  expect(typeof created.session_id).toBe("string");
  const sessionId = created.session_id as string;
  await expect(page.getByRole("combobox", { name: "Session" })).toHaveValue(sessionId);
  return sessionId;
}

test.describe("Real-stack Journey Tests (Unmocked)", () => {
  test.beforeEach(async ({ page }) => {
    expect(process.env.APEXGRID_E2E_OWNED_DISPOSABLE).toBe("1");
    await page.goto("/");
    expect(["localhost", "127.0.0.1"]).toContain(new URL(page.url()).hostname);
  });

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
    const timingUpdates = watchTimingUpdates(page);
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

    const sessionId = await createGeneratedRace(page);
    const update = await waitForTimingUpdate(timingUpdates, sessionId);
    const carCount = update.data?.cars?.length ?? 0;
    expect(carCount).toBeGreaterThan(0);
    await expect(page.getByText("Connected · live stream", { exact: true }).first()).toBeVisible();
    await expect(page.getByRole("heading", { name: `${carCount} cars on timing` })).toBeVisible();
    await expect(
      page.getByRole("table", { name: "LIVE TIMING / RUNNING ORDER" }).getByRole("row"),
    ).toHaveCount(carCount + 1);

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

  test("Test 7: Steward approval is followed by standings recalculation", async ({ page }) => {
    await signIn(page);
    const timingUpdates = watchTimingUpdates(page);
    await page.goto("/live");
    const sessionId = await createGeneratedRace(page);
    const update = await waitForTimingUpdate(timingUpdates, sessionId);
    const firstCar = update.data?.cars?.[0];
    expect(firstCar?.driver_id).toBeTruthy();
    const driverId = String(firstCar?.driver_id);

    await page.goto("/stewards");
    await expect(page.getByRole("heading", { name: "Steward desk" })).toBeVisible();
    await expect(page.getByRole("table", { name: "Incident case files" })).toBeVisible();
    const report = page.getByRole("button", { name: "Report incident" });
    await expect(report).toBeVisible();
    await report.click();
    await expect(page.getByRole("heading", { name: "Report incident" })).toBeVisible();

    const sessionField = page.getByLabel("session id", { exact: true });
    const driverField = page.getByLabel("driver id", { exact: true });
    await expect.poll(() => sessionField.locator(`option[value="${sessionId}"]`).count()).toBe(1);
    await expect.poll(() => driverField.locator(`option[value="${driverId}"]`).count()).toBe(1);
    await sessionField.selectOption(sessionId);
    await driverField.selectOption(driverId);
    await page.getByLabel("lap", { exact: true }).fill("1");
    const description = `Owned disposable steward case ${Date.now()}`;
    await page.getByLabel("description", { exact: true }).fill(description);
    await page.getByRole("button", { name: "Save record" }).click();

    const incident = page.getByRole("row", { name: new RegExp(description) });
    await expect(incident).toBeVisible();
    await incident.click();
    await expect(page.getByRole("heading", { name: "Incident review" })).toBeVisible();
    await page.getByLabel("Decision notes").fill("Approved in disposable E2E fixture");
    await page.getByLabel("Penalty points").fill("1");
    await page.getByRole("button", { name: "Approve penalty" }).click();
    await expect(page.getByRole("status").filter({ hasText: "Decision recorded." })).toBeVisible();

    await page.goto("/standings");
    await expect(page.getByRole("heading", { name: "Standings" })).toBeVisible();
    const championship = page.getByLabel("Championship");
    const demoChampionship = championship.locator("option").filter({ hasText: "ApexGrid Live Demo" }).first();
    await expect(demoChampionship).toBeAttached();
    const championshipId = await demoChampionship.getAttribute("value");
    if (!championshipId) throw new Error("Generated demo championship is unavailable");
    await championship.selectOption(championshipId);
    await page.getByRole("button", { name: "Recalculate standings" }).click();
    await expect(page.getByText(/^Standings recalculated\..*"recalculated":true/)).toBeVisible();
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
