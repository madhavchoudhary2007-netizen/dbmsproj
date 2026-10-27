import type { Locator, Page, WebSocketRoute } from "@playwright/test";
import { expect, test } from "./mock-platform";

test.describe.configure({ timeout: 60_000 });
const expectSlow = expect.configure({ timeout: 15_000 });

const adminUser = { id: 999, email: "admin@apexgrid.test", full_name: "Admin User", role: "ADMIN" };

type Reply = { status?: number; json: unknown };
type Responder = (method: string) => Reply | Promise<Reply>;
type Routes = Record<string, Responder>;
type Flag = { down: boolean };
type StateName = "loading" | "empty" | "populated" | "error" | "partial";

const failure: Reply = { status: 500, json: { detail: "Service unavailable" } };
const ok = (json: unknown): Responder => () => ({ json });
const down: Responder = () => failure;
const serve = (json: unknown, flag: Flag): Responder => () => (flag.down ? failure : { json });

async function mockApi(page: Page, routes: Routes) {
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const pathname = new URL(request.url()).pathname;
    if (pathname === "/api/auth/me") {
      await route.fulfill({ status: 200, json: adminUser });
      return;
    }
    const responder = routes[pathname];
    const reply: Reply = responder ? await responder(request.method()) : { json: [] };
    await route.fulfill({ status: reply.status ?? 200, json: reply.json });
  });
}

function latch() {
  let open: () => void = () => undefined;
  const released = new Promise<void>((resolve) => {
    open = () => resolve();
  });
  return { released, open };
}

async function routeSessionSocket(page: Page): Promise<{ ready: Promise<WebSocketRoute> }> {
  let resolveReady: (socket: WebSocketRoute) => void = () => undefined;
  const ready = new Promise<WebSocketRoute>((resolve) => {
    resolveReady = resolve;
  });
  await page.routeWebSocket("**/api/ws/sessions/*", (socket) => {
    resolveReady(socket);
  });
  return { ready };
}

// Nearest NbCard (nb-face) or .panel that contains the given locator.
function cardOf(locator: Locator): Locator {
  return locator.locator(
    "xpath=ancestor::*[contains(concat(' ', normalize-space(@class), ' '), ' nb-face ') or contains(concat(' ', normalize-space(@class), ' '), ' panel ')][1]",
  );
}

function stateIn(scope: Locator, state: StateName): Locator {
  return scope.getByTestId(`state-${state}`);
}

// ---------------------------------------------------------------- sessions

const eventRow = { id: 1, name: "Apex Sprint", round_number: 1 };
const sessionRow = {
  id: "sess-1",
  event_id: 1,
  event_name: "Apex Sprint",
  session_type: "RACE",
  state: "SCHEDULED",
  scheduled_at: "2026-10-28T10:00:00Z",
  total_laps: 10,
};
const resultRows = [
  { id: "res-1", position: 1, driver_name: "Ada Vale", laps: 10 },
  { id: "res-2", position: 2, driver_name: "Ben Hart", laps: 10 },
];

function sessionRoutes(extra: Routes): Routes {
  return {
    "/api/sessions": ok([sessionRow]),
    "/api/events": ok([eventRow]),
    "/api/drivers": ok([]),
    ...extra,
  };
}

function overviewCard(page: Page): Locator {
  return cardOf(page.locator(".session-count-sticker"));
}

async function openResults(page: Page) {
  await page.getByRole("region", { name: "Sessions", exact: true }).getByText("Apex Sprint", { exact: true }).click();
  await page.getByRole("button", { name: "Load results", exact: true }).click();
}

test("E-1 /sessions SessionOverview renders the loading state", async ({ page }) => {
  const gate = latch();
  await mockApi(page, sessionRoutes({
    "/api/sessions": async () => {
      await gate.released;
      return { json: [sessionRow] };
    },
  }));
  await page.goto("/sessions", { waitUntil: "domcontentloaded" });
  await expect(stateIn(overviewCard(page), "loading")).toBeVisible();
});

test("E-1 /sessions SessionOverview renders the error state", async ({ page }) => {
  await mockApi(page, sessionRoutes({ "/api/sessions": down }));
  await page.goto("/sessions", { waitUntil: "domcontentloaded" });
  await expect(stateIn(overviewCard(page), "error")).toContainText("Service unavailable");
});

test("E-1 /sessions SessionOverview renders the empty state", async ({ page }) => {
  await mockApi(page, sessionRoutes({ "/api/sessions": ok([]) }));
  await page.goto("/sessions", { waitUntil: "domcontentloaded" });
  await expect(stateIn(overviewCard(page), "empty")).toContainText("No records returned by the API.");
});

