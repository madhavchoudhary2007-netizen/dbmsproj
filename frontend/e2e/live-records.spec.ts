import { expect, test, type Page } from "./mock-platform";
import type { Route } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const drivers = [
  { id: "a", full_name: "Driver A", number: 1, licence_number: "A1", team_name: "Red", team_color: "#f00" },
  { id: "b", full_name: "Driver B", number: 2, licence_number: "B2", team_name: "Blue", team_color: "#00f" },
];
const packets = drivers.map((driver, index) => ({ session_id: "s1", driver_id: driver.id, position: index + 1, lap: 60, sector: 3, elapsed_ms: 5_400_000 + index, sector_ms: [30_000, 31_000, 32_000], tire_compound: "SOFT", tire_age_laps: 4, tire_wear_pct: 12, tire_temp_c: [90, 91, 92, 93], pit_state: "TRACK", pit_box_number: index + 1, last_lap_ms: 93_000, speed_kph: 310, throttle_pct: 98, brake_pct: 0 }));
const session = { id: "s1", state: "ACTIVE", event_name: "Records Demo", circuit_name: "Test Circuit" };
const laps = drivers.flatMap((driver, index) => Array.from({ length: 60 }, (_, lap) => ({ driver_id: driver.id, lap: lap + 1, position: index + 1, sector_ms: [30_000 + lap, 31_000 + lap, 32_000 + lap], lap_time_ms: 93_000 + lap + index })));
const incidents = [{ id: "incident-a", driver_id: "a", driver_name: "Driver A", lap: 42, description: "Track limit warning", state: "CONFIRMED" }];
const pitStops = [{ id: "pit-a", driver_id: "a", driver_name: "Driver A", team_name: "Red", box_number: 1, starts_at: "2026-10-25T10:00:00Z", ends_at: "2026-10-25T10:00:24Z", status: "COMPLETED" }];
const json = (route: Route, body: unknown) => route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(body) });
const card = (page: Page, title: string) => page.locator(".nb-face").filter({ has: page.getByRole("heading", { name: title, exact: true }) }).first();
const lapCard = (page: Page) => card(page, "Driver lap and sector history");
const recordsCard = (page: Page) => card(page, "Incidents and pit stops");

async function mount(page: Page, getLaps: (route: Route) => Promise<void>) {
  const unexpected: string[] = [];
  let lapGets = 0;
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (request.method() !== "GET") { unexpected.push(`${request.method()} ${path}`); await route.fulfill({ status: 405 }); return; }
    if (path === "/api/auth/me") await json(route, { id: 1, email: "qa@example.test", full_name: "QA", role: "ADMIN" });
    else if (path === "/api/sessions") await json(route, [session]);
    else if (path === "/api/demo-races") await json(route, []);
    else if (path === "/api/dashboard") await json(route, { counts: { active_sessions: 1, scheduled_events: 0, open_incidents: 1, drivers: 2 }, latest_incidents: [] });
    else if (path === "/api/sessions/s1/live") await json(route, { session, drivers, packets });
    else if (path === "/api/sessions/s1/laps") { lapGets += 1; await getLaps(route); }
    else await json(route, []);
  });
  await page.routeWebSocket("**/api/ws/sessions/*", (socket) => socket.onMessage(() => { unexpected.push("unexpected client websocket message"); }));
  await page.goto("/live");
  return { unexpected, lapGets: () => lapGets };
}

