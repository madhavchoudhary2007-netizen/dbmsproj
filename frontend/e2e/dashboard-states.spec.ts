import { expect, test } from "@playwright/test";

const admin = { id: 999, email: "qa@example.test", full_name: "QA", role: "ADMIN" };
const metrics = { active_sessions: 0, scheduled_events: 0, open_incidents: 0, drivers: 0 };
const healthy = { status: "ok", services: { postgres: "up", mongodb: "up" } };
const event = {
  id: "event-7", name: "Night Grand Prix", session_id: "session-7",
  scheduled_at: "2026-11-07T18:00:00Z", circuit_name: "Marina Bay",
};

type Reply = { status?: number; json: unknown };
type Overrides = {
  dashboard?: (count: number) => Promise<Reply>;
  health?: (count: number) => Promise<Reply>;
};

async function mockApi(page: import("@playwright/test").Page, overrides: Overrides = {}) {
  const calls: Record<string, number> = {};
  const writes: string[] = [];
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (request.method() !== "GET") {
      writes.push(`${request.method()} ${path}`);
      await route.fulfill({ status: 405, json: { detail: "Unexpected write" } });
      return;
    }
    calls[path] = (calls[path] || 0) + 1;
    let reply: Reply;
    if (path === "/api/auth/me") reply = { json: admin };
    else if (path === "/api/dashboard") reply = await (overrides.dashboard?.(calls[path]) ?? Promise.resolve({ json: metrics }));
    else if (path === "/api/health") reply = await (overrides.health?.(calls[path]) ?? Promise.resolve({ json: healthy }));
    else reply = { json: [] };
    await route.fulfill({ status: reply.status ?? 200, json: reply.json });
  });
  return { calls, writes };
}

function gate() {
  let release!: (reply: Reply) => void;
  const promise = new Promise<Reply>((resolve) => { release = resolve; });
  return { promise, release };
}

test("shows controlled loading, then empty state and reload action", async ({ page }) => {
  const pending = gate();
  const api = await mockApi(page, { dashboard: (n) => n === 1 ? pending.promise : Promise.resolve({ json: {} }) });
  await page.goto("/dashboard");
  await expect(page.locator('.dashboard-summary[data-testid="state-loading"]')).toBeVisible();
  pending.release({ json: {} });
  await expect(page.locator('.dashboard-summary[data-testid="state-empty"]')).toBeVisible();
  await page.getByRole("button", { name: "Reload dashboard data" }).click();
  await expect.poll(() => api.calls["/api/dashboard"]).toBe(2);
  await expect(page.locator('.dashboard-summary[data-testid="state-empty"]')).toBeVisible();
  expect(api.writes).toEqual([]);
});

test("renders zero metrics and the actual next event with its sessions link", async ({ page }) => {
  const api = await mockApi(page, { dashboard: async () => ({ json: { ...metrics, next_event: event } }) });
  await page.goto("/dashboard");
  await expect(page.locator('.dashboard-summary[data-testid="state-populated"]')).toBeVisible();
  await expect(page.locator('.dashboard-summary[data-testid="state-populated"] .stat-card')).toHaveCount(4);
  for (const value of ["Night Grand Prix", "Marina Bay"]) {
    await expect(page.locator(".dashboard-summary").getByText(value)).toBeVisible();
  }
  await expect(page.getByRole("link", { name: "View sessions" })).toHaveAttribute("href", "/sessions");
  expect(api.writes).toEqual([]);
});