test("E-1 /sessions SessionOverview renders the populated state", async ({ page }) => {
  await mockApi(page, sessionRoutes({}));
  await page.goto("/sessions", { waitUntil: "domcontentloaded" });
  await expect(stateIn(overviewCard(page), "populated")).toBeVisible();
  await expect(page.getByRole("region", { name: "Sessions", exact: true })).toContainText("Apex Sprint");
});

test("E-1 /sessions SessionOverview renders the partial state when refresh fails", async ({ page }) => {
  const flag: Flag = { down: false };
  await mockApi(page, sessionRoutes({ "/api/sessions": serve([sessionRow], flag) }));
  await page.goto("/sessions", { waitUntil: "domcontentloaded" });
  const card = overviewCard(page);
  await expect(stateIn(card, "populated")).toBeVisible();
  flag.down = true;
  await card.getByRole("button", { name: "Refresh", exact: true }).click();
  await expect(stateIn(card, "partial")).toContainText("The latest refresh failed.");
});

test("E-1 /sessions SessionResults renders the loading state", async ({ page }) => {
  const gate = latch();
  await mockApi(page, sessionRoutes({
    "/api/sessions/sess-1/results": async () => {
      await gate.released;
      return { json: resultRows };
    },
  }));
  await page.goto("/sessions", { waitUntil: "domcontentloaded" });
  await openResults(page);
  await expect(stateIn(page.locator(".results-table"), "loading")).toBeVisible();
});

test("E-1 /sessions SessionResults renders the error state", async ({ page }) => {
  await mockApi(page, sessionRoutes({ "/api/sessions/sess-1/results": down }));
  await page.goto("/sessions", { waitUntil: "domcontentloaded" });
  await openResults(page);
  await expect(stateIn(page.locator(".results-table"), "error")).toContainText("Service unavailable");
});

test("E-1 /sessions SessionResults renders the empty state", async ({ page }) => {
  await mockApi(page, sessionRoutes({ "/api/sessions/sess-1/results": ok([]) }));
  await page.goto("/sessions", { waitUntil: "domcontentloaded" });
  await openResults(page);
  await expect(stateIn(page.locator(".results-table"), "empty")).toContainText("No result rows are recorded for this session.");
});

test("E-1 /sessions SessionResults renders the populated state", async ({ page }) => {
  await mockApi(page, sessionRoutes({ "/api/sessions/sess-1/results": ok(resultRows) }));
  await page.goto("/sessions", { waitUntil: "domcontentloaded" });
  await openResults(page);
  const results = page.locator(".results-table");
  await expect(stateIn(results, "populated")).toBeVisible();
  await expect(results.getByRole("heading", { name: "2 classified entries" })).toBeVisible();
});

test("E-1 /sessions SessionResults renders the partial state while an update is in progress", async ({ page }) => {
  let calls = 0;
  const second = latch();
  await mockApi(page, sessionRoutes({
    "/api/sessions/sess-1/results": async () => {
      calls += 1;
      if (calls > 1) await second.released;
      return { json: resultRows };
    },
  }));
  await page.goto("/sessions", { waitUntil: "domcontentloaded" });
  await openResults(page);
  const results = page.locator(".results-table");
  await expect(stateIn(results, "populated")).toBeVisible();
  await page.getByRole("button", { name: "Load results", exact: true }).click();
  await expect(stateIn(results, "partial")).toContainText("Showing saved results while an update is in progress.");
});

test("E-1 /sessions SessionResults renders the partial state when an update fails", async ({ page }) => {
  let calls = 0;
  await mockApi(page, sessionRoutes({
    "/api/sessions/sess-1/results": async () => {
      calls += 1;
      if (calls > 1) return failure;
      return { json: resultRows };
    },
  }));
  await page.goto("/sessions", { waitUntil: "domcontentloaded" });
  await openResults(page);
  const results = page.locator(".results-table");
  await expect(stateIn(results, "populated")).toBeVisible();
  await page.getByRole("button", { name: "Load results", exact: true }).click();
  await expect(stateIn(results, "partial")).toContainText("Showing saved results because the latest update failed.");
});

// ---------------------------------------------------------------- live demo race list

