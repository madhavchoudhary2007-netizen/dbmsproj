import { expect, test, type Page } from "./mock-platform";

type Endpoint = { status: number; json: unknown; gate?: Promise<void> };
type Endpoints = Record<string, Endpoint>;

const adminUser = { id: 999, email: "admin@apexgrid.test", full_name: "Admin User", role: "ADMIN" };
// Pit strategy refreshes on a 5s timer, so its partial state can need more than the default expect window.
const LONG_WAIT = { timeout: 15_000 };

const ok = (json: unknown): Endpoint => ({ status: 200, json });
const fail = (): Endpoint => ({ status: 500, json: { detail: "Service unavailable" } });

// Holds replies until release() is called, so a loading state can be observed before the data arrives.
function hold(endpoint: Endpoint) {
  let release: () => void = () => undefined;
  const gate = new Promise<void>((resolve) => {
    release = () => resolve();
  });
  return { endpoint: { ...endpoint, gate }, release };
}

// Collapses ids in paths so one mutable entry covers every event, session, championship or incident.
function routeKey(method: string, pathname: string): string {
  const path = pathname
    .replace(/^\/api\/sessions\/[^/]+\/pit-strategy$/, "/api/sessions/:id/pit-strategy")
    .replace(/^\/api\/incidents\/[^/]+\/decision$/, "/api/incidents/:id/decision")
    .replace(/^\/api\/championships\/[^/]+\/standings$/, "/api/championships/:id/standings");
  return `${method} ${path}`;
}

// Endpoints are read on every request, so a test can flip one to fail or hold after the page has data.
async function serveApi(page: Page, endpoints: Endpoints): Promise<void> {
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const { pathname } = new URL(request.url());
    if (pathname === "/api/auth/me") return route.fulfill({ status: 200, json: adminUser });
    const endpoint = endpoints[routeKey(request.method(), pathname)] ?? ok([]);
    if (endpoint.gate) await endpoint.gate;
    // A component that aborted the request (refresh or unmount) has no reader left for the reply.
    return route.fulfill({ status: endpoint.status, json: endpoint.json }).catch(() => undefined);
  });
}

/* ---------------------------------------------------------------- /stewards */

const incidentRows = [
  { id: "101", driver_id: "drv-1", driver_name: "Ada Driver", session_id: "sess-1", session_name: "Race", lap: 12, description: "Unsafe release at pit exit", state: "OPEN", reported_at: "2026-10-27T10:00:00Z" },
  { id: "102", driver_id: "drv-2", driver_name: "Ben Driver", session_id: "sess-1", session_name: "Race", lap: 20, description: "Track limits at turn 4", state: "OPEN", reported_at: "2026-10-27T10:20:00Z" },
];
const penaltyRows = [
  { id: "pen-1", incident_id: "101", driver_id: "drv-1", driver_name: "Ada Driver", session_id: "sess-1", lap: 12, points: 5, time_seconds: 10, grid_places: 0, created_at: "2026-10-27T10:05:00Z" },
  { id: "pen-2", incident_id: "102", driver_id: "drv-2", driver_name: "Ben Driver", session_id: "sess-1", lap: 20, points: 3, time_seconds: 0, grid_places: 2, created_at: "2026-10-27T10:30:00Z" },
];
const licenceRows = [
  { driver_id: "drv-1", driver_name: "Ada Driver", licence_number: "LIC-001", eligibility: "ELIGIBLE", season: 2026, points: 5 },
  { driver_id: "drv-2", driver_name: "Ben Driver", licence_number: "LIC-002", eligibility: "ELIGIBLE", season: 2026, points: 3 },
];

function stewardEndpoints(): Endpoints {
  return {
    "GET /api/incidents": ok(incidentRows),
    "GET /api/drivers": ok([{ id: "drv-1", full_name: "Ada Driver" }, { id: "drv-2", full_name: "Ben Driver" }]),
    "GET /api/sessions": ok([{ id: "sess-1", session_type: "RACE" }]),
    "GET /api/stewarding/penalties": ok(penaltyRows),
    "GET /api/stewarding/licences": ok(licenceRows),
    "POST /api/incidents/:id/decision": ok({ driver: { season_points: 5, eligibility: "ELIGIBLE" } }),
  };
}

