import { expect, test } from "@playwright/test";

const apiPattern = "**/api/**";
const steward = {
  id: "steward-fixture",
  email: "steward@apexgrid.test",
  full_name: "Race Steward",
  role: "STEWARD",
};
const incident = {
  id: "incident-open-1",
  reported_at: "2026-10-22T10:00:00Z",
  session_label: "Grand Prix · Race",
  driver_name: "Fixture Driver",
  lap: 12,
  description: "Unsafe overtake at turn four",
  state: "OPEN",
};

test("F-DOM-02 steward decision dialog disables unenforced sanctions", async ({ page }) => {
  await page.route(apiPattern, async (route) => {
    const pathname = new URL(route.request().url()).pathname;
    if (pathname === "/api/auth/me") {
      await route.fulfill({ status: 200, json: steward });
      return;
    }
    if (pathname === "/api/incidents") {
      await route.fulfill({ status: 200, json: [incident] });
      return;
    }
    if (pathname === "/api/drivers" || pathname === "/api/sessions") {
      await route.fulfill({ status: 200, json: [] });
      return;
    }
    await route.fulfill({ status: 200, json: [] });
  });

  await page.goto("/stewards");
  await page.getByRole("row").filter({ hasText: incident.description }).click();

  const dialog = page.getByRole("dialog", { name: "Incident review" });
  await expect(dialog).toBeVisible();
  await expect(dialog.getByLabel("Time penalty (seconds)")).toBeDisabled();
  await expect(dialog.getByLabel("Grid places")).toBeDisabled();
  await expect(dialog.getByText(
    /official timing\/grid enforcement is unavailable.*use penalty points and notes for now/i,
  )).toBeVisible();
  await expect(dialog.getByLabel("Penalty points")).toBeEnabled();
  await expect(dialog.getByRole("button", { name: "Reject report" })).toBeEnabled();
  await expect(dialog.getByRole("button", { name: "Approve penalty" })).toBeEnabled();
});