const demoRace = {
  session_id: "sess-1",
  event_name: "Apex Sprint",
  circuit_name: "Apex Ring",
  car_count: 2,
  total_laps: 10,
  state: "ACTIVE",
  created_at: "2026-10-28T09:00:00Z",
};
const liveSession = {
  id: "sess-1",
  event_id: 1,
  event_name: "Apex Sprint",
  session_type: "RACE",
  state: "ACTIVE",
  total_laps: 10,
  scheduled_at: "2026-10-28T10:00:00Z",
};
const driver = {
  id: "drv-1",
  full_name: "Ada Vale",
  number: 7,
  licence_number: "LIC-7",
  team_name: "Apex Team",
  eligibility: "ACTIVE",
};
const packet = {
  session_id: "sess-1",
  driver_id: "drv-1",
  ts: "2026-10-28T10:05:00Z",
  lap: 3,
  sector: 2,
  position: 1,
  speed_kph: 287,
  throttle_pct: 98,
  brake_pct: 0,
  tire_compound: "SOFT",
  tire_age_laps: 4,
  tire_wear_pct: 12,
  pit_state: "NONE",
  elapsed_ms: 200000,
  lap_time_ms: 91234,
  sector_ms: [30000, 31000, 30234],
};
const liveState = { ...liveSession, safety_car: false };
const liveFull = { session: liveState, drivers: [driver], packets: [packet] };
const emptyLive = { session: liveState, drivers: [], packets: [] };
const lapRow = { session_id: "sess-1", driver_id: "drv-1", lap: 3, sector_ms: [30000, 31000, 30234], lap_time_ms: 91234, position: 1 };
const incident = { id: "inc-1", driver_name: "Ada Vale", lap: 2, description: "Track limits", state: "OPEN" };
const timingUpdate = {
  type: "timing.update",
  session_id: "sess-1",
  data: { cars: [{ driver_id: "drv-1", position: 1, lap: 3, gap: "LEADER", last_lap_ms: 91234 }], safety_car: false },
};
const sessionStateMessage = { type: "session.state", session_id: "sess-1", data: { state: "ACTIVE" } };

function liveRoutes(overrides: Routes): Routes {
  return {
    "/api/sessions": ok([liveSession]),
    "/api/demo-races": ok([demoRace]),
    "/api/sessions/sess-1/live": ok(liveFull),
    "/api/sessions/sess-1/laps": ok({ laps: [], incidents: [], pit_reservations: [] }),
    ...overrides,
  };
}

function demoPanel(page: Page): Locator {
  return page.getByRole("region", { name: "Live race demos", exact: true });
}

test("E-1 /live demo race list renders the loading state", async ({ page }) => {
  const gate = latch();
  await mockApi(page, liveRoutes({
    "/api/demo-races": async () => {
      await gate.released;
      return { json: [demoRace] };
    },
  }));
  await page.goto("/live", { waitUntil: "domcontentloaded" });
  await expect(stateIn(demoPanel(page), "loading")).toBeVisible();
});

test("E-1 /live demo race list renders the error state", async ({ page }) => {
  await mockApi(page, liveRoutes({ "/api/sessions": down, "/api/demo-races": down }));
  await page.goto("/live", { waitUntil: "domcontentloaded" });
  await expect(stateIn(demoPanel(page), "error")).toContainText("Service unavailable");
});

test("E-1 /live demo race list renders the empty state", async ({ page }) => {
  await mockApi(page, liveRoutes({ "/api/sessions": ok([]), "/api/demo-races": ok([]) }));
  await page.goto("/live", { waitUntil: "domcontentloaded" });
  await expect(stateIn(demoPanel(page), "empty")).toContainText("No generated races are available.");
});

test("E-1 /live demo race list renders the populated state", async ({ page }) => {
  await mockApi(page, liveRoutes({}));
  await page.goto("/live", { waitUntil: "domcontentloaded" });
  const panel = demoPanel(page);
  await expect(stateIn(panel, "populated")).toBeVisible();
  await expect(panel.getByRole("button", { name: "Show Apex Sprint sess-1 live timing", exact: true })).toBeVisible();
});

test("E-1 /live demo race list renders the partial state for a truncated list", async ({ page }) => {
  const completed = Array.from({ length: 7 }, (_, index) => ({
    ...demoRace,
    session_id: `old-${index}`,
    state: "COMPLETED",
  }));
  await mockApi(page, liveRoutes({ "/api/demo-races": ok([demoRace, ...completed]) }));
  await page.goto("/live", { waitUntil: "domcontentloaded" });
  await expect(stateIn(demoPanel(page), "partial")).toContainText("Showing 6 of 8 generated races");
});