// Approving a case runs the steward desk's load(), which refreshes incidents, penalties and licences.
async function approveCase(page: Page, caseId: string): Promise<void> {
  await page.getByRole("row", { name: new RegExp(`^Case ${caseId}:`) }).click();
  await page.getByRole("button", { name: "Approve penalty" }).click();
}

test.describe("E-1 states /stewards StewardCases", () => {
  // StewardCases has no landmark of its own; its reserve wrapper is the component root.
  const casesRegion = (page: Page) => page.locator(".steward-cases-reserve");

  test("E-1 StewardCases shows the loading state while incident files load", async ({ page }) => {
    const endpoints = stewardEndpoints();
    const pending = hold(ok(incidentRows));
    endpoints["GET /api/incidents"] = pending.endpoint;
    await serveApi(page, endpoints);
    await page.goto("/stewards", { waitUntil: "domcontentloaded" });
    await expect(casesRegion(page).getByTestId("state-loading")).toBeVisible();
    pending.release();
    await expect(casesRegion(page).getByTestId("state-populated")).toContainText("Unsafe release at pit exit");
  });

  test("E-1 StewardCases shows the empty state when no incidents are returned", async ({ page }) => {
    const endpoints = stewardEndpoints();
    endpoints["GET /api/incidents"] = ok([]);
    await serveApi(page, endpoints);
    await page.goto("/stewards", { waitUntil: "domcontentloaded" });
    await expect(casesRegion(page).getByTestId("state-empty")).toContainText("No records returned by the API.");
  });

  test("E-1 StewardCases renders the populated case table", async ({ page }) => {
    await serveApi(page, stewardEndpoints());
    await page.goto("/stewards", { waitUntil: "domcontentloaded" });
    const populated = casesRegion(page).getByTestId("state-populated");
    await expect(populated).toBeVisible();
    await expect(casesRegion(page).getByRole("table", { name: "Incident case files" })).toContainText("Track limits at turn 4");
  });

  test("E-1 StewardCases shows the error state when incidents fail", async ({ page }) => {
    const endpoints = stewardEndpoints();
    endpoints["GET /api/incidents"] = fail();
    await serveApi(page, endpoints);
    await page.goto("/stewards", { waitUntil: "domcontentloaded" });
    await expect(casesRegion(page).getByTestId("state-error")).toContainText("Service unavailable", LONG_WAIT);
  });

  test("E-1 StewardCases keeps retained cases when the post-decision refresh fails", async ({ page }) => {
    const endpoints = stewardEndpoints();
    await serveApi(page, endpoints);
    await page.goto("/stewards", { waitUntil: "domcontentloaded" });
    await expect(casesRegion(page).getByTestId("state-populated")).toBeVisible();
    endpoints["GET /api/incidents"] = fail();
    await approveCase(page, "101");
    const partial = casesRegion(page).getByTestId("state-partial");
    await expect(partial).toContainText("after a refresh error", LONG_WAIT);
    await expect(casesRegion(page).getByRole("table", { name: "Incident case files" })).toContainText("Track limits at turn 4");
  });
});