test("shows actual laps, filtered history, all telemetry, and responsive tables", async ({ page }, testInfo) => {
  const app = await mount(page, (route) => json(route, { laps, incidents, pit_reservations: pitStops }));
  const lapHistory = lapCard(page);
  await expect(lapHistory.getByText("120 completed driver laps")).toBeVisible();
  await expect(lapHistory.getByText("Showing 100 of 120 completed driver laps")).toBeVisible();
  await lapHistory.getByRole("button", { name: "Show all laps", exact: true }).click();
  await expect(lapHistory.getByRole("button", { name: "Show latest 100", exact: true })).toBeVisible();
  await page.locator(".running-order-panel").getByText("Driver A", { exact: true }).click();
  await expect(lapHistory.getByText("60 completed driver laps")).toBeVisible();
  await page.locator(".running-order-panel").screenshot({ path: testInfo.outputPath("tower.png") });
  await page.locator(".telemetry-charts").screenshot({ path: testInfo.outputPath("telemetry-charts.png") });
  const rows = lapHistory.getByRole("row");
  await expect(rows.filter({ hasText: "Driver A" }).first()).toBeVisible();
  await expect(rows.filter({ hasText: "Driver B" })).toHaveCount(0);
  for (const title of ["Speed · km/h", "Throttle · %", "Brake · %", "Lap time · ms", "Tire wear · %", "Tire temperatures · °C"]) await expect(card(page, title).getByRole("heading", { name: title, exact: true })).toBeVisible();
  const temps = card(page, "Tire temperatures · °C");
  for (const [label, value] of [["Front left", "90"], ["Front right", "91"], ["Rear left", "92"], ["Rear right", "93"]]) await expect(temps.getByText(label, { exact: true }).locator("..")).toContainText(value);
  const accessibility = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
  expect(accessibility.violations).toEqual([]);
  for (const width of [320, 375, 768, 1440, 2560]) { await page.setViewportSize({ width, height: 900 }); expect(await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBe(0); }
  expect(app.unexpected).toEqual([]);
});

test("shows actual loading and error states, then retries laps and timelines", async ({ page }) => {
  let release!: () => void;
  const gated = new Promise<void>((resolve) => { release = resolve; });
  let fail = true;
  const app = await mount(page, async (route) => { await gated; if (fail) await route.fulfill({ status: 503, json: { detail: "Records offline" } }); else await json(route, { laps, incidents, pit_reservations: pitStops }); });
  const card = lapCard(page);
  await expect(card.getByTestId("state-loading")).toBeVisible();
  await expect.poll(app.lapGets).toBe(1);
  release();
  await expect(card.getByTestId("state-error")).toContainText("Records offline");
  fail = false;
  await card.getByRole("button", { name: "Try again", exact: true }).click();
  await expect(card.getByText("120 completed driver laps")).toBeVisible();
  const controls = recordsCard(page);
  await expect(controls.getByText("Track limit warning")).toBeVisible();
  await expect(controls.getByText("COMPLETED", { exact: true })).toBeVisible();
  expect(app.lapGets()).toBe(2);
  expect(app.unexpected).toEqual([]);
});

test("retains records during a timed outage and recovers from the lap card", async ({ page }) => {
  await page.clock.install();
  let fail = false;
  const app = await mount(page, async (route) => { if (fail) await route.fulfill({ status: 503, json: { detail: "Records refresh failed" } }); else await json(route, { laps, incidents, pit_reservations: pitStops }); });
  const card = lapCard(page);
  const controls = recordsCard(page);
  await expect(card.getByText("120 completed driver laps")).toBeVisible();
  await expect(controls.getByText("Track limit warning")).toBeVisible();
  await expect(controls.getByText("COMPLETED", { exact: true })).toBeVisible();
  const baseline = app.lapGets();
  fail = true;
  await page.clock.fastForward(5_000);
  await expect(card.getByText("Records refresh failed").first()).toBeVisible();
  await expect(card.getByText("120 completed driver laps")).toBeVisible();
  await expect(controls.getByText("Track limit warning")).toBeVisible();
  await expect(controls.getByText("COMPLETED", { exact: true })).toBeVisible();
  fail = false;
  await card.getByRole("button", { name: "Retry records", exact: true }).click();
  await expect(card.getByText("120 completed driver laps")).toBeVisible();
  await expect(card.getByText("Records refresh failed")).toHaveCount(0);
  expect(app.lapGets()).toBe(baseline + 2);
  expect(app.unexpected).toEqual([]);
});

test("renders empty lap and race-control records from an empty API response", async ({ page }) => {
  await mount(page, (route) => json(route, { laps: [], incidents: [], pit_reservations: [] }));
  await expect(lapCard(page).getByText("No records returned by the API.")).toBeVisible();
  await expect(recordsCard(page).getByText("No records returned by the API.")).toHaveCount(2);
});