test("E-1 /live demo race list renders the partial state when refresh fails", async ({ page }) => {
  const flag: Flag = { down: false };
  await mockApi(page, liveRoutes({
    "/api/sessions": serve([liveSession], flag),
    "/api/demo-races": serve([demoRace], flag),
  }));
  await page.goto("/live", { waitUntil: "domcontentloaded" });
  await expect(stateIn(demoPanel(page), "populated")).toBeVisible();
  flag.down = true;
  await expectSlow(stateIn(demoPanel(page), "partial")).toContainText("Showing 1 of 1 generated races");
});

// ---------------------------------------------------------------- live timing, records, telemetry, chart

function towerCard(page: Page): Locator {
  return cardOf(page.getByRole("heading", { name: /cars on timing/ }));
}

function lapCard(page: Page): Locator {
  return cardOf(page.getByRole("heading", { name: "Driver lap and sector history", exact: true }));
}

function incidentCard(page: Page): Locator {
  return cardOf(page.getByRole("heading", { name: "Incidents and pit stops", exact: true }));
}

function telemetryCard(page: Page): Locator {
  return cardOf(page.getByRole("heading", { name: /samples in view/ }));
}

function chartCard(page: Page): Locator {
  return cardOf(page.getByRole("heading", { name: "Speed · km/h", exact: true }));
}

async function pickDriver(page: Page, label: string) {
  await towerCard(page).getByText(label, { exact: true }).click();
}

test("E-1 /live TimingTower renders the loading state", async ({ page }) => {
  const gate = latch();
  await mockApi(page, liveRoutes({
    "/api/sessions/sess-1/live": async () => {
      await gate.released;
      return { json: liveFull };
    },
  }));
  await page.goto("/live", { waitUntil: "domcontentloaded" });
  await expect(stateIn(towerCard(page), "loading")).toBeVisible();
});

test("E-1 /live TimingTower renders the error state", async ({ page }) => {
  await mockApi(page, liveRoutes({ "/api/sessions/sess-1/live": down }));
  await page.goto("/live", { waitUntil: "domcontentloaded" });
  await expect(stateIn(towerCard(page), "error")).toContainText("Service unavailable");
});

test("E-1 /live TimingTower renders the empty state", async ({ page }) => {
  await mockApi(page, liveRoutes({ "/api/sessions/sess-1/live": ok(emptyLive) }));
  await page.goto("/live", { waitUntil: "domcontentloaded" });
  await expect(stateIn(towerCard(page), "empty")).toContainText("Waiting for timing and telemetry packets from this session.");
});

test("E-1 /live TimingTower renders the populated state", async ({ page }) => {
  await mockApi(page, liveRoutes({}));
  await page.goto("/live", { waitUntil: "domcontentloaded" });
  const card = towerCard(page);
  await expect(stateIn(card, "populated")).toBeVisible();
  await expect(card.getByText("Ada Vale", { exact: true })).toBeVisible();
});

test("E-1 /live TimingTower renders the partial state when a snapshot refresh fails", async ({ page }) => {
  const flag: Flag = { down: false };
  const { ready } = await routeSessionSocket(page);
  await mockApi(page, liveRoutes({ "/api/sessions/sess-1/live": serve(liveFull, flag) }));
  await page.goto("/live", { waitUntil: "domcontentloaded" });
  const card = towerCard(page);
  await expect(stateIn(card, "populated")).toBeVisible();
  flag.down = true;
  const socket = await ready;
  socket.send(JSON.stringify(sessionStateMessage));
  await expectSlow(stateIn(card, "partial")).toContainText("Showing 1 retained drivers.");
});

test("E-1 /live RaceRecords lap table renders the loading state", async ({ page }) => {
  const gate = latch();
  await mockApi(page, liveRoutes({
    "/api/sessions/sess-1/laps": async () => {
      await gate.released;
      return { json: { laps: [], incidents: [], pit_reservations: [] } };
    },
  }));
  await page.goto("/live", { waitUntil: "domcontentloaded" });
  await expect(stateIn(lapCard(page), "loading")).toBeVisible();
});

test("E-1 /live RaceRecords lap table renders the error state", async ({ page }) => {
  await mockApi(page, liveRoutes({ "/api/sessions/sess-1/laps": down }));
  await page.goto("/live", { waitUntil: "domcontentloaded" });
  await expect(stateIn(lapCard(page), "error")).toContainText("Service unavailable");
});

test("E-1 /live RaceRecords lap table renders the empty state", async ({ page }) => {
  await mockApi(page, liveRoutes({ "/api/sessions/sess-1/laps": ok({ laps: [], incidents: [], pit_reservations: [] }) }));
  await page.goto("/live", { waitUntil: "domcontentloaded" });
  await expect(stateIn(lapCard(page), "empty")).toContainText("No records returned by the API.");
});