test.describe("E-1 states /stewards Penalties and Licences", () => {
  const penaltiesRegion = (page: Page) => page.getByRole("region", { name: "Penalties and sanctions", exact: true });
  const licencesRegion = (page: Page) => page.getByRole("region", { name: "Licence points", exact: true });

  test("E-1 Penalties shows the loading state while penalty history loads", async ({ page }) => {
    const endpoints = stewardEndpoints();
    const pending = hold(ok(penaltyRows));
    endpoints["GET /api/stewarding/penalties"] = pending.endpoint;
    await serveApi(page, endpoints);
    await page.goto("/stewards", { waitUntil: "domcontentloaded" });
    await expect(penaltiesRegion(page).getByTestId("state-loading")).toBeVisible();
    pending.release();
    await expect(penaltiesRegion(page).getByTestId("state-populated")).toContainText("Ada Driver");
  });

  test("E-1 Penalties shows the empty state when no penalties are recorded", async ({ page }) => {
    const endpoints = stewardEndpoints();
    endpoints["GET /api/stewarding/penalties"] = ok([]);
    await serveApi(page, endpoints);
    await page.goto("/stewards", { waitUntil: "domcontentloaded" });
    await expect(penaltiesRegion(page).getByTestId("state-empty")).toContainText("No official penalties or sanctions have been recorded.");
  });

  test("E-1 Penalties renders the populated penalty table", async ({ page }) => {
    await serveApi(page, stewardEndpoints());
    await page.goto("/stewards", { waitUntil: "domcontentloaded" });
    await expect(penaltiesRegion(page).getByTestId("state-populated")).toContainText("Ada Driver");
    await expect(penaltiesRegion(page).getByRole("region", { name: "Official penalty and sanction history" })).toBeVisible();
  });

  test("E-1 Penalties shows the error state when penalties fail", async ({ page }) => {
    const endpoints = stewardEndpoints();
    endpoints["GET /api/stewarding/penalties"] = fail();
    await serveApi(page, endpoints);
    await page.goto("/stewards", { waitUntil: "domcontentloaded" });
    await expect(penaltiesRegion(page).getByTestId("state-error")).toContainText("Service unavailable", LONG_WAIT);
  });

  test("E-1 Penalties keeps retained rows when the post-decision refresh fails", async ({ page }) => {
    const endpoints = stewardEndpoints();
    await serveApi(page, endpoints);
    await page.goto("/stewards", { waitUntil: "domcontentloaded" });
    await expect(penaltiesRegion(page).getByTestId("state-populated")).toBeVisible();
    endpoints["GET /api/stewarding/penalties"] = fail();
    await approveCase(page, "101");
    await expect(penaltiesRegion(page).getByTestId("state-partial")).toContainText("the refresh has failed", LONG_WAIT);
    await expect(penaltiesRegion(page).getByTestId("state-partial")).toContainText("Ada Driver");
  });

  test("E-1 Licences shows the loading state while licence points load", async ({ page }) => {
    const endpoints = stewardEndpoints();
    const pending = hold(ok(licenceRows));
    endpoints["GET /api/stewarding/licences"] = pending.endpoint;
    await serveApi(page, endpoints);
    await page.goto("/stewards", { waitUntil: "domcontentloaded" });
    await expect(licencesRegion(page).getByTestId("state-loading")).toBeVisible();
    pending.release();
    await expect(licencesRegion(page).getByTestId("state-populated")).toContainText("Ada Driver");
  });

  test("E-1 Licences shows the empty state when no licence records are returned", async ({ page }) => {
    const endpoints = stewardEndpoints();
    endpoints["GET /api/stewarding/licences"] = ok([]);
    await serveApi(page, endpoints);
    await page.goto("/stewards", { waitUntil: "domcontentloaded" });
    await expect(licencesRegion(page).getByTestId("state-empty")).toContainText(/No licence records were returned for season \d{4}\./);
  });

  test("E-1 Licences renders populated licence meters", async ({ page }) => {
    await serveApi(page, stewardEndpoints());
    await page.goto("/stewards", { waitUntil: "domcontentloaded" });
    await expect(licencesRegion(page).getByTestId("state-populated")).toContainText("LIC-001");
    await expect(licencesRegion(page).getByRole("meter", { name: "Ada Driver licence points" })).toBeVisible();
  });

  test("E-1 Licences shows the error state when licence points fail", async ({ page }) => {
    const endpoints = stewardEndpoints();
    endpoints["GET /api/stewarding/licences"] = fail();
    await serveApi(page, endpoints);
    await page.goto("/stewards", { waitUntil: "domcontentloaded" });
    await expect(licencesRegion(page).getByTestId("state-error")).toContainText("Service unavailable", LONG_WAIT);
  });

  test("E-1 Licences keeps retained meters when the post-decision refresh fails", async ({ page }) => {
    const endpoints = stewardEndpoints();
    await serveApi(page, endpoints);
    await page.goto("/stewards", { waitUntil: "domcontentloaded" });
    await expect(licencesRegion(page).getByTestId("state-populated")).toBeVisible();
    endpoints["GET /api/stewarding/licences"] = fail();
    await approveCase(page, "101");
    await expect(licencesRegion(page).getByTestId("state-partial")).toContainText("the refresh has failed", LONG_WAIT);
    await expect(licencesRegion(page).getByTestId("state-partial")).toContainText("LIC-001");
  });
});

