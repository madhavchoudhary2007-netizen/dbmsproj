import { expect, test } from "./mock-platform";
import type { Page, WebSocketRoute } from "@playwright/test";

const adminUser = { id: 999, email: "admin@apexgrid.test", full_name: "Admin User", role: "ADMIN" };
const LONG_NAME = "Racer".repeat(24); // 120 characters, no spaces
const LONG_ID = "ID".repeat(60); // 120 characters, no spaces

const dashboard = {
  active_sessions: 1, scheduled_events: 3, open_incidents: 2, drivers: 20,
  active_session: { name: "Grand Prix", circuit_name: "Silverstone" },
  next_event: { name: "Next GP", circuit_name: "Spa" },
};
const health = { status: "healthy", services: { postgres: "healthy", mongodb: "healthy" } };
const liveDrivers = [
  { id: "d1", full_name: "Driver One", number: 1, licence_number: "L1", team_name: "Red", team_color: "#f00" },
  { id: "d2", full_name: "Driver Two", number: 2, licence_number: "L2", team_name: "Blue", team_color: "#00f" },
];
const liveSession = { id: "s1", state: "ACTIVE", event_name: "Boundary GP", circuit_name: "Test Circuit" };
const livePackets = [
  { session_id: "s1", driver_id: "d1", position: 1, lap: 8, sector: 2, elapsed_ms: 64000, sector_ms: [30000, 32000, 31000], tire_compound: "SOFT", tire_age_laps: 2, tire_wear_pct: 12, pit_state: "TRACK", pit_box_number: 1, last_lap_ms: 93000 },
  { session_id: "s1", driver_id: "d2", position: 2, lap: 8, sector: 2, elapsed_ms: 65000, sector_ms: [31000, 33000, 32000], tire_compound: "MEDIUM", tire_age_laps: 4, tire_wear_pct: 24, pit_state: "TRACK", pit_box_number: 2, last_lap_ms: 97000 },
];
const liveSnapshot = { session: liveSession, drivers: liveDrivers, packets: livePackets };
const liveLaps = {
  laps: [
    { driver_id: "d1", lap_time_ms: 92000, sector_ms: [30000, 31000, 31000] },
    { driver_id: "d2", lap_time_ms: 95000, sector_ms: [31000, 32000, 32000] },
  ],
  incidents: [],
  pit_reservations: [],
};
const liveHandlers = {
  "/api/sessions": [liveSession],
  "/api/sessions/s1/live": liveSnapshot,
  "/api/sessions/s1/laps": liveLaps,
  "/api/dashboard": dashboard,
  "/api/health": health,
};

const boundarySession = { id: "s1", event_id: 1, session_type: "RACE", state: "SCHEDULED", scheduled_at: "2026-01-01T10:00:00Z", total_laps: 40 };
const boundaryEvents = [{ id: 1, name: "Apex GP" }];

async function mockApi(page: Page, handlers: Record<string, unknown>) {
  await page.route("**/api/**", async (route) => {
    const pathname = new URL(route.request().url()).pathname;
    if (pathname === "/api/auth/me") {
      await route.fulfill({ status: 200, json: adminUser });
      return;
    }
    const data = pathname in handlers ? handlers[pathname] : [];
    if (Array.isArray(data)) {
      const params = new URL(route.request().url()).searchParams;
      const offset = Number(params.get("offset") ?? 0);
      const limit = Number(params.get("limit") ?? data.length);
      await route.fulfill({ status: 200, json: data.slice(offset, offset + limit) });
      return;
    }
    await route.fulfill({ status: 200, json: data });
  });
}

async function expectNoHorizontalOverflow(page: Page, label: string) {
  const extent = await page.evaluate(() => ({
    scroll: document.documentElement.scrollWidth,
    client: document.documentElement.clientWidth,
  }));
  expect(extent.scroll, label).toBeLessThanOrEqual(extent.client + 1);
}

async function setVisibility(page: Page, value: "hidden" | "visible") {
  await page.evaluate((next) => {
    Object.defineProperty(document, "visibilityState", { configurable: true, value: next });
    document.dispatchEvent(new Event("visibilitychange"));
  }, value);
}

const streamStatus = (page: Page) => page.locator(".running-order-panel .live-badge");

