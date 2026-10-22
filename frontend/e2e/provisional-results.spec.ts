import { expect, test, type Page } from "@playwright/test";

const steward = {
  id: "steward-fixture",
  email: "steward@apexgrid.test",
  full_name: "Race Steward",
  role: "STEWARD",
};
const session = {
  id: "session-historical-race",
  event_id: "event-historical-gp",
  event_name: "Historical Grand Prix",
  session_type: "Race",
  state: "COMPLETED",
  scheduled_at: "2025-06-15T14:00:00Z",
  total_laps: 20,
};

async function mockData(page: Page, provisional: boolean) {
  await page.route("**/api/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path === "/api/auth/me") {
      await route.fulfill({ status: 200, json: steward });
    } else if (path === "/api/sessions") {
      await route.fulfill({ status: 200, json: [session] });
    } else if (path === "/api/events") {
      await route.fulfill({ status: 200, json: [{ id: session.event_id, name: "Historical Grand Prix" }] });
    } else if (path === "/api/drivers") {
      await route.fulfill({ status: 200, json: [] });
    } else if (path === `/api/sessions/${session.id}/results`) {
      await route.fulfill({
        status: 200,
        json: [{ position: 1, driver_name: "Fixture Driver", provisional }],
      });
    } else if (path === "/api/championships") {
      await route.fulfill({ status: 200, json: [{ id: "champ-2025", name: "2025 Championship", season: 2025 }] });
    } else if (path === "/api/championships/champ-2025/standings") {
      await route.fulfill({
        status: 200,
        json: [{ rank: 1, driver_name: "Fixture Driver", points: 25, provisional }],
      });
    } else {
      await route.fulfill({ status: 200, json: [] });
    }
  });
}

async function expectProvisionalExplanation(page: Page, label: RegExp) {
  await expect(page.getByText(label)).toBeVisible();
  await expect(page.getByText(/historical time and grid penalties are recorded but not applied/i)).toBeVisible();
  await expect(page.getByText(/review .* before treating .* as final/i)).toBeVisible();
}

test("F-DOM-02 completed race results explain historical provisional status", async ({ page }) => {
  test.fail(!process.env.RUN_XFAIL);
  await mockData(page, true);
  await page.goto("/sessions");
  await page.getByRole("row").filter({ hasText: "Historical Grand Prix" }).click();
  await page.getByRole("button", { name: "Load results" }).click();
  await expectProvisionalExplanation(page, /provisional results|results are provisional/i);
});

test("unaffected completed race results keep ordinary presentation", async ({ page }) => {
  await mockData(page, false);
  await page.goto("/sessions");
  await page.getByRole("row").filter({ hasText: "Historical Grand Prix" }).click();
  await page.getByRole("button", { name: "Load results" }).click();
  await expect(page.getByText("OFFICIAL RESULTS")).toBeVisible();
  await expect(page.getByText(/provisional results|results are provisional/i)).toHaveCount(0);
});

test("F-DOM-02 championship standings explain historical provisional status", async ({ page }) => {
  test.fail(!process.env.RUN_XFAIL);
  await mockData(page, true);
  await page.goto("/standings");
  await expectProvisionalExplanation(page, /provisional standings|standings are provisional|provisional classification/i);
});

test("unaffected championship standings keep ordinary presentation", async ({ page }) => {
  await mockData(page, false);
  await page.goto("/standings");
  await expect(page.getByRole("heading", { name: "Standings" })).toBeVisible();
  await expect(page.getByText(/provisional standings|standings are provisional|provisional classification/i)).toHaveCount(0);
});