/* ---------------------------------------------------------------- /pit-wall */

const pitEvents = [
  { id: "evt-1", name: "Silverstone Grand Prix", start_date: "2026-07-05T00:00:00Z" },
  { id: "evt-2", name: "Monza Grand Prix", start_date: "2026-09-06T00:00:00Z" },
];
const pitSessions = [
  { id: "sess-1", event_id: "evt-1", session_type: "RACE", state: "ACTIVE", scheduled_at: "2026-07-05T13:00:00Z", started_at: "2026-07-05T13:00:00Z" },
  { id: "sess-2", event_id: "evt-2", session_type: "RACE", state: "SCHEDULED", scheduled_at: "2026-09-06T13:00:00Z" },
];
const pitTeams = [{ id: "team-1", name: "Apex Racing", principal_user_id: 42 }];
const pitBoxes = [
  { id: "box-1", number: 1, team_name: "Apex Racing", status: "AVAILABLE", starts_at: "2026-09-06T12:00:00Z", ends_at: "2026-09-06T14:00:00Z" },
  { id: "box-2", number: 2, team_name: "Blue Line", status: "RESERVED", starts_at: "2026-09-06T12:00:00Z", ends_at: "2026-09-06T14:00:00Z" },
];
const pitReservations = [
  { id: "res-1", team_id: "team-1", driver_name: "Ada Driver", team_name: "Apex Racing", box_number: 1, allocation_source: "AUTOMATIC", status: "RESERVED", starts_at: "2026-09-06T12:00:00Z", ends_at: "2026-09-06T14:00:00Z" },
  { id: "res-2", team_id: "team-2", driver_name: "Ben Driver", team_name: "Blue Line", box_number: 2, allocation_source: "AUTOMATIC", status: "RESERVED", starts_at: "2026-09-06T12:00:00Z", ends_at: "2026-09-06T14:00:00Z" },
];
const pitStrategy = {
  strategy: [
    {
      driver_id: "drv-1", driver_name: "Ada Driver", team_name: "Apex Racing", driver_number: 7, status: "PENDING",
      current_lap: 12, tire_compound: "SOFT", tire_age_laps: 8, tire_wear_pct: 41, recommended_stop_lap: 15,
      pit_window_start_lap: 14, pit_window_end_lap: 18, laps_until_decision: 3,
      reason: "Tire wear projects a stop inside the pit window.", assigned_box: null, stops: [],
    },
  ],
  historical_summary: { total_stops: 0, by_driver: [] },
};

function pitEndpoints(): Endpoints {
  return {
    "GET /api/events": ok(pitEvents),
    "GET /api/sessions": ok(pitSessions),
    "GET /api/teams": ok(pitTeams),
    "GET /api/pit-boxes": ok(pitBoxes),
    "GET /api/pit-reservations": ok(pitReservations),
    "GET /api/sessions/:id/pit-strategy": ok(pitStrategy),
  };
}

// Event and session are chosen through the page's own selects; the session list only shows the chosen event's sessions.
async function selectEventAndSession(page: Page): Promise<void> {
  await page.getByLabel("Event", { exact: true }).selectOption("evt-2");
  const session = page.getByLabel("Session", { exact: true });
  await expect(session.locator('option[value="sess-2"]')).toHaveCount(1);
  await session.selectOption("sess-2");
}

