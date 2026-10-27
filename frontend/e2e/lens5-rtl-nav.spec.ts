import { expect, test, type Locator, type Page } from "./mock-platform";

type Reply = { status: number; json: unknown };
type Endpoint = { reply: Reply; gate?: Promise<void>; served?: () => void };
type Endpoints = Record<string, Endpoint>;

const adminUser = { id: 999, email: "admin@apexgrid.test", full_name: "Admin User", role: "ADMIN" };
const PAGE_SIZE = 50; // resource-page.tsx: const pageSize = 50

const ok = (json: unknown): Reply => ({ status: 200, json });
const fail = (): Reply => ({ status: 500, json: { detail: "Service unavailable" } });

const dashboard = {
  active_sessions: 1, scheduled_events: 3, open_incidents: 2, drivers: 20,
  active_session: { name: "Grand Prix", circuit_name: "Silverstone" },
  next_event: { name: "Next GP", circuit_name: "Spa" },
};
const health = { status: "healthy", services: { postgres: "healthy", mongodb: "healthy" } };
const championships = [
  { id: "ch-1", name: "World Championship", season: 2026 },
  { id: "ch-2", name: "Cup Series", season: 2025 },
];
const standingRows = [
  { driver_id: "drv-1", rank: 1, driver_name: "Ada Driver", number: 7, team_name: "Apex Racing", points: 120, wins: 3, podiums: 5 },
  { driver_id: "drv-2", rank: 2, driver_name: "Ben Driver", number: 9, team_name: "Blue Line", points: 98, wins: 1, podiums: 4 },
];
const driverRows = [
  { id: "drv-1", user_id: 1, full_name: "Ada Driver", number: 7, licence_number: "LIC-001", eligibility: "ACTIVE", team_name: "Apex Racing" },
];

// Collapses ids in paths so one mutable entry covers every championship.
function routeKey(method: string, pathname: string): string {
  const path = pathname.replace(/^\/api\/championships\/[^/]+\/(standings|recalculate)$/, "/api/championships/:id/$1");
  return `${method} ${path}`;
}

// Endpoints are read on every request, so a test can flip one to fail, restore it, or hold it.
async function serveApi(page: Page, endpoints: Endpoints): Promise<void> {
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const { pathname } = new URL(request.url());
    if (pathname === "/api/auth/me") return route.fulfill({ status: 200, json: adminUser });
    const endpoint = endpoints[routeKey(request.method(), pathname)] ?? { reply: ok([]) };
    if (endpoint.gate) await endpoint.gate;
    // A component that aborted the request (refresh or unmount) has no reader left for the reply.
    await route.fulfill({ status: endpoint.reply.status, json: endpoint.reply.json }).catch(() => undefined);
    endpoint.served?.();
  });
}

// Holds a reply until release() is called and reports, through served, once the reply has been delivered.
function hold(reply: Reply) {
  let release: () => void = () => undefined;
  const gate = new Promise<void>((resolve) => {
    release = () => resolve();
  });
  let markServed: () => void = () => undefined;
  const served = new Promise<void>((resolve) => {
    markServed = () => resolve();
  });
  return { endpoint: { reply, gate, served: markServed }, release, served };
}

// Mobile widths keep the sidebar in a drawer that must be opened before its links are reachable.
async function openNavigationIfCollapsed(page: Page): Promise<void> {
  if ((page.viewportSize()?.width ?? 1024) >= 1000) return;
  await page.getByRole("button", { name: "Open navigation", exact: true }).click();
}

async function expectNoHorizontalOverflow(target: Locator, label: string): Promise<void> {
  const extent = await target.evaluate((element) => ({ scroll: element.scrollWidth, client: element.clientWidth }));
  expect(extent.scroll, label).toBeLessThanOrEqual(extent.client + 1);
}

/* ------------------------------------------------------- RTL, no overflow */

const rtlPages = [
  {
    path: "/dashboard",
    heading: "Race operations",
    endpoints: (): Endpoints => ({ "GET /api/dashboard": { reply: ok(dashboard) }, "GET /api/health": { reply: ok(health) } }),
    populated: (page: Page) => page.locator(".dashboard-summary[data-testid='state-populated']"),
  },
  {
    path: "/standings",
    heading: "Standings",
    endpoints: (): Endpoints => ({
      "GET /api/championships": { reply: ok(championships) },
      "GET /api/championships/:id/standings": { reply: ok(standingRows) },
    }),
    populated: (page: Page) => page.locator("section[aria-label='Full standings']").getByTestId("state-populated"),
  },
  {
    path: "/championships",
    heading: "Championships",
    endpoints: (): Endpoints => ({ "GET /api/championships": { reply: ok(championships) } }),
    populated: (page: Page) => page.getByTestId("state-populated").getByRole("region", { name: "Championships", exact: true }),
  },
];

test.describe("E-2 Lens 5 RTL layout", () => {
  for (const rtlPage of rtlPages) {
    test(`E-2 Lens 5 ${rtlPage.path} in dir=rtl keeps its heading and populated state without horizontal overflow`, async ({ page }) => {
      await page.addInitScript(() => {
        const setRtl = () => { document.documentElement.dir = "rtl"; };
        document.addEventListener("readystatechange", setRtl);
        if (document.documentElement) setRtl();
      });
      await serveApi(page, rtlPage.endpoints());

      await page.goto(rtlPage.path, { waitUntil: "domcontentloaded" });
      await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
      await expect(page.getByRole("heading", { level: 1, name: rtlPage.heading, exact: true })).toBeVisible();
      await expect(rtlPage.populated(page)).toBeVisible();

      await expectNoHorizontalOverflow(page.locator("html"), `${rtlPage.path} html in rtl`);
      await expectNoHorizontalOverflow(page.locator("main#main-content"), `${rtlPage.path} main in rtl`);
    });
  }
});

