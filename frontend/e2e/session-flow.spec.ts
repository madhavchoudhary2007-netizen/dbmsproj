import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "./mock-platform";
import { pretty } from "@/lib/api";

const sessionId = "7b481fa3-795d-4c65-95e5-a3639306f1a1";
const eventId = "82ad5b7b-1567-4be6-94c1-50a82185a544";
const driverIds = ["9651a769-7ba6-4ab1-90cd-f07685a72fb1", "4c706e53-bb24-474d-92b6-65f72a8252ea"];
const sessions = [
  { id: sessionId, event_id: eventId, event_name: "Fixture Grand Prix", session_type: "RACE", state: "SCHEDULED", scheduled_at: "2026-12-01T12:00:00Z", total_laps: 18 },
  { id: "c81b20e7-e135-40aa-b6e7-9003eb9638f2", event_id: eventId, event_name: "Fixture Grand Prix", session_type: "PRACTICE", state: "COMPLETED", scheduled_at: "2026-11-30T12:00:00Z", total_laps: 10 },
];
const drivers = driverIds.map((id, index) => ({ id, number: index + 7, full_name: `Fixture Driver ${index + 1}`, eligibility: "ACTIVE" }));
type Write = { path: string; body: unknown };

async function fixture(page: Page) {
  let state = "SCHEDULED";
  const writes: Write[] = [];
  const unexpected: string[] = [];
  const results: Record<string, unknown[]> = {
    "c81b20e7-e135-40aa-b6e7-9003eb9638f2": [{ position: 1, driver_name: "Fixture Driver 1", lap_time_ms: 90500, provisional: true }],
  };
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (request.method() === "POST") {
      const body = request.postDataJSON() as Record<string, unknown>;
      const actionPath = path === `/api/sessions/${sessionId}/action` && ["start", "pause", "resume", "finish", "reset"].includes(String(body.action));
      const simulatePath = path === `/api/sessions/${sessionId}/simulate` && ["start", "pause", "resume", "stop", "reset"].includes(String(body.action));
      const resultPath = path === `/api/sessions/${sessionId}/results`;
      if (!actionPath && !simulatePath && !resultPath) {
        unexpected.push(`POST ${path}`);
        await route.fulfill({ status: 405, json: { detail: "Unexpected session write" } });
        return;
      }
      writes.push({ path, body });
      if (actionPath) state = ({ start: "ACTIVE", pause: "PAUSED", resume: "ACTIVE", finish: "COMPLETED", reset: "SCHEDULED" } as Record<string, string>)[String(body.action)];
      if (resultPath) results[sessionId] = (body as unknown as unknown[]).map((item) => ({ ...(item as object), driver_name: "Fixture Driver 1" }));
      await route.fulfill({ status: 200, json: simulatePath ? { state: body.action === "start" ? "running" : "paused", cars: body.cars, rate_hz: body.rate_hz } : resultPath ? results[sessionId] : {} });
      return;
    }
    if (request.method() !== "GET") {
      unexpected.push(`${request.method()} ${path}`);
      await route.fulfill({ status: 405, json: { detail: "Unexpected API method" } });
      return;
    }
    const knownGet = ["/api/auth/me", "/api/sessions", "/api/events", "/api/drivers", "/api/dashboard"].includes(path) || /^\/api\/sessions\/[^/]+\/results$/.test(path);
    if (!knownGet) {
      unexpected.push(`GET ${path}`);
      await route.fulfill({ status: 405, json: { detail: "Unexpected API path" } });
      return;
    }
    const data = path === "/api/auth/me" ? { id: driverIds[0], email: "admin@apexgrid.test", full_name: "Fixture Admin", role: "ADMIN" }
      : path === "/api/sessions" ? sessions.map((row) => row.id === sessionId ? { ...row, state } : row)
      : path === "/api/events" ? [{ id: eventId, name: "Fixture Grand Prix", round_number: 4 }]
      : path === "/api/drivers" ? drivers : path === "/api/dashboard" ? { counts: { active_sessions: 0, scheduled_events: 0, open_incidents: 0, drivers: 2 }, latest_incidents: [] }
      : path.endsWith("/results") ? results[path.split("/")[3]] ?? [] : [];
    await route.fulfill({ status: 200, json: data });
  });
  return { writes, unexpected };
}

