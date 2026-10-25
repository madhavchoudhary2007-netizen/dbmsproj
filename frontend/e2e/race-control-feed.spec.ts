import { expect, test, type Page } from "./mock-platform";

const admin = { id: "feed-admin", email: "feed@example.test", full_name: "Feed Admin", role: "ADMIN" };
const liveData = {
  active_sessions: 1, scheduled_events: 3, open_incidents: 2, drivers: 20,
  active_session: { name: "Grand Prix", circuit_name: "Silverstone" },
  next_event: { name: "Next GP", circuit_name: "Spa" },
};
type Reply = { status: number; json: unknown; wait?: Promise<void> };
type Harness = { count: number; writes: string[]; reply: () => Promise<Reply> };

async function harness(page: Page): Promise<Harness> {
  const state: Harness = { count: 0, writes: [], reply: async () => ({ status: 200, json: liveData }) };
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const pathname = new URL(request.url()).pathname;
    if (request.method() !== "GET") { state.writes.push(`${request.method()} ${pathname}`); await route.abort(); return; }
    if (pathname === "/api/auth/me") { await route.fulfill({ status: 200, json: admin }); return; }
    if (pathname === "/api/health") { await route.fulfill({ status: 200, json: { status: "healthy", services: { postgres: "healthy", mongodb: "healthy" } } }); return; }
    if (pathname === "/api/dashboard") {
      state.count += 1;
      const response = await state.reply();
      if (response.wait) await response.wait;
      await route.fulfill({ status: response.status, json: response.json });
      return;
    }
    await route.fulfill({ status: 200, json: [] });
  });
  return state;
}

async function visibility(page: Page, value: "hidden" | "visible") {
  await page.evaluate((next) => {
    Object.defineProperty(document, "visibilityState", { configurable: true, value: next });
    document.dispatchEvent(new Event("visibilitychange"));
  }, value);
}

test("shared dashboard feed polls, pauses when hidden, and fits a 320px ticker", async ({ page }) => {
  const state = await harness(page);
  await page.clock.install();
  await page.goto("/dashboard", { waitUntil: "domcontentloaded" });
  await expect(page.locator("[data-feed-state='populated']")).toBeVisible();
  expect(state.count).toBe(1);
  await expect(page.locator(".race-control-feed")).toContainText("ACTIVE: Grand Prix — Silverstone");
  await expect(page.locator(".race-control-feed")).toContainText("OPEN INCIDENTS: 2");
  await expect(page.locator(".race-control-feed")).toContainText("NEXT: Next GP — Spa");
  expect(await page.locator(".race-control-feed").evaluate((el) => Math.round(el.getBoundingClientRect().height))).toBe(40);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBe(true);

  await page.clock.runFor(30_000);
  await expect.poll(() => state.count).toBe(2);
  await visibility(page, "hidden");
  await page.clock.runFor(60_000);
  expect(state.count).toBe(2);
  await visibility(page, "visible");
  await expect.poll(() => state.count).toBe(3);
  expect(state.writes).toEqual([]);
});

test("delayed, empty, and rapid refresh states share one transport", async ({ page }) => {
  const state = await harness(page);
  let release!: () => void;
  const gate = new Promise<void>((resolve) => { release = resolve; });
  state.reply = async () => ({ status: 200, json: liveData, wait: gate });
  await page.goto("/dashboard", { waitUntil: "domcontentloaded" });
  await expect(page.locator("[data-feed-state='loading']")).toBeVisible();
  expect(state.count).toBe(1);
  release();
  await expect(page.locator("[data-feed-state='populated']")).toBeVisible();

  let empty = true;
  state.reply = async () => ({ status: 200, json: empty ? {} : liveData });
  await page.locator(".feed-status").getByRole("button", { name: "Refresh race control feed" }).click();
  await expect(page.locator("[data-feed-state='empty']")).toHaveCount(1);
  await expect(page.locator("[data-feed-state='empty']")).toContainText("Race control feed is empty.");
  await expect(page.locator(".race-control-feed")).toHaveCount(0);
  empty = false;
  let nextRelease!: () => void;
  const nextGate = new Promise<void>((resolve) => { nextRelease = resolve; });
  state.reply = async () => ({ status: 200, json: liveData, wait: nextGate });
  await Promise.all(Array.from({ length: 20 }, () => page.locator(".feed-status").getByRole("button", { name: "Refresh race control feed" }).click()));
  await expect.poll(() => state.count).toBe(3);
  nextRelease();
  await expect(page.locator("[data-feed-state='populated']")).toBeVisible();
  expect(state.writes).toEqual([]);
});

test("error, partial, retry, and real offline events recover the feed", async ({ page, context }) => {
  const state = await harness(page);
  let step = 0;
  state.reply = async () => {
    step += 1;
    if (step === 1 || step === 3) return { status: 503, json: { detail: "temporary outage" } };
    return { status: 200, json: liveData };
  };
  await page.goto("/dashboard", { waitUntil: "domcontentloaded" });
  await expect(page.locator("[data-feed-state='error']")).toBeVisible();
  await page.locator(".feed-status").getByRole("button", { name: "Refresh race control feed" }).click();
  await expect(page.locator("[data-feed-state='populated']")).toBeVisible();
  await expect(page.locator(".race-control-feed")).toContainText("ACTIVE: Grand Prix — Silverstone");
  await page.locator(".feed-status").getByRole("button", { name: "Refresh race control feed" }).click();
  await expect(page.locator("[data-feed-state='partial']")).toBeVisible();
  await expect(page.locator(".race-control-feed")).toContainText("NEXT: Next GP — Spa");
  await page.locator("[data-feed-state='partial']").getByRole("button", { name: "Refresh race control feed" }).click();
  await expect(page.locator("[data-feed-state='populated']")).toBeVisible();

  await context.setOffline(true);
  await expect(page.locator(".feed-status[data-connection='OFFLINE']")).toBeVisible();
  await context.setOffline(false);
  await expect(page.locator(".feed-status[data-connection='LIVE']")).toBeVisible();
  expect(state.count).toBe(5);
  expect(state.writes).toEqual([]);
});
