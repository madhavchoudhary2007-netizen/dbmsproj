import { expect, test } from "./mock-platform";

const admin = { id: 999, email: "qa@example.test", full_name: "QA", role: "ADMIN" };
const sessionId = "123e4567-e89b-42d3-a456-426614174000";
const metrics = { active_sessions: 0, scheduled_events: 0, open_incidents: 0, drivers: 0 };
type Reply = { status?: number; json: unknown };

async function mockApi(page: import("@playwright/test").Page, session = false) {
  const writes: string[] = [];
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (request.method() !== "GET") {
      writes.push(`${request.method()} ${path}`);
      await route.fulfill({ status: 405, json: { detail: "Unexpected write" } });
    } else {
      const json = path === "/api/auth/me" ? admin
        : path === "/api/dashboard" ? { ...metrics, ...(session ? { active_sessions: 1, active_session: { id: sessionId, state: "RUNNING" } } : {}) }
        : path === "/api/health" ? { status: "ok", services: { postgres: "up", mongodb: "up" } } : [];
      await route.fulfill({ json });
    }
  });
  return writes;
}

function card(page: import("@playwright/test").Page) { return page.locator(".dashboard-health-card"); }
function readiness(page: import("@playwright/test").Page, reply: () => Reply | Promise<Reply>) { return page.route("**/health/ready", async (route) => { const response = await reply(); await route.fulfill({ status: response.status ?? 200, json: response.json }); }); }
function value(page: import("@playwright/test").Page, label: string) { return card(page).locator(".detail-row").filter({ has: page.getByText(label, { exact: true }) }).locator("b"); }

test("shows idle WebSocket and an up runtime lease without an active session", async ({ page }) => {
  const writes = await mockApi(page);
  await page.goto("/dashboard");
  await expect(card(page).getByText("No active session")).toBeVisible();
  await expect(value(page, "Runtime lease")).toHaveText("up");
  expect(writes).toEqual([]);
});
test("reports the actual session WebSocket URL and open state without sending frames", async ({ page }) => {
  const writes = await mockApi(page, true);
  const sockets: string[] = [];
  let frames = 0;
  page.on("websocket", (socket) => { sockets.push(socket.url()); socket.on("framesent", () => frames++); });
  let opened = false;
  await page.routeWebSocket(`**/api/ws/sessions/${sessionId}`, (socket) => { opened = true; socket.onMessage(() => { frames++; }); });
  await page.goto("/dashboard");
  await expect(value(page, "WebSocket")).toHaveText("up");
  await expect.poll(() => opened).toBe(true);
  const apiBase = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");
  expect(sockets).toContain(`${apiBase.replace(/^http/, "ws")}/api/ws/sessions/${sessionId}`);
  expect(frames).toBe(0);
  expect(writes).toEqual([]);
});
test("uses a valid not-ready response to report the runtime lease down", async ({ page }) => {
  const writes = await mockApi(page);
  await readiness(page, () => ({ status: 503, json: { status: "not_ready", services: { runtime_lease: "down" } } }));
  await page.goto("/dashboard");
  await expect(value(page, "Runtime lease")).toHaveText("down");
  expect(writes).toEqual([]);
});
test("shows malformed readiness cause and recovers on recheck", async ({ page }) => {
  const writes = await mockApi(page);
  let malformed = true;
  await readiness(page, () => malformed ? { json: { status: "ready", services: {} } } : { json: { status: "ready", services: { runtime_lease: "up" } } });
  await page.goto("/dashboard");
  await expect(value(page, "Runtime lease")).toHaveText("Unknown");
  await expect(card(page).getByRole("alert")).toContainText("runtime lease status is missing");
  malformed = false;
  await card(page).getByRole("button", { name: "Recheck runtime lease" }).click();
  await expect(value(page, "Runtime lease")).toHaveText("up");
  await expect(card(page).getByRole("alert")).toHaveCount(0);
  expect(writes).toEqual([]);
});
test("keeps the last lease visible after a reload failure and recovers", async ({ page }) => {
  const writes = await mockApi(page);
  let fail = false;
  await readiness(page, () => fail ? { status: 503, json: { detail: "Readiness source unavailable" } } : { json: { status: "ready", services: { runtime_lease: "up" } } });
  await page.goto("/dashboard");
  await expect(value(page, "Runtime lease")).toHaveText("up");
  fail = true;
  await card(page).getByRole("button", { name: "Recheck runtime lease" }).click();
  await expect(value(page, "Runtime lease")).toHaveText("up · Last observed");
  await expect(card(page).getByRole("alert")).toContainText("Readiness request failed (503)");
  fail = false;
  await card(page).getByRole("button", { name: "Recheck runtime lease" }).click();
  await expect(value(page, "Runtime lease")).toHaveText("up");
  expect(writes).toEqual([]);
});
test("reports a mocked socket close as down", async ({ page }) => {
  const writes = await mockApi(page, true);
  let socket!: import("@playwright/test").WebSocketRoute;
  await page.routeWebSocket(`**/api/ws/sessions/${sessionId}`, (route) => { socket = route; });
  await page.goto("/dashboard");
  await expect(value(page, "WebSocket")).toHaveText("up");
  await expect.poll(() => Boolean(socket)).toBe(true);
  await socket.close({ code: 1001, reason: "test close" });
  await expect(value(page, "WebSocket")).toHaveText("down");
  expect(writes).toEqual([]);
});
test("closes the active socket on navigation without page errors", async ({ page }) => {
  const writes = await mockApi(page, true);
  const errors: string[] = [];
  let closed = false;
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("websocket", (socket) => socket.on("close", () => { closed = true; }));
  await page.goto("/dashboard");
  await expect(value(page, "WebSocket")).toHaveText("up");
  await page.getByRole("link", { name: "Open live timing" }).click();
  await expect(page).toHaveURL(/\/live$/);
  await expect.poll(() => closed).toBe(true);
  expect(errors).toEqual([]);
  expect(writes).toEqual([]);
});
test("coalesces twenty same-frame runtime lease rechecks", async ({ page }) => {
  const writes = await mockApi(page);
  let calls = 0;
  let defer = false;
  let release!: (reply: Reply) => void;
  const pending = new Promise<Reply>((resolve) => { release = resolve; });
  await readiness(page, () => { calls++; return defer ? pending : { json: { status: "ready", services: { runtime_lease: "up" } } }; });
  await page.goto("/dashboard");
  await expect(value(page, "Runtime lease")).toHaveText("up");
  const baseline = calls;
  defer = true;
  const button = card(page).getByRole("button", { name: "Recheck runtime lease" });
  await button.click();
  await expect.poll(() => calls).toBe(baseline + 1);
  await button.evaluate((element) => { for (let i = 0; i < 20; i++) element.dispatchEvent(new MouseEvent("click", { bubbles: true })); });
  expect(calls).toBe(baseline + 1);
  release({ json: { status: "ready", services: { runtime_lease: "up" } } });
  await expect(value(page, "Runtime lease")).toHaveText("up");
  expect(calls).toBe(baseline + 1);
  expect(writes).toEqual([]);
});