test("E-2 Lens 5 10,000 championships render one bounded page without horizontal overflow", async ({ page }) => {
  const rows = Array.from({ length: 10_000 }, (_, i) => ({ id: i + 1, name: `Series ${i + 1}`, season: 2000 + (i % 40) }));
  await mockApi(page, { "/api/championships": rows });

  await page.goto("/championships", { waitUntil: "domcontentloaded" });
  const region = page.getByTestId("state-populated").getByRole("region", { name: "Championships", exact: true });
  await expect(region).toBeVisible();
  await expect(region.locator("tbody tr")).toHaveCount(50);
  await expect(page.locator(".record-count")).toHaveText("10000 RECORDS");
  await expect(page.locator(".dbms-pagination")).toContainText("Page 1 of 200");
  await expectNoHorizontalOverflow(page, "10,000-row championships collection");
});

test("E-2 Lens 5 zero championships render the empty state and a zero record count", async ({ page }) => {
  await mockApi(page, { "/api/championships": [] });

  await page.goto("/championships", { waitUntil: "domcontentloaded" });
  await expect(page.getByTestId("state-empty")).toContainText("No records returned by the API.");
  await expect(page.getByTestId("state-populated")).toHaveCount(0);
  await expect(page.locator(".record-count")).toHaveText("0 RECORDS");
  await expectNoHorizontalOverflow(page, "zero-row championships collection");
});

test("E-2 Lens 5 120-character unbroken driver name and licence stay readable inside the drivers table", async ({ page }) => {
  await mockApi(page, {
    "/api/drivers": [{ id: "d1", user_id: 1, full_name: LONG_NAME, number: 7, licence_number: LONG_ID, eligibility: "ACTIVE", team_name: "Red Team" }],
  });

  await page.goto("/drivers", { waitUntil: "domcontentloaded" });
  const region = page.getByTestId("state-populated").getByRole("region", { name: "Drivers", exact: true });
  await expect(region.locator("tbody tr")).toHaveCount(1);
  await expect(region.getByRole("cell", { name: LONG_NAME, exact: true })).toBeVisible();
  await expect(region.getByRole("cell", { name: LONG_ID, exact: true })).toBeVisible();
  await expectNoHorizontalOverflow(page, "drivers table with 120-character strings");
});

test("E-2 Lens 5 120-character unbroken case identifiers and driver names stay inside the steward case card", async ({ page }) => {
  await mockApi(page, {
    "/api/incidents": [{ id: LONG_ID, driver_id: "d1", session_id: "s1", lap: 3, state: "OPEN", description: "Contact at turn three", reported_at: "2026-01-01T10:00:00Z" }],
    "/api/drivers": [{ id: "d1", full_name: LONG_NAME, number: 7, eligibility: "ACTIVE" }],
    "/api/sessions": [{ id: "s1", session_type: "RACE", state: "ACTIVE", event_id: 1 }],
  });

  await page.goto("/stewards", { waitUntil: "domcontentloaded" });
  const cases = page.getByTestId("state-populated").getByRole("table", { name: "Incident case files", exact: true });
  await expect(cases.getByRole("row")).toHaveCount(1);
  await expect(cases.getByRole("cell", { name: `CASE #${LONG_ID}`, exact: true })).toBeVisible();
  await expect(cases.getByText(LONG_NAME, { exact: true })).toBeVisible();
  await expectNoHorizontalOverflow(page, "steward case card with 120-character strings");
});

test("E-2 Lens 5 server-closed session WebSocket reports reconnecting, reopens, and connected frames update timing", async ({ page }) => {
  await mockApi(page, liveHandlers);
  const sockets: WebSocketRoute[] = [];
  await page.routeWebSocket("**/api/ws/sessions/*", (socket) => { sockets.push(socket); });

  await page.goto("/live", { waitUntil: "domcontentloaded" });
  await expect(streamStatus(page)).toContainText("Connected · live stream");
  await expect.poll(() => sockets.length).toBe(1);

  sockets[0].close({ code: 1011, reason: "Server restart" });
  await expect(streamStatus(page)).toContainText(/reconnecting/i);
  await expect.poll(() => sockets.length).toBe(2);
  await expect(streamStatus(page)).toContainText("Connected · live stream");

  sockets[1].send(JSON.stringify({
    type: "telemetry.sample",
    session_id: "s1",
    data: { ...livePackets[0], lap: 4242 },
  }));
  const row = page.locator(".running-order-panel").getByRole("row").filter({ hasText: "Driver One" });
  await expect(row).toContainText("4242");
  await expect(streamStatus(page)).toContainText("Connected · live stream");
});