test.describe("E-1 states /pit-wall PitStrategy", () => {
  const strategyRegion = (page: Page) => page.getByRole("region", { name: "Driver pit decisions", exact: true });

  test("E-1 PitStrategy shows the loading state while a selected session loads", async ({ page }) => {
    const endpoints = pitEndpoints();
    await serveApi(page, endpoints);
    await page.goto("/pit-wall", { waitUntil: "domcontentloaded" });
    await expect(strategyRegion(page).getByTestId("state-populated")).toBeVisible();
    const pending = hold(ok(pitStrategy));
    endpoints["GET /api/sessions/:id/pit-strategy"] = pending.endpoint;
    await selectEventAndSession(page);
    await expect(strategyRegion(page).getByTestId("state-loading")).toBeVisible();
    pending.release();
    await expect(strategyRegion(page).getByTestId("state-populated")).toContainText("Ada Driver");
  });

  test("E-1 PitStrategy shows the empty state when the session has no strategy", async ({ page }) => {
    const endpoints = pitEndpoints();
    endpoints["GET /api/sessions/:id/pit-strategy"] = ok({ strategy: [], historical_summary: {} });
    await serveApi(page, endpoints);
    await page.goto("/pit-wall", { waitUntil: "domcontentloaded" });
    await selectEventAndSession(page);
    await expect(strategyRegion(page).getByTestId("state-empty")).toContainText("No driver strategy is available for this session.");
  });

  test("E-1 PitStrategy renders populated driver decisions", async ({ page }) => {
    await serveApi(page, pitEndpoints());
    await page.goto("/pit-wall", { waitUntil: "domcontentloaded" });
    await selectEventAndSession(page);
    await expect(strategyRegion(page).getByTestId("state-populated")).toContainText("Ada Driver");
  });

  test("E-1 PitStrategy shows the error state when strategy fails", async ({ page }) => {
    const endpoints = pitEndpoints();
    endpoints["GET /api/sessions/:id/pit-strategy"] = fail();
    await serveApi(page, endpoints);
    await page.goto("/pit-wall", { waitUntil: "domcontentloaded" });
    await selectEventAndSession(page);
    await expect(strategyRegion(page).getByTestId("state-error")).toContainText("Service unavailable", LONG_WAIT);
  });

  test("E-1 PitStrategy keeps retained decisions when the automatic refresh fails", async ({ page }) => {
    const endpoints = pitEndpoints();
    await serveApi(page, endpoints);
    await page.goto("/pit-wall", { waitUntil: "domcontentloaded" });
    await selectEventAndSession(page);
    await expect(strategyRegion(page).getByTestId("state-populated")).toContainText("Ada Driver");
    // The strategy poll runs every 5s; the next poll after this change is the component's own refresh.
    endpoints["GET /api/sessions/:id/pit-strategy"] = fail();
    const partial = strategyRegion(page).getByTestId("state-partial");
    await expect(partial).toContainText("Showing retained strategy while the refresh failed.", LONG_WAIT);
    await expect(partial).toContainText("Ada Driver");
  });
});

