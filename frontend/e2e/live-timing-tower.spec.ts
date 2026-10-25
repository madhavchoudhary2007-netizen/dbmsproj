import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page, type WebSocketRoute } from "@playwright/test";

declare global { interface Window { __towerAnimations: number[] } }

const drivers = [
  { id: "d1", full_name: "Driver One", number: 1, licence_number: "L1", team_name: "Red", team_color: "#f00" },
  { id: "d2", full_name: "Driver Two", number: 2, licence_number: "L2", team_name: "Blue", team_color: "#00f" },
];
const packets = [
  { session_id: "s1", driver_id: "d1", position: 1, lap: 8, sector: 2, elapsed_ms: 64000, sector_ms: [30000, 32000, 31000], tire_compound: "SOFT", tire_age_laps: 2, tire_wear_pct: 12, pit_state: "TRACK", pit_box_number: 1, last_lap_ms: 93000 },
  { session_id: "s1", driver_id: "d2", position: 2, lap: 8, sector: 2, elapsed_ms: 65000, sector_ms: [31000, 33000, 32000], tire_compound: "MEDIUM", tire_age_laps: 4, tire_wear_pct: 24, pit_state: "TRACK", pit_box_number: 2, last_lap_ms: 97000 },
];
const laps = [
  { driver_id: "d1", lap_time_ms: 92000, sector_ms: [30000, 31000, 31000] },
  { driver_id: "d2", lap_time_ms: 95000, sector_ms: [31000, 32000, 32000] },
];
const session = { id: "s1", state: "ACTIVE", event_name: "Timing Demo", circuit_name: "Test Circuit" };
const snapshot = () => ({ session, drivers, packets });
const ok = (route: import("@playwright/test").Route, body: unknown) => route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(body) });

async function fixture(page: Page, snapshotHandler: (route: import("@playwright/test").Route) => Promise<void>) {
  const unexpected: string[] = [];
  await page.route("**/api/**", async (route) => {
    const req = route.request();
    const path = new URL(req.url()).pathname;
    if (req.method() !== "GET") { unexpected.push(`${req.method()} ${path}`); await route.fulfill({ status: 405 }); return; }
    if (path === "/api/auth/me") await ok(route, { id: 1, email: "qa@example.test", full_name: "QA", role: "ADMIN" });
    else if (path === "/api/sessions") await ok(route, [session]);
    else if (path === "/api/demo-races") await ok(route, []);
    else if (path === "/api/sessions/s1/live") await snapshotHandler(route);
    else if (path === "/api/sessions/s1/laps") await ok(route, { laps, incidents: [], pit_reservations: [] });
    else await ok(route, []);
  });
  let socket: WebSocketRoute | undefined;
  await page.routeWebSocket("**/api/ws/sessions/*", (ws) => { socket = ws; ws.onMessage(() => unexpected.push("unexpected client websocket message")); });
  await page.goto("/live");
  return { unexpected, push: (message: unknown) => socket?.send(JSON.stringify(message)), connected: () => Boolean(socket) };
}

const tower = (page: Page) => page.locator(".running-order-panel");
const rows = (page: Page) => tower(page).getByRole("row");

test("snapshot loading resolves to named timing rows with tyre, fastest lap, and sector data", async ({ page }) => {
  let release!: () => void;
  const ready = new Promise<void>((resolve) => { release = resolve; });
  const app = await fixture(page, async (route) => { await ready; await ok(route, snapshot()); });
  await expect(tower(page).getByTestId("state-loading")).toBeVisible();
  release();
  await expect(tower(page).getByText("Driver One")).toBeVisible();
  await expect(tower(page).getByText("Driver Two")).toBeVisible();
  await expect(tower(page).getByText("FL")).toBeVisible();
  await expect(tower(page).getByText("SOFT")).toBeVisible();
  if (await page.evaluate(() => window.innerWidth < 768)) {
    const firstDriver = rows(page).filter({ hasText: "Driver One" });
    await firstDriver.locator("details").locator("summary[aria-label='Timing details for Driver One']").click();
  }
  await expect(tower(page).getByText("OB", { exact: true }).filter({ visible: true })).toBeVisible();
  expect(app.unexpected).toEqual([]);
});

test("failed initial snapshot retries and then shows the exact empty state copy", async ({ page }) => {
  let calls = 0;
  let outage = true;
  const app = await fixture(page, async (route) => { calls += 1; if (outage) { await route.fulfill({ status: 503, json: { detail: "Snapshot outage" } }); } else await ok(route, { session, drivers, packets: [] }); });
  const panel = tower(page);
  await expect(panel.getByTestId("state-error")).toContainText("Snapshot outage");
  const baselineCalls = calls;
  outage = false;
  await panel.getByRole("button", { name: "Try again" }).click();
  await expect(panel.getByText("Waiting for timing and telemetry packets from this session.")).toBeVisible();
  expect(calls).toBe(baselineCalls + 1);
  expect(app.unexpected).toEqual([]);
});