test("E-1 /live RaceRecords renders the populated state for laps and incidents", async ({ page }) => {
  await mockApi(page, liveRoutes({
    "/api/sessions/sess-1/laps": ok({ laps: [lapRow], incidents: [incident], pit_reservations: [] }),
  }));
  await page.goto("/live", { waitUntil: "domcontentloaded" });
  await expect(stateIn(lapCard(page), "populated")).toContainText("Ada Vale");
  await expect(incidentCard(page).getByText("Track limits", { exact: true })).toBeVisible();
});

test("E-1 /live RaceRecords lap table renders the partial state when a records refresh fails", async ({ page }) => {
  const flag: Flag = { down: false };
  await mockApi(page, liveRoutes({
    "/api/sessions/sess-1/laps": serve({ laps: [lapRow], incidents: [], pit_reservations: [] }, flag),
  }));
  await page.goto("/live", { waitUntil: "domcontentloaded" });
  await expect(stateIn(lapCard(page), "populated")).toBeVisible();
  flag.down = true;
  await expectSlow(stateIn(lapCard(page), "partial")).toContainText("Showing 1 of 1 records");
});

test("E-1 /live LatestTelemetry renders the loading state", async ({ page }) => {
  const gate = latch();
  await mockApi(page, liveRoutes({
    "/api/sessions/sess-1/live": async () => {
      await gate.released;
      return { json: liveFull };
    },
  }));
  await page.goto("/live", { waitUntil: "domcontentloaded" });
  await expect(stateIn(telemetryCard(page), "loading")).toBeVisible();
});

test("E-1 /live LatestTelemetry renders the error state", async ({ page }) => {
  await mockApi(page, liveRoutes({ "/api/sessions/sess-1/live": down }));
  await page.goto("/live", { waitUntil: "domcontentloaded" });
  await expect(stateIn(telemetryCard(page), "error")).toContainText("Service unavailable");
});

test("E-1 /live LatestTelemetry renders the empty state", async ({ page }) => {
  await mockApi(page, liveRoutes({ "/api/sessions/sess-1/live": ok(emptyLive) }));
  await page.goto("/live", { waitUntil: "domcontentloaded" });
  await expect(stateIn(telemetryCard(page), "empty")).toContainText("No records returned by the API.");
});

test("E-1 /live LatestTelemetry renders the populated state", async ({ page }) => {
  await mockApi(page, liveRoutes({}));
  await page.goto("/live", { waitUntil: "domcontentloaded" });
  const card = telemetryCard(page);
  await expect(stateIn(card, "populated")).toBeVisible();
  await expect(card.getByText("drv-1", { exact: true })).toBeVisible();
});

test("E-1 /live LatestTelemetry renders the partial state when a snapshot refresh fails", async ({ page }) => {
  const flag: Flag = { down: false };
  const { ready } = await routeSessionSocket(page);
  await mockApi(page, liveRoutes({ "/api/sessions/sess-1/live": serve(liveFull, flag) }));
  await page.goto("/live", { waitUntil: "domcontentloaded" });
  const card = telemetryCard(page);
  await expect(stateIn(card, "populated")).toBeVisible();
  flag.down = true;
  const socket = await ready;
  socket.send(JSON.stringify(sessionStateMessage));
  await expectSlow(stateIn(card, "partial")).toContainText("Showing 1 retained samples of 1.");
});

test("E-1 /live chart frame renders the loading state", async ({ page }) => {
  const gate = latch();
  const { ready } = await routeSessionSocket(page);
  await mockApi(page, liveRoutes({
    "/api/sessions/sess-1/live": async () => {
      await gate.released;
      return { json: liveFull };
    },
  }));
  await page.goto("/live", { waitUntil: "domcontentloaded" });
  const socket = await ready;
  socket.send(JSON.stringify(timingUpdate));
  await pickDriver(page, "drv-1");
  await expect(chartCard(page).getByTestId("chart-loading")).toBeVisible();
});

test("E-1 /live chart frame renders the empty state", async ({ page }) => {
  const { ready } = await routeSessionSocket(page);
  await mockApi(page, liveRoutes({ "/api/sessions/sess-1/live": ok(emptyLive) }));
  await page.goto("/live", { waitUntil: "domcontentloaded" });
  const socket = await ready;
  socket.send(JSON.stringify(timingUpdate));
  await pickDriver(page, "drv-1");
  await expect(stateIn(chartCard(page), "empty")).toContainText("Waiting for timing and telemetry packets from this session.");
});

