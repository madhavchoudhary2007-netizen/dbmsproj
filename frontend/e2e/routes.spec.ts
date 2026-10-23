import { expect, test } from "@playwright/test";

const adminUser = {
  id: 999,
  email: "smoke@example.test",
  full_name: "Smoke Audit",
  role: "ADMIN",
};

interface RouteAcceptance {
  id: string;
  route: string;
  job: string;
  expectedHeading: string;
  expectedText?: string;
}

const deliverables: RouteAcceptance[] = [
  { id: "E2E-R01", route: "/", job: "authenticated landing redirect", expectedHeading: "Race operations" },
  { id: "E2E-R02", route: "/login", job: "sign in and show validation failure", expectedHeading: "Sign in to ApexGrid" },
  { id: "E2E-R03", route: "/dashboard", job: "operational counts and active race", expectedHeading: "Race operations" },
  { id: "E2E-R04", route: "/live", job: "create/select/delete generated race and live timing", expectedHeading: "Live session" },
  { id: "E2E-R05", route: "/sessions", job: "lifecycle, simulator and official results", expectedHeading: "Sessions" },
  { id: "E2E-R06", route: "/stewards", job: "incident review and penalty decision", expectedHeading: "Steward desk" },
  { id: "E2E-R07", route: "/pit-wall", job: "automatic strategy, assignment and stop history", expectedHeading: "Pit Wall" },
  { id: "E2E-R08", route: "/championships", job: "competition CRUD", expectedHeading: "Championships", expectedText: "New record" },
  { id: "E2E-R09", route: "/events", job: "race calendar CRUD", expectedHeading: "Race calendar", expectedText: "New record" },
  { id: "E2E-R10", route: "/circuits", job: "venue CRUD", expectedHeading: "Circuits", expectedText: "New record" },
  { id: "E2E-R11", route: "/standings", job: "persisted ranks and recalculation", expectedHeading: "Standings", expectedText: "Recalculate standings" },
  { id: "E2E-R12", route: "/teams", job: "team CRUD and membership", expectedHeading: "Teams", expectedText: "New record" },
  { id: "E2E-R13", route: "/drivers", job: "driver CRUD and eligibility display", expectedHeading: "Drivers", expectedText: "New record" },
  { id: "E2E-R14", route: "/users", job: "admin user management", expectedHeading: "Users", expectedText: "New record" },
  { id: "E2E-R15", route: "/analytics", job: "paged/filterable driver statistics", expectedHeading: "Driver analytics" },
  { id: "E2E-R16", route: "/dbms", job: "SQL/Mongo views, archive, EER and write demonstrations", expectedHeading: "DBMS workspace", expectedText: "Overview" },
];

for (const { id, route, job, expectedHeading, expectedText } of deliverables) {
  test(`${id} ${route} verifies ${job}`, async ({ page }) => {
    const failures: string[] = [];
    page.on("pageerror", (error) => failures.push(`pageerror: ${error.message}`));
    page.on("console", (msg) => {
      if (msg.type() === "error") {
        const text = msg.text();
        if (route === "/login" && text.includes("401")) return;
        failures.push(`console: ${text}`);
      }
    });
    page.on("response", (response) => {
      if (response.status() >= 500) failures.push(`${response.status()} ${response.url()}`);
    });

    await page.route("**/api/**", async (routeRequest) => {
      const pathname = new URL(routeRequest.request().url()).pathname;
      if (pathname === "/api/auth/me") {
        if (route === "/login") {
          await routeRequest.fulfill({ status: 401, json: { detail: "Authentication required" } });
        } else {
          await routeRequest.fulfill({ status: 200, json: adminUser });
        }
        return;
      }
      if (pathname === "/api/dashboard") {
        await routeRequest.fulfill({
          status: 200,
          json: {
            active_sessions: 2,
            scheduled_events: 5,
            open_incidents: 1,
            drivers: 20,
            active_session: { id: "s-1", name: "Grand Prix", circuit_name: "Silverstone", status: "RUNNING" },
          },
        });
        return;
      }
      if (pathname === "/api/health") {
        await routeRequest.fulfill({
          status: 200,
          json: { status: "healthy", services: { postgres: "healthy", mongodb: "healthy" } },
        });
        return;
      }
      if (pathname === "/api/championships") {
        await routeRequest.fulfill({
          status: 200,
          json: [{ id: 1, name: "Formula Apex 2026", season: 2026 }],
        });
        return;
      }
      if (pathname === "/api/dbms/overview") {
        await routeRequest.fulfill({
          status: 200,
          json: { postgres: { status: "connected" }, mongodb: { status: "connected" } },
        });
        return;
      }
      await routeRequest.fulfill({ status: 200, json: [] });
    });

    const response = await page.goto(route, { waitUntil: "domcontentloaded" });
    if (response && response.status() >= 500) {
      failures.push(`${response.status()} ${response.url()}`);
    }

    await expect(page.getByRole("heading", { name: expectedHeading })).toBeVisible();
    if (expectedText) {
      await expect(page.getByText(expectedText).first()).toBeVisible();
    }
    expect(failures).toEqual([]);
  });
}