test.describe("E-1 states /pit-wall PitInfrastructure", () => {
  const boxesRegion = (page: Page) => page.getByRole("region", { name: "Selected event infrastructure", exact: true });
  const queueRegion = (page: Page) => page.getByRole("region", { name: "Pit stop queue", exact: true });

  test("E-1 PitInfrastructure shows the loading state for boxes and the queue", async ({ page }) => {
    const endpoints = pitEndpoints();
    await serveApi(page, endpoints);
    await page.goto("/pit-wall", { waitUntil: "domcontentloaded" });
    await expect(boxesRegion(page).getByTestId("state-populated")).toBeVisible();
    const pending = hold(ok(pitBoxes));
    endpoints["GET /api/pit-boxes"] = pending.endpoint;
    await selectEventAndSession(page);
    await expect(boxesRegion(page).getByTestId("state-loading")).toBeVisible();
    await expect(queueRegion(page).getByTestId("state-loading")).toBeVisible();
    pending.release();
    await expect(boxesRegion(page).getByTestId("state-populated")).toContainText("Apex Racing");
  });

  test("E-1 PitInfrastructure shows the empty state when the event has no boxes or stops", async ({ page }) => {
    const endpoints = pitEndpoints();
    endpoints["GET /api/pit-boxes"] = ok([]);
    endpoints["GET /api/pit-reservations"] = ok([]);
    await serveApi(page, endpoints);
    await page.goto("/pit-wall", { waitUntil: "domcontentloaded" });
    await selectEventAndSession(page);
    await expect(boxesRegion(page).getByTestId("state-empty")).toContainText("No records returned by the API.");
    await expect(queueRegion(page).getByTestId("state-empty")).toContainText("No records returned by the API.");
  });

  test("E-1 PitInfrastructure renders populated boxes and queue entries", async ({ page }) => {
    await serveApi(page, pitEndpoints());
    await page.goto("/pit-wall", { waitUntil: "domcontentloaded" });
    await selectEventAndSession(page);
    await expect(boxesRegion(page).getByTestId("state-populated")).toContainText("Blue Line");
    await expect(queueRegion(page).getByTestId("state-populated")).toContainText("Ada Driver");
  });

  test("E-1 PitInfrastructure shows the error state when boxes fail", async ({ page }) => {
    const endpoints = pitEndpoints();
    endpoints["GET /api/pit-boxes"] = fail();
    await serveApi(page, endpoints);
    await page.goto("/pit-wall", { waitUntil: "domcontentloaded" });
    await selectEventAndSession(page);
    await expect(boxesRegion(page).getByTestId("state-error")).toContainText("Service unavailable", LONG_WAIT);
    await expect(queueRegion(page).getByTestId("state-error")).toContainText("Service unavailable", LONG_WAIT);
  });

  test("E-1 PitInfrastructure keeps retained boxes and stops when the page refresh fails", async ({ page }) => {
    const endpoints = pitEndpoints();
    await serveApi(page, endpoints);
    await page.goto("/pit-wall", { waitUntil: "domcontentloaded" });
    await selectEventAndSession(page);
    await expect(boxesRegion(page).getByTestId("state-populated")).toBeVisible();
    endpoints["GET /api/pit-boxes"] = fail();
    await page.getByRole("button", { name: "Refresh", exact: true }).click();
    await expect(boxesRegion(page).getByTestId("state-partial")).toContainText("Showing retained pit boxes", LONG_WAIT);
    await expect(boxesRegion(page).getByTestId("state-partial")).toContainText("Apex Racing");
    await expect(queueRegion(page).getByTestId("state-partial")).toContainText("Showing retained pit stops", LONG_WAIT);
    await expect(queueRegion(page).getByTestId("state-partial")).toContainText("Ada Driver");
  });
});

/* ---------------------------------------------------------------- /dashboard */

const dashboardMetrics = {
  active_sessions: 2,
  scheduled_events: 7,
  open_incidents: 3,
  drivers: 20,
  next_event: { name: "Monza Grand Prix", circuit_name: "Autodromo Nazionale Monza", scheduled_at: "2026-09-06T13:00:00Z" },
};
const dashboardHealth = { status: "ok", services: { postgres: "up", mongodb: "up", runtime_lease: "up" } };
const incidentFeed = [
  { id: "inc-1", driver_name: "Ada Driver", event_name: "Silverstone Grand Prix", lap: 12, state: "OPEN" },
  { id: "inc-2", driver_name: "Ben Driver", event_name: "Silverstone Grand Prix", lap: 20, state: "RESOLVED" },
];

function dashboardEndpoints(): Endpoints {
  return {
    "GET /api/dashboard": ok(dashboardMetrics),
    "GET /api/health": ok(dashboardHealth),
    "GET /api/incidents": ok(incidentFeed),
  };
}