test("selected session lifecycle and simulator send exact actions", async ({ page }, testInfo) => {
  const { writes, unexpected } = await fixture(page);
  await page.goto("/sessions");
  await page.getByRole("row").filter({ hasText: "Fixture Grand Prix" }).filter({ hasText: "RACE" }).click();
  await expect(page.getByRole("group", { name: "Session lifecycle" })).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("sessions-selected.png"), fullPage: true });
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  const lifecycle = page.getByRole("group", { name: "Session lifecycle" });
  await expect(lifecycle.getByRole("button", { name: "Start", exact: true })).toBeEnabled();
  for (const name of ["Pause", "Resume", "Finish"]) await expect(lifecycle.getByRole("button", { name, exact: true })).toBeDisabled();
  await expect(page.getByRole("button", { name: "Reset", exact: true })).toBeDisabled();
  await lifecycle.getByRole("button", { name: "Start", exact: true }).click();
  await expect(lifecycle).toContainText("ACTIVE");
  await lifecycle.getByRole("button", { name: "Pause", exact: true }).click();
  await expect(lifecycle).toContainText("PAUSED");
  await expect(page.getByRole("button", { name: "Reset", exact: true })).toBeEnabled();
  await lifecycle.getByRole("button", { name: "Resume", exact: true }).click();
  await expect(lifecycle).toContainText("ACTIVE");
  const cars = page.getByRole("spinbutton", { name: "Cars" });
  const rate = page.getByRole("spinbutton", { name: "Rate Hz" });
  await expect(cars).toHaveAttribute("min", "1"); await expect(cars).toHaveAttribute("max", "2");
  await expect(rate).toHaveAttribute("min", "1");
  await cars.fill("2"); await rate.fill("17");
  await page.getByRole("button", { name: "start", exact: true }).click();
  expect(writes).toEqual([
    { path: `/api/sessions/${sessionId}/action`, body: { action: "start" } },
    { path: `/api/sessions/${sessionId}/action`, body: { action: "pause" } },
    { path: `/api/sessions/${sessionId}/action`, body: { action: "resume" } },
    { path: `/api/sessions/${sessionId}/simulate`, body: { action: "start", cars: 2, rate_hz: 17 } },
  ]);
  expect(unexpected).toEqual([]);
});

test("session dialogs support Escape, focus return and recorded fields", async ({ page }, testInfo) => {
  const { writes, unexpected } = await fixture(page);
  await page.goto("/sessions");
  const schedule = page.getByRole("button", { name: "Schedule session", exact: true });
  await schedule.click();
  let dialog = page.getByRole("dialog", { name: "Schedule session" });
  await expect(dialog).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("session-dialog.png") });
  await page.keyboard.press("Escape");
  await expect(dialog).toHaveCount(0); await expect(schedule).toBeFocused();
  expect(writes).toEqual([]);
  await schedule.click(); dialog = page.getByRole("dialog", { name: "Schedule session" });
  await expect(dialog).toBeVisible(); await page.keyboard.press("Escape");
  await page.getByRole("row").filter({ hasText: "Fixture Grand Prix" }).filter({ hasText: "RACE" }).click();
  await page.getByRole("button", { name: "Start", exact: true }).click(); await expect(page.getByRole("group", { name: "Session lifecycle" })).toContainText("ACTIVE");
  await page.getByRole("button", { name: "Record result", exact: true }).click();
  dialog = page.getByRole("dialog", { name: "Add or update session result" });
  await expect(dialog).toBeVisible();
  await expect(dialog.locator("[data-primary]")).toHaveCount(1);
  await dialog.getByLabel("driver_id").selectOption(driverIds[0]);
  await dialog.getByLabel("position").fill("2"); await dialog.getByLabel("lap_time_ms").fill("90500");
  await dialog.getByLabel("pole").selectOption("true"); await dialog.getByLabel("fastest_lap").selectOption("false");
  await dialog.getByLabel("classified").selectOption("true");
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await dialog.screenshot({ path: testInfo.outputPath("session-result-dialog.png") });
  await dialog.getByRole("button", { name: "Save record", exact: true }).click();
  await expect(page.getByRole("cell", { name: "90500" })).toBeVisible();
  await expect(page.getByRole("cell", { name: "true" }).first()).toBeVisible();
  expect(writes).toEqual([
    { path: `/api/sessions/${sessionId}/action`, body: { action: "start" } },
    {
      path: `/api/sessions/${sessionId}/results`,
      body: [{ driver_id: driverIds[0], position: "2", lap_time_ms: "90500", pole: true, fastest_lap: false, classified: true }],
    },
  ]);
  expect(unexpected).toEqual([]);
});

test("loaded session results show only returned fields and exact empty state", async ({ page }) => {
  const { writes, unexpected } = await fixture(page);
  await page.goto("/sessions");
  const rows = page.getByRole("row").filter({ hasText: "Fixture Grand Prix" });
  await rows.filter({ hasText: "RACE" }).click();
  await page.getByRole("button", { name: "Load results" }).click();
  await expect(page.getByText("No result rows are recorded for this session.")).toBeVisible();
  await rows.filter({ hasText: "PRACTICE" }).click();
  await page.getByRole("button", { name: "Load results" }).click();
  await expect(page.getByText("PROVISIONAL RESULTS")).toBeVisible();
  await expect(page.getByText(/Historical time and grid penalties are recorded but not applied/)).toBeVisible();
  const table = page.getByRole("table").filter({ has: page.getByRole("columnheader", { name: "position" }) });
  for (const field of ["position", "driver name", "lap time ms", "provisional"]) await expect(table.getByRole("columnheader", { name: field })).toBeVisible();
  await expect(table.getByRole("row")).toHaveCount(2);
  for (const value of [pretty(1), pretty("Fixture Driver 1"), pretty(90500), pretty(true)]) await expect(table.getByRole("cell", { name: value, exact: true })).toBeVisible();
  expect(writes).toEqual([]);
  expect(unexpected).toEqual([]);
});