test("session state outage preserves timing rows and retry recovers the snapshot", async ({ page }) => {
  let calls = 0;
  let outage = false;
  const app = await fixture(page, async (route) => { calls += 1; if (outage) { await route.fulfill({ status: 503, json: { detail: "Snapshot outage" } }); } else await ok(route, snapshot()); });
  const panel = tower(page);
  await expect(panel.getByText("Driver One")).toBeVisible();
  await expect.poll(app.connected).toBe(true);
  const baselineCalls = calls;
  outage = true;
  app.push({ type: "session.state", session_id: "s1", data: { state: "PAUSED" } });
  await expect(panel.getByTestId("state-partial")).toContainText("Snapshot outage");
  await expect(panel.getByText("Driver One")).toBeVisible();
  outage = false;
  await panel.getByRole("button", { name: "Retry snapshot" }).click();
  await expect(panel.getByTestId("state-partial")).toHaveCount(0);
  await expect(panel.getByText("Driver Two")).toBeVisible();
  expect(calls).toBe(baselineCalls + 2);
  expect(app.unexpected).toEqual([]);
});

test("driver selection supports click, Enter, and Space; mobile details preserve selection and accessibility", async ({ page }, testInfo) => {
  const app = await fixture(page, async (route) => ok(route, snapshot()));
  const panel = tower(page);
  await expect(panel.getByText("Driver One")).toBeVisible();
  const first = rows(page).filter({ hasText: "Driver One" });
  const second = rows(page).filter({ hasText: "Driver Two" });
  const driverSelect = page.getByLabel("Driver", { exact: true });
  await first.click();
  await expect(first).toHaveAttribute("aria-selected", "true");
  await expect(driverSelect).toHaveValue("d1");
  await second.focus(); await page.keyboard.press("Enter");
  await expect(second).toHaveAttribute("aria-selected", "true");
  await expect(driverSelect).toHaveValue("d2");
  await first.focus(); await page.keyboard.press("Space");
  await expect(first).toHaveAttribute("aria-selected", "true");
  await expect(driverSelect).toHaveValue("d1");
  if (await page.evaluate(() => window.innerWidth < 768)) {
    const details = first.locator("details");
    await details.locator("summary[aria-label='Timing details for Driver One']").click();
    for (const label of ["number", "licence number", "team name", "lap", "sector", "sector times ms", "last lap ms", "best lap ms", "tire age laps", "tire wear pct", "pit state", "pit box number", "interval", "S1", "S2", "S3"]) await expect(details.getByText(label, { exact: true })).toBeVisible();
    await expect(first).toHaveAttribute("aria-selected", "true");
    await expect(driverSelect).toHaveValue("d1");
  }
  expect(await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBe(0);
  expect((await new AxeBuilder({ page }).include(".running-order-panel").analyze()).violations).toHaveLength(0);
  await page.screenshot({ path: testInfo.outputPath("timing-tower.png"), fullPage: true });
  expect(app.unexpected).toEqual([]);
});

test("WebSocket reorder animates within 300ms and reduced motion disables later animations", async ({ page }) => {
  await page.addInitScript(() => {
    const animate = Element.prototype.animate;
    Object.defineProperty(window, "__towerAnimations", { value: [] });
    Element.prototype.animate = function (frames, options) {
      const result = animate.call(this, frames, options);
      if (this.closest(".running-order-panel")) window.__towerAnimations.push(Number(typeof options === "number" ? options : options?.duration ?? 0));
      return result;
    };
  });
  const app = await fixture(page, async (route) => ok(route, snapshot()));
  await expect(tower(page).getByText("Driver One")).toBeVisible();
  await expect.poll(app.connected).toBe(true);
  app.push({ type: "timing.update", session_id: "s1", data: { cars: packets.map((car) => ({ ...car, position: car.driver_id === "d1" ? 2 : 1 })) } });
  await expect(rows(page).nth(1)).toContainText("Driver Two");
  const durations = () => page.evaluate(() => window.__towerAnimations);
  await expect.poll(async () => (await durations()).length).toBeGreaterThan(0);
  expect((await durations()).every((duration) => duration <= 300)).toBe(true);
  await page.emulateMedia({ reducedMotion: "reduce" });
  const count = (await durations()).length;
  app.push({ type: "timing.update", session_id: "s1", data: { cars: packets.map((car) => ({ ...car, position: car.driver_id === "d1" ? 1 : 2 })) } });
  await expect(rows(page).nth(1)).toContainText("Driver One");
  await expect.poll(async () => (await durations()).length).toBe(count);
  expect(app.unexpected).toEqual([]);
});