test.describe("E-1 states /dashboard summary grid", () => {
  // NbState applies the summary class to the state element itself, so the testid and the class share one node.
  const summaryState = (page: Page, testId: string) => page.getByTestId(testId).and(page.locator(".dashboard-summary"));

  test("E-1 dashboard summary shows the loading state while metrics load", async ({ page }) => {
    const endpoints = dashboardEndpoints();
    const pending = hold(ok(dashboardMetrics));
    endpoints["GET /api/dashboard"] = pending.endpoint;
    await serveApi(page, endpoints);
    await page.goto("/dashboard", { waitUntil: "domcontentloaded" });
    await expect(summaryState(page, "state-loading")).toBeVisible();
    pending.release();
    await expect(summaryState(page, "state-populated")).toContainText("Monza Grand Prix");
  });

  test("E-1 dashboard summary shows the empty state when the feed has no metrics", async ({ page }) => {
    const endpoints = dashboardEndpoints();
    endpoints["GET /api/dashboard"] = ok({});
    await serveApi(page, endpoints);
    await page.goto("/dashboard", { waitUntil: "domcontentloaded" });
    await expect(summaryState(page, "state-empty")).toContainText("No dashboard data is currently available.");
  });

  test("E-1 dashboard summary renders the populated metric grid", async ({ page }) => {
    await serveApi(page, dashboardEndpoints());
    await page.goto("/dashboard", { waitUntil: "domcontentloaded" });
    await expect(summaryState(page, "state-populated")).toContainText("Monza Grand Prix");
    await expect(summaryState(page, "state-populated").locator("dd")).toHaveCount(4);
  });

  test("E-1 dashboard summary shows the error state when the feed fails", async ({ page }) => {
    const endpoints = dashboardEndpoints();
    endpoints["GET /api/dashboard"] = fail();
    await serveApi(page, endpoints);
    await page.goto("/dashboard", { waitUntil: "domcontentloaded" });
    await expect(summaryState(page, "state-error")).toContainText("Service unavailable", LONG_WAIT);
  });

  test("E-1 dashboard summary keeps retained metrics when the header refresh fails", async ({ page }) => {
    const endpoints = dashboardEndpoints();
    await serveApi(page, endpoints);
    await page.goto("/dashboard", { waitUntil: "domcontentloaded" });
    await expect(summaryState(page, "state-populated")).toBeVisible();
    endpoints["GET /api/dashboard"] = fail();
    await page.locator(".dashboard-hero").getByRole("button", { name: "Refresh", exact: true }).click();
    const partial = summaryState(page, "state-partial");
    await expect(partial).toContainText("Showing 4 dashboard metrics", LONG_WAIT);
    await expect(partial).toContainText("Monza Grand Prix");
  });
});

test.describe("E-1 states /dashboard Latest incidents table", () => {
  const incidentsCard = (page: Page) =>
    page.locator(".dashboard-incidents-card").filter({ has: page.getByRole("heading", { name: "Latest incidents", exact: true }) });

  test("E-1 Latest incidents shows the loading state while incidents load", async ({ page }) => {
    const endpoints = dashboardEndpoints();
    const pending = hold(ok(incidentFeed));
    endpoints["GET /api/incidents"] = pending.endpoint;
    await serveApi(page, endpoints);
    await page.goto("/dashboard", { waitUntil: "domcontentloaded" });
    await expect(incidentsCard(page).getByTestId("state-loading")).toBeVisible();
    pending.release();
    await expect(incidentsCard(page).getByTestId("state-populated")).toContainText("Ada Driver");
  });

  test("E-1 Latest incidents shows the empty state when no incidents exist", async ({ page }) => {
    const endpoints = dashboardEndpoints();
    endpoints["GET /api/incidents"] = ok([]);
    await serveApi(page, endpoints);
    await page.goto("/dashboard", { waitUntil: "domcontentloaded" });
    await expect(incidentsCard(page).getByTestId("state-empty")).toContainText("No incidents have been reported.");
  });

  test("E-1 Latest incidents renders the populated table", async ({ page }) => {
    await serveApi(page, dashboardEndpoints());
    await page.goto("/dashboard", { waitUntil: "domcontentloaded" });
    await expect(incidentsCard(page).getByRole("region", { name: "Latest incidents", exact: true })).toContainText("Ben Driver");
    await expect(incidentsCard(page).getByTestId("state-populated")).toBeVisible();
  });

  test("E-1 Latest incidents shows the error state when incidents fail", async ({ page }) => {
    const endpoints = dashboardEndpoints();
    endpoints["GET /api/incidents"] = fail();
    await serveApi(page, endpoints);
    await page.goto("/dashboard", { waitUntil: "domcontentloaded" });
    await expect(incidentsCard(page).getByTestId("state-error")).toContainText("Service unavailable", LONG_WAIT);
  });

  test("E-1 Latest incidents keeps retained rows when the reload fails", async ({ page }) => {
    const endpoints = dashboardEndpoints();
    await serveApi(page, endpoints);
    await page.goto("/dashboard", { waitUntil: "domcontentloaded" });
    await expect(incidentsCard(page).getByTestId("state-populated")).toBeVisible();
    endpoints["GET /api/incidents"] = fail();
    await incidentsCard(page).getByRole("button", { name: "Reload incidents", exact: true }).click();
    const partial = incidentsCard(page).getByTestId("state-partial");
    await expect(partial).toContainText("Showing previously loaded incidents", LONG_WAIT);
    await expect(incidentsCard(page).getByRole("region", { name: "Latest incidents", exact: true })).toContainText("Ada Driver");
  });
});