test("E-1 /live chart frame renders the error state", async ({ page }) => {
  const { ready } = await routeSessionSocket(page);
  await mockApi(page, liveRoutes({ "/api/sessions/sess-1/live": down }));
  await page.goto("/live", { waitUntil: "domcontentloaded" });
  const socket = await ready;
  socket.send(JSON.stringify(timingUpdate));
  await pickDriver(page, "drv-1");
  await expect(stateIn(chartCard(page), "error")).toContainText("Service unavailable");
});

test("E-1 /live chart frame renders the populated state", async ({ page }) => {
  await mockApi(page, liveRoutes({}));
  await page.goto("/live", { waitUntil: "domcontentloaded" });
  await pickDriver(page, "Ada Vale");
  await expect(stateIn(chartCard(page), "populated")).toBeVisible();
});

test("E-1 /live chart frame renders the partial state when a snapshot refresh fails", async ({ page }) => {
  const flag: Flag = { down: false };
  const { ready } = await routeSessionSocket(page);
  await mockApi(page, liveRoutes({ "/api/sessions/sess-1/live": serve(liveFull, flag) }));
  await page.goto("/live", { waitUntil: "domcontentloaded" });
  await pickDriver(page, "Ada Vale");
  const card = chartCard(page);
  await expect(stateIn(card, "populated")).toBeVisible();
  flag.down = true;
  const socket = await ready;
  socket.send(JSON.stringify(sessionStateMessage));
  await expectSlow(stateIn(card, "partial")).toContainText("Service unavailable");
});

// ---------------------------------------------------------------- analytics

const analyticsRow = {
  id: 1,
  full_name: "Ada Vale",
  number: 7,
  team_name: "Apex Team",
  sessions: 3,
  classified: 3,
  best_finish: 1,
  wins: 1,
  avg_lap_time_ms: 90000,
  points: 25,
};

function analyticsPanel(page: Page): Locator {
  return cardOf(page.getByRole("heading", { name: /driver records/i }));
}

function analyticsRoutes(analytics: Responder): Routes {
  return { "/api/analytics/drivers": analytics };
}

test("E-1 /analytics results render the loading state", async ({ page }) => {
  const gate = latch();
  await mockApi(page, analyticsRoutes(async () => {
    await gate.released;
    return { json: [analyticsRow] };
  }));
  await page.goto("/analytics", { waitUntil: "domcontentloaded" });
  await page.getByRole("button", { name: "Apply filters", exact: true }).click();
  await expect(analyticsPanel(page).getByRole("status").filter({ hasText: "Loading from API" })).toBeVisible();
});

test("E-1 /analytics results render the error state", async ({ page }) => {
  await mockApi(page, analyticsRoutes(down));
  await page.goto("/analytics", { waitUntil: "domcontentloaded" });
  await page.getByRole("button", { name: "Apply filters", exact: true }).click();
  await expect(page.locator(".filter-panel").locator("xpath=following-sibling::*[1]")).toContainText("Service unavailable");
  await expect(analyticsPanel(page)).toContainText("Apply filters to load driver analytics.");
});

test("E-1 /analytics results render the empty state", async ({ page }) => {
  await mockApi(page, analyticsRoutes(ok([])));
  await page.goto("/analytics", { waitUntil: "domcontentloaded" });
  await page.getByRole("button", { name: "Apply filters", exact: true }).click();
  const panel = analyticsPanel(page);
  await expect(panel.getByRole("heading", { name: "0 driver records" })).toBeVisible();
  await expect(panel.getByRole("status").filter({ hasText: "No records returned by the API." })).toBeVisible();
});

test("E-1 /analytics results render the populated state", async ({ page }) => {
  await mockApi(page, analyticsRoutes(ok([analyticsRow])));
  await page.goto("/analytics", { waitUntil: "domcontentloaded" });
  await page.getByRole("button", { name: "Apply filters", exact: true }).click();
  const panel = analyticsPanel(page);
  await expect(panel.getByRole("heading", { name: "1 driver records" })).toBeVisible();
  await expect(panel.getByRole("table")).toContainText("Ada Vale");
});

test("E-1 /analytics results render the partial state when a refresh fails", async ({ page }) => {
  const flag: Flag = { down: false };
  await mockApi(page, analyticsRoutes(serve([analyticsRow], flag)));
  await page.goto("/analytics", { waitUntil: "domcontentloaded" });
  const apply = page.getByRole("button", { name: "Apply filters", exact: true });
  await apply.click();
  const panel = analyticsPanel(page);
  await expect(panel.getByRole("table")).toContainText("Ada Vale");
  flag.down = true;
  await apply.click();
  await expect(page.locator(".filter-panel").locator("xpath=following-sibling::*[1]")).toContainText("Service unavailable");
  await expect(panel.getByRole("table")).toContainText("Ada Vale");
});