test("E-2 Lens 5 hidden race-control feed with a 5-minute clock jump makes one catch-up request on return", async ({ page }) => {
  await page.clock.install();
  await mockApi(page, { "/api/dashboard": dashboard, "/api/health": health });
  let dashboardCalls = 0;
  await page.route("**/api/dashboard", async (route) => {
    dashboardCalls += 1;
    await route.fulfill({ status: 200, json: dashboard });
  });

  await page.goto("/dashboard", { waitUntil: "domcontentloaded" });
  const feed = page.locator("[data-feed-state='populated']");
  await expect(feed).toBeVisible();
  const loadedCalls = dashboardCalls;

  await setVisibility(page, "hidden");
  await page.clock.runFor(5 * 60_000);
  expect(dashboardCalls).toBe(loadedCalls);

  await setVisibility(page, "visible");
  await expect.poll(() => dashboardCalls).toBe(loadedCalls + 1);
  await expect(feed).toBeVisible();
  await expect(page.locator("[data-feed-state='loading']")).toHaveCount(0);
  expect(dashboardCalls).toBe(loadedCalls + 1);
});

test("E-2 Lens 5 large lap and time jump packet renders finite live timing values", async ({ page }) => {
  await mockApi(page, liveHandlers);
  const sockets: WebSocketRoute[] = [];
  await page.routeWebSocket("**/api/ws/sessions/*", (socket) => { sockets.push(socket); });

  await page.goto("/live", { waitUntil: "domcontentloaded" });
  await expect(streamStatus(page)).toContainText("Connected · live stream");
  await expect.poll(() => sockets.length).toBe(1);

  sockets[0].send(JSON.stringify({
    type: "telemetry.sample",
    session_id: "s1",
    data: {
      session_id: "s1", driver_id: "d2", position: 2, lap: 9999, sector: 1,
      elapsed_ms: 7200000, sector_ms: [2400000, 2400000, 2400000], last_lap_ms: 7200000,
      tire_compound: "MEDIUM", tire_age_laps: 4, tire_wear_pct: 24, pit_state: "TRACK", pit_box_number: 2,
    },
  }));
  const jumpRow = page.locator(".running-order-panel").getByRole("row").filter({ hasText: "Driver Two" });
  await expect(jumpRow).toContainText("9999");
  await expect(jumpRow).toContainText("7200000");
  const mainText = await page.locator("main").innerText();
  expect(mainText).not.toMatch(/NaN|Infinity|undefined/);
});

test("E-2 Lens 5 a 409 illegal transition shows an error and keeps the displayed session state", async ({ page }) => {
  await mockApi(page, { "/api/sessions": [boundarySession], "/api/events": boundaryEvents, "/api/drivers": [] });
  const postedActions: string[] = [];
  await page.route("**/api/sessions/s1/action", async (route) => {
    const body = JSON.parse(route.request().postData() ?? "{}") as { action?: string };
    postedActions.push(String(body.action));
    await route.fulfill({ status: 409, json: { detail: "Illegal transition from SCHEDULED for action start" } });
  });

  await page.goto("/sessions", { waitUntil: "domcontentloaded" });
  const sessions = page.getByRole("region", { name: "Sessions", exact: true });
  const sessionRow = sessions.getByRole("row", { name: /Apex GP/ });
  await expect(sessionRow).toBeVisible();
  await sessionRow.click();

  const lifecycle = page.getByRole("group", { name: "Session lifecycle" });
  await expect(lifecycle).toContainText("SCHEDULED");
  await lifecycle.getByRole("button", { name: "Start", exact: true }).click();

  await expect(page.locator(".session-control .notice")).toContainText("Illegal transition from SCHEDULED for action start");
  await expect(lifecycle).toContainText("SCHEDULED");
  await expect(lifecycle).not.toContainText("ACTIVE");
  await expect(sessionRow).toContainText("SCHEDULED");
  expect(postedActions).toEqual(["start"]);
});

test("E-2 Lens 5 a completed session has no enabled illegal lifecycle transitions", async ({ page }) => {
  await mockApi(page, {
    "/api/sessions": [{ ...boundarySession, state: "COMPLETED" }],
    "/api/events": boundaryEvents,
    "/api/drivers": [],
  });

  await page.goto("/sessions", { waitUntil: "domcontentloaded" });
  const sessions = page.getByRole("region", { name: "Sessions", exact: true });
  await sessions.getByRole("row", { name: /Apex GP/ }).click();

  const lifecycle = page.getByRole("group", { name: "Session lifecycle" });
  await expect(lifecycle).toContainText("COMPLETED");
  for (const name of ["Start", "Pause", "Resume", "Finish"]) {
    const control = lifecycle.getByRole("button", { name, exact: true });
    const count = await control.count();
    expect(count, `${name} control count`).toBeLessThanOrEqual(1);
    if (count === 1) await expect(control, `${name} control`).toBeDisabled();
  }
});