/* ---------------------------------------------------------------- /standings */

const championships = [
  { id: "ch-1", name: "World Championship", season: 2026 },
  { id: "ch-2", name: "Cup Series", season: 2025 },
];
const standingRows = [
  { driver_id: "drv-1", rank: 1, driver_name: "Ada Driver", number: 7, team_name: "Apex Racing", points: 120, wins: 3, podiums: 5 },
  { driver_id: "drv-2", rank: 2, driver_name: "Ben Driver", number: 9, team_name: "Blue Line", points: 98, wins: 1, podiums: 4 },
];

function standingsEndpoints(): Endpoints {
  return {
    "GET /api/championships": ok(championships),
    "GET /api/championships/:id/standings": ok(standingRows),
  };
}

test.describe("E-1 states /standings standings table", () => {
  const standingsRegion = (page: Page) => page.getByRole("region", { name: "Full standings", exact: true });

  test("E-1 standings table shows the loading state when another championship is selected", async ({ page }) => {
    const endpoints = standingsEndpoints();
    await serveApi(page, endpoints);
    await page.goto("/standings", { waitUntil: "domcontentloaded" });
    await expect(standingsRegion(page).getByTestId("state-populated")).toBeVisible();
    const pending = hold(ok(standingRows));
    endpoints["GET /api/championships/:id/standings"] = pending.endpoint;
    await page.getByRole("combobox", { name: /Championship/ }).selectOption("ch-2");
    await expect(standingsRegion(page).getByTestId("state-loading")).toBeVisible();
    pending.release();
    await expect(standingsRegion(page).getByTestId("state-populated")).toContainText("Ada Driver");
  });

  test("E-1 standings table shows the empty state when no standings are recorded", async ({ page }) => {
    const endpoints = standingsEndpoints();
    endpoints["GET /api/championships/:id/standings"] = ok([]);
    await serveApi(page, endpoints);
    await page.goto("/standings", { waitUntil: "domcontentloaded" });
    await expect(standingsRegion(page).getByTestId("state-empty")).toContainText("No standings have been recorded for this championship.");
  });

  test("E-1 standings table renders populated classification rows", async ({ page }) => {
    await serveApi(page, standingsEndpoints());
    await page.goto("/standings", { waitUntil: "domcontentloaded" });
    await expect(standingsRegion(page).getByTestId("state-populated")).toContainText("Ben Driver");
    await expect(standingsRegion(page).getByRole("region", { name: "Championship standings", exact: true })).toBeVisible();
  });

  test("E-1 standings table shows the error state when standings fail", async ({ page }) => {
    const endpoints = standingsEndpoints();
    endpoints["GET /api/championships/:id/standings"] = fail();
    await serveApi(page, endpoints);
    await page.goto("/standings", { waitUntil: "domcontentloaded" });
    await expect(standingsRegion(page).getByTestId("state-error")).toContainText("Service unavailable", LONG_WAIT);
  });
});