// ---------------------------------------------------------------- resource pages (championships)

const championshipRows = [
  { id: "ch-1", name: "Apex Cup", season: 2026 },
  { id: "ch-2", name: "Harbour Trophy", season: 2026 },
];

function resourceTable(page: Page): Locator {
  return page.locator(".resource-toolbar").locator("xpath=..");
}

test("E-1 /championships resource table renders the loading state", async ({ page }) => {
  const gate = latch();
  await mockApi(page, {
    "/api/championships": async () => {
      await gate.released;
      return { json: championshipRows };
    },
  });
  await page.goto("/championships", { waitUntil: "domcontentloaded" });
  await expect(stateIn(resourceTable(page), "loading")).toBeVisible();
});

test("E-1 /championships resource table renders the error state", async ({ page }) => {
  await mockApi(page, { "/api/championships": down });
  await page.goto("/championships", { waitUntil: "domcontentloaded" });
  await expect(stateIn(resourceTable(page), "error")).toContainText("Service unavailable");
});

test("E-1 /championships resource table renders the empty state", async ({ page }) => {
  await mockApi(page, { "/api/championships": ok([]) });
  await page.goto("/championships", { waitUntil: "domcontentloaded" });
  await expect(stateIn(resourceTable(page), "empty")).toContainText("No records returned by the API.");
});

test("E-1 /championships resource table renders the populated state", async ({ page }) => {
  await mockApi(page, { "/api/championships": ok(championshipRows) });
  await page.goto("/championships", { waitUntil: "domcontentloaded" });
  await expect(stateIn(resourceTable(page), "populated")).toBeVisible();
  await expect(page.getByRole("region", { name: "Championships", exact: true })).toContainText("Apex Cup");
});

test("E-1 /championships resource table renders the partial state for a filtered subset", async ({ page }) => {
  await mockApi(page, { "/api/championships": ok(championshipRows) });
  await page.goto("/championships", { waitUntil: "domcontentloaded" });
  await expect(stateIn(resourceTable(page), "populated")).toBeVisible();
  await page.getByLabel("Filter records").fill("Apex");
  await expect(stateIn(resourceTable(page), "partial")).toContainText("Showing 1 of 2 records");
});

test("E-1 /championships resource table renders the partial state when a refresh fails", async ({ page }) => {
  const flag: Flag = { down: false };
  await mockApi(page, { "/api/championships": serve(championshipRows, flag) });
  await page.goto("/championships", { waitUntil: "domcontentloaded" });
  const table = resourceTable(page);
  await expect(stateIn(table, "populated")).toBeVisible();
  flag.down = true;
  await page.locator(".resource-toolbar").getByRole("button", { name: "Refresh", exact: true }).click();
  await expect(stateIn(table, "partial")).toContainText("Showing 2 of 2 records");
});

// ---------------------------------------------------------------- membership history (/drivers)

const driverRow = {
  id: "drv-1",
  full_name: "Ada Vale",
  number: 7,
  licence_number: "LIC-7",
  eligibility: "ACTIVE",
  team_name: "Apex Team",
  user_id: 5,
};
const membershipRow = { id: "m1", driver_id: "drv-1", team_name: "Apex Team", start_date: "2026-01-01", end_date: null };

function driverRoutes(memberships: Responder, extra: Routes = {}): Routes {
  return {
    "/api/drivers": ok([driverRow]),
    "/api/drivers/drv-1/memberships": memberships,
    ...extra,
  };
}

async function openDriverRecord(page: Page): Promise<Locator> {
  await page.getByRole("region", { name: "Drivers", exact: true }).getByText("Ada Vale", { exact: true }).click();
  return page.getByRole("dialog", { name: "Record details", exact: true });
}

function membershipHistory(dialog: Locator): Locator {
  return dialog
    .getByRole("heading", { name: "Ada Vale", exact: true })
    .locator("xpath=ancestor::div[contains(concat(' ', normalize-space(@class), ' '), ' membership-history ')][1]");
}

test("E-1 /drivers membership history renders the loading state", async ({ page }) => {
  const gate = latch();
  await mockApi(page, driverRoutes(async () => {
    await gate.released;
    return { json: [membershipRow] };
  }));
  await page.goto("/drivers", { waitUntil: "domcontentloaded" });
  const dialog = await openDriverRecord(page);
  await expect(stateIn(membershipHistory(dialog), "loading")).toBeVisible();
});