test("keeps healthy status labels readable and the sessions link visible", async ({ page }) => {
  const api = await mockApi(page);
  await page.goto("/dashboard");
  await expect(page.locator('.dashboard-summary[data-testid="state-populated"]')).toBeVisible();
  const healthLabels = page.locator(".dashboard-health-card .green");
  await expect(healthLabels).toHaveCount(3);
  expect(await healthLabels.evaluateAll((labels) => labels.map((label) => getComputedStyle(label).color))).toEqual(["rgb(0, 0, 0)", "rgb(0, 0, 0)", "rgb(0, 0, 0)"]);
  expect(await healthLabels.evaluateAll((labels) => labels.map((label) => getComputedStyle(label).backgroundColor))).toEqual(["rgb(124, 245, 176)", "rgb(124, 245, 176)", "rgb(124, 245, 176)"]);

  const sessionsLink = page.getByRole("link", { name: "View sessions" });
  const face = sessionsLink.locator(".nb-face");
  await expect(face).toBeVisible();
  expect(await face.evaluate((element) => getComputedStyle(element).backgroundColor)).toBe("rgb(255, 255, 255)");
  expect(await face.evaluate((element) => getComputedStyle(element).color)).toBe("rgb(0, 0, 0)");
  const box = await sessionsLink.boundingBox();
  expect(box?.width).toBeGreaterThanOrEqual(44);
  expect(box?.height).toBeGreaterThanOrEqual(44);
  await expect(sessionsLink).not.toHaveAttribute("data-primary");
  expect(api.writes).toEqual([]);
});

test("shows dashboard failure cause and recovers on retry", async ({ page }) => {
  const api = await mockApi(page, { dashboard: async (n) => n === 1
    ? { status: 503, json: { detail: "Dashboard source unavailable" } }
    : { json: metrics } });
  await page.goto("/dashboard");
  const error = page.locator('.dashboard-summary[data-testid="state-error"]');
  await expect(error).toContainText("Dashboard source unavailable");
  await error.getByRole("button", { name: "Try again" }).click();
  await expect(page.locator('.dashboard-summary[data-testid="state-populated"]')).toBeVisible();
  expect(api.writes).toEqual([]);
});

test("retains four metrics in partial health state and recovers", async ({ page }) => {
  let sourceOffline = true;
  const api = await mockApi(page, { health: async () => sourceOffline
    ? { status: 503, json: { detail: "Health source unavailable" } }
    : { json: healthy } });
  await page.goto("/dashboard");
  const partial = page.locator('.dashboard-summary[data-testid="state-partial"]');
  await expect(partial).toContainText("Health source unavailable");
  await expect(page.locator('.dashboard-summary[data-testid="state-partial"] .stat-card')).toHaveCount(4);
  sourceOffline = false;
  await partial.getByRole("button", { name: "Try again" }).click();
  await expect(page.locator('.dashboard-summary[data-testid="state-populated"]')).toBeVisible();
  expect(api.writes).toEqual([]);
});

test("coalesces same-frame reload spam while health is pending", async ({ page }) => {
  const pendingHealth = gate();
  let deferHealth = false;
  const api = await mockApi(page, { health: () => deferHealth ? pendingHealth.promise : Promise.resolve({ json: healthy }) });
  await page.goto("/dashboard");
  await expect(page.locator('.dashboard-summary[data-testid="state-populated"]')).toBeVisible();
  const baselineHealthCalls = api.calls["/api/health"];
  deferHealth = true;
  await page.getByRole("button", { name: "Refresh", exact: true }).click();
  await expect.poll(() => api.calls["/api/health"]).toBe(baselineHealthCalls + 1);
  await page.getByRole("button", { name: "Refresh", exact: true }).evaluate((button) => {
    for (let i = 0; i < 20; i++) button.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  });
  await expect.poll(() => api.calls["/api/health"]).toBe(baselineHealthCalls + 1);
  pendingHealth.release({ json: healthy });
  await expect(page.locator('.dashboard-summary[data-testid="state-populated"]')).toBeVisible();
  expect(api.calls["/api/health"]).toBe(baselineHealthCalls + 1);
  expect(api.writes).toEqual([]);
});

test("navigation away while requests are pending produces no page errors", async ({ page }) => {
  const pending = gate();
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  const api = await mockApi(page, { health: () => pending.promise });
  await page.goto("/dashboard");
  await expect(page.getByRole("heading", { name: "Race operations" })).toBeVisible();
  await page.getByRole("link", { name: "Open live timing" }).click();
  await expect(page).toHaveURL(/\/live$/);
  pending.release({ json: healthy });
  await expect.poll(() => errors.length).toBe(0);
  expect(api.writes).toEqual([]);
});
