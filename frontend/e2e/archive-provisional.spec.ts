import { expect, test, type Page } from "@playwright/test";

const raceId = "historical-dbms-race";
const admin = {
  id: "dbms-admin-fixture",
  email: "admin@apexgrid.test",
  full_name: "DBMS Admin",
  role: "ADMIN",
};

async function mockArchive(page: Page, affected: boolean) {
  await page.route("**/api/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path === "/api/auth/me") {
      await route.fulfill({ status: 200, json: admin });
    } else if (path === "/api/dbms/overview") {
      await route.fulfill({ status: 200, json: {} });
    } else if (path === "/api/dbms/races") {
      await route.fulfill({
        status: 200,
        json: [{ id: raceId, state: "COMPLETED", total_laps: 20, event_name: "Historical Grand Prix" }],
      });
    } else if (path === `/api/dbms/races/${raceId}`) {
      await route.fulfill({
        status: 200,
        json: {
          session: { id: raceId, state: "COMPLETED", total_laps: 20 },
          results: [{ position: 1, driver_name: "Fixture Driver", lap_time_ms: 85000, provisional: affected }],
          penalties: affected ? [{ id: "historical-penalty", time_seconds: 5, grid_places: 0 }] : [],
          incidents: [],
          pit_reservations: [],
          drivers: [],
          latest: [],
          telemetry_count: 0,
          completed_driver_laps: 0,
          updated_at: "2026-10-22T00:00:00Z",
          lap_source: "recorded_telemetry",
        },
      });
    } else {
      await route.fulfill({ status: 200, json: [] });
    }
  });
}

async function openRaceArchive(page: Page, affected: boolean) {
  await mockArchive(page, affected);
  await page.goto("/dbms");
  await page.getByRole("button", { name: "Race records", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Live records & race archive" })).toBeVisible();
}

test("F-DOM-02 historical sanctions mark the archive classification provisional", async ({ page }) => {
  test.fail(!process.env.RUN_XFAIL);
  await openRaceArchive(page, true);
  await expect(page.getByText(/provisional classification|classification is provisional|provisional results/i)).toBeVisible();
  await expect(page.getByText(/historical time and grid penalties are recorded but not applied/i)).toBeVisible();
  await expect(page.getByText(/review .*penalties.* before treating .*classification.* as final/i)).toBeVisible();
});

test("unaffected completed archive keeps its ordinary classification presentation", async ({ page }) => {
  await openRaceArchive(page, false);
  await expect(page.getByRole("heading", { name: "Final classification" })).toBeVisible();
  await expect(page.getByText(/provisional classification|classification is provisional|provisional results/i)).toHaveCount(0);
  await expect(page.getByText(/penalties are recorded but not applied|review .*penalties.* before treating/i)).toHaveCount(0);
});