test("E-1 /drivers membership history renders the error state", async ({ page }) => {
  await mockApi(page, driverRoutes(down));
  await page.goto("/drivers", { waitUntil: "domcontentloaded" });
  const dialog = await openDriverRecord(page);
  await expect(stateIn(membershipHistory(dialog), "error")).toContainText("Service unavailable");
});

test("E-1 /drivers membership history renders the empty state", async ({ page }) => {
  await mockApi(page, driverRoutes(ok([])));
  await page.goto("/drivers", { waitUntil: "domcontentloaded" });
  const dialog = await openDriverRecord(page);
  await expect(stateIn(membershipHistory(dialog), "empty")).toContainText("No membership history returned.");
});

test("E-1 /drivers membership history renders the populated state", async ({ page }) => {
  await mockApi(page, driverRoutes(ok([membershipRow])));
  await page.goto("/drivers", { waitUntil: "domcontentloaded" });
  const dialog = await openDriverRecord(page);
  const history = membershipHistory(dialog);
  await expect(stateIn(history, "populated")).toBeVisible();
  await expect(history.getByText("Apex Team", { exact: true })).toBeVisible();
});

test("E-1 /drivers membership history renders the partial state when a reload fails", async ({ page }) => {
  const flag: Flag = { down: false };
  await mockApi(page, driverRoutes(serve([membershipRow], flag), {
    "/api/team-memberships/m1": async () => {
      flag.down = true;
      return { json: {} };
    },
  }));
  await page.goto("/drivers", { waitUntil: "domcontentloaded" });
  const dialog = await openDriverRecord(page);
  const history = membershipHistory(dialog);
  await expect(stateIn(history, "populated")).toBeVisible();
  await dialog.getByRole("button", { name: "End membership", exact: true }).click();
  await expect(stateIn(history, "partial")).toContainText("Some membership history could not be loaded.");
});

// ---------------------------------------------------------------- DBMS workspace (/dbms)

const dbOverview = { postgres: "up", mongodb: "up", updated_at: "2026-10-28T10:00:00Z" };

function statusPanel(page: Page): Locator {
  return page.getByRole("heading", { name: "Live system state", exact: true }).locator("xpath=ancestor::section[1]");
}

function telemetryPanel(page: Page): Locator {
  return page.getByRole("heading", { name: "Telemetry documents", exact: true }).locator("xpath=ancestor::section[1]");
}

test("E-1 /dbms workspace status renders the loading state", async ({ page }) => {
  const gate = latch();
  await mockApi(page, {
    "/api/dbms/overview": async () => {
      await gate.released;
      return { json: dbOverview };
    },
  });
  await page.goto("/dbms", { waitUntil: "domcontentloaded" });
  await expect(statusPanel(page)).toContainText("Connecting…");
  await expect(statusPanel(page)).toContainText("PostgreSQL · checking");
});

test("E-1 /dbms workspace status renders the error state", async ({ page }) => {
  await mockApi(page, { "/api/dbms/overview": down });
  await page.goto("/dbms", { waitUntil: "domcontentloaded" });
  await expect(statusPanel(page).locator(".notice.error-notice")).toContainText("Service unavailable");
});

test("E-1 /dbms workspace telemetry documents render the empty state", async ({ page }) => {
  await mockApi(page, {
    "/api/dbms/overview": ok(dbOverview),
    "/api/dbms/mongo/collections/telemetry": ok({ documents: [], total: 0 }),
  });
  await page.goto("/dbms#telemetry", { waitUntil: "domcontentloaded" });
  const panel = telemetryPanel(page);
  await expect(panel.getByRole("status").filter({ hasText: "No records returned by the API." })).toBeVisible();
  await expect(panel).toContainText("0 documents");
});

test("E-1 /dbms workspace status renders the populated state", async ({ page }) => {
  await mockApi(page, { "/api/dbms/overview": ok(dbOverview) });
  await page.goto("/dbms", { waitUntil: "domcontentloaded" });
  await expect(statusPanel(page)).toContainText("PostgreSQL · up");
  await expect(statusPanel(page)).toContainText("MongoDB · up");
});

test("E-1 /dbms workspace status renders the partial state when a refresh fails", async ({ page }) => {
  const flag: Flag = { down: false };
  await mockApi(page, { "/api/dbms/overview": serve(dbOverview, flag) });
  await page.goto("/dbms", { waitUntil: "domcontentloaded" });
  const panel = statusPanel(page);
  await expect(panel).toContainText("PostgreSQL · up");
  flag.down = true;
  await expectSlow(panel.locator(".notice.error-notice")).toContainText("Service unavailable");
  await expect(panel).toContainText("PostgreSQL · up");
});
