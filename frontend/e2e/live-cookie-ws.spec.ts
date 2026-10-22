import { expect, test } from "@playwright/test";

type WebSocketCapture = { url: string; protocols?: string | string[] };

const user = {
  id: "cookie-user",
  email: "operator@apexgrid.test",
  full_name: "Race Operator",
  role: "ADMIN",
};
const sessionId = "cookie-live-session";

test.fail(!process.env.RUN_XFAIL, "G11");

test("G11 cookie-only live session opens WebSocket without JWT protocols", async ({ page }) => {
  await page.route("http://localhost:8000/api/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path === "/api/auth/me") {
      await route.fulfill({ status: 200, json: user });
    } else if (path === "/api/sessions") {
      await route.fulfill({ status: 200, json: [{ id: sessionId, state: "ACTIVE" }] });
    } else if (path === "/api/demo-races") {
      await route.fulfill({ status: 200, json: [] });
    } else if (path === `/api/sessions/${sessionId}/live`) {
      await route.fulfill({
        status: 200,
        json: { session: { id: sessionId, state: "ACTIVE" }, drivers: [], packets: [] },
      });
    } else if (path === `/api/sessions/${sessionId}/laps`) {
      await route.fulfill({
        status: 200,
        json: { laps: [], incidents: [], pit_reservations: [] },
      });
    } else {
      await route.fulfill({ status: 200, json: [] });
    }
  });
  await page.context().addCookies([{
    name: "apexgrid_session",
    value: "fixture-session-cookie",
    domain: "localhost",
    path: "/",
    httpOnly: true,
    sameSite: "Lax",
  }]);
  await page.addInitScript(() => {
    const captureWindow = window as Window & { __wsCalls?: WebSocketCapture[] };
    const wsCalls: WebSocketCapture[] = [];
    localStorage.removeItem("apexgrid_token");
    captureWindow.__wsCalls = wsCalls;
    Object.defineProperty(window, "WebSocket", { configurable: true, value: class {
      constructor(url: string, protocols?: string | string[]) {
        wsCalls.push({ url, protocols });
      }
      close() {}
    } });
  });

  await page.goto("/live");
  const liveUrl = new RegExp(`/api/ws/sessions/${sessionId}$`);
  await expect.poll(async () => page.evaluate((pattern) =>
    ((window as Window & { __wsCalls?: WebSocketCapture[] }).__wsCalls ?? [])
      .filter((call) => new RegExp(pattern).test(call.url)).length,
  liveUrl.source)).toBeGreaterThan(0);
  const calls = await page.evaluate(() =>
    (window as Window & { __wsCalls?: WebSocketCapture[] }).__wsCalls ?? [],
  );
  const liveCall = calls.find((call) => liveUrl.test(call.url));
  if (!liveCall) throw new Error("Expected live session WebSocket call");
  expect(liveCall.url).toMatch(liveUrl);
  expect(liveCall.protocols).toBeUndefined();
  expect(await page.evaluate(() => localStorage.getItem("apexgrid_token"))).toBeNull();
});