/* ------------------------------------------------- navigation mid-request */

test("E-2 Lens 5 leaving championships while its slow response is held reports no errors and renders drivers", async ({ page }) => {
  const pageErrors: string[] = [];
  const consoleErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });

  const slowChampionships = hold(ok(championships));
  await serveApi(page, {
    "GET /api/championships": slowChampionships.endpoint,
    "GET /api/drivers": { reply: ok(driverRows) },
  });

  await page.goto("/championships", { waitUntil: "domcontentloaded" });
  await expect(page.getByTestId("state-loading")).toBeVisible();

  await openNavigationIfCollapsed(page);
  await page.locator("#primary-navigation").getByRole("link", { name: "Drivers", exact: true }).click();
  await expect(page).toHaveURL(/\/drivers$/);
  await expect(page.getByRole("heading", { level: 1, name: "Drivers", exact: true })).toBeVisible();

  slowChampionships.release();
  await slowChampionships.served;

  const drivers = page.getByTestId("state-populated").getByRole("region", { name: "Drivers", exact: true });
  await expect(drivers.locator("tbody tr")).toHaveCount(1);
  await expect(drivers.getByRole("cell", { name: "Ada Driver", exact: true })).toBeVisible();

  expect(pageErrors).toEqual([]);
  expect(consoleErrors.filter((text) => /unmounted|state update/i.test(text))).toEqual([]);
});

/* ------------------------------------------------------ pagination grazing */

test.describe("E-2 Lens 5 pagination boundaries on championships", () => {
  for (const count of [PAGE_SIZE - 1, PAGE_SIZE, PAGE_SIZE + 1]) {
    test(`E-2 Lens 5 championships with ${count} rows show the correct page count and next-page control`, async ({ page }) => {
      const rows = Array.from({ length: count }, (_, i) => ({ id: i + 1, name: `Series ${i + 1}`, season: 2026 }));
      await serveApi(page, { "GET /api/championships": { reply: ok(rows) } });

      await page.goto("/championships", { waitUntil: "domcontentloaded" });
      const region = page.getByTestId("state-populated").getByRole("region", { name: "Championships", exact: true });
      const pagination = page.locator(".dbms-pagination");
      await expect(region.locator("tbody tr")).toHaveCount(Math.min(count, PAGE_SIZE));
      await expect(page.locator(".record-count")).toHaveText(`${count} RECORDS`);

      if (count <= PAGE_SIZE) {
        // Exactly one page or fewer: no pagination control and every row is on the single page.
        await expect(page.locator(".resource-range")).toHaveText(`Showing 1–${count} of ${count}`);
        await expect(pagination).toHaveCount(0);
        await expect(region.getByRole("cell", { name: `Series ${count}`, exact: true })).toBeVisible();
        return;
      }

      // One row past the page size: exactly two pages, the first full and the second holding the single overflow row.
      await expect(pagination).toContainText("Page 1 of 2");
      await expect(page.locator(".resource-range")).toHaveText(`Showing 1–${PAGE_SIZE} of ${count}`);
      await expect(region.getByRole("cell", { name: `Series ${PAGE_SIZE}`, exact: true })).toBeVisible();
      await expect(region.getByRole("cell", { name: `Series ${count}`, exact: true })).toHaveCount(0);
      await expect(pagination.getByRole("button", { name: "Previous", exact: true })).toBeDisabled();
      await expect(pagination.getByRole("button", { name: "Next", exact: true })).toBeEnabled();

      await pagination.getByRole("button", { name: "Next", exact: true }).click();
      await expect(pagination).toContainText("Page 2 of 2");
      await expect(region.locator("tbody tr")).toHaveCount(1);
      await expect(region.getByRole("cell", { name: `Series ${count}`, exact: true })).toBeVisible();
      await expect(page.locator(".resource-range")).toHaveText(`Showing ${count}–${count} of ${count}`);
      await expect(pagination.getByRole("button", { name: "Next", exact: true })).toBeDisabled();
      await expect(pagination.getByRole("button", { name: "Previous", exact: true })).toBeEnabled();
    });
  }
});

/* ---------------------------------------------------- standings partial */

test("E-1 standings keep the last loaded classification as partial when a refresh fails and recover on retry", async ({ page }) => {
  const standingsKey = "GET /api/championships/:id/standings";
  const endpoints: Endpoints = {
    "GET /api/championships": { reply: ok(championships) },
    [standingsKey]: { reply: ok(standingRows) },
    "POST /api/championships/:id/recalculate": { reply: ok({ recalculated: true }) },
  };
  await serveApi(page, endpoints);

  await page.goto("/standings", { waitUntil: "domcontentloaded" });
  const region = page.locator("section[aria-label='Full standings']");
  await expect(region.getByTestId("state-populated")).toContainText("Ada Driver");

  endpoints[standingsKey] = { reply: fail() };
  await page.getByRole("button", { name: "Recalculate standings", exact: true }).click();
  await expect(page.locator(".notice").filter({ hasText: "Standings recalculated" })).toBeVisible();

  const partial = region.getByTestId("state-partial");
  await expect(partial).toContainText("Showing the last loaded standings");
  await expect(partial).toContainText("Ada Driver");
  await expect(region.getByTestId("state-populated")).toHaveCount(0);

  endpoints[standingsKey] = { reply: ok(standingRows) };
  await region.getByRole("button", { name: "Retry loading standings", exact: true }).click();
  await expect(region.getByTestId("state-populated")).toContainText("Ada Driver");
  await expect(region.getByTestId("state-partial")).toHaveCount(0);
});
