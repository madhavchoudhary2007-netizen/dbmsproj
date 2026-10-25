import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "./mock-platform";

const memberships = [
  { id: "open", team_id: "team-a", driver_id: "d1", driver_name: "Open Driver", number: 1, licence_number: "L1", start_date: "2020-01-01", end_date: null },
  { id: "future-end", team_id: "team-a", driver_id: "d2", driver_name: "Future End Driver", number: 2, licence_number: "L2", start_date: "2020-01-01", end_date: "2099-01-01" },
  { id: "ended", team_id: "team-a", driver_id: "d3", driver_name: "Ended Driver", number: 3, licence_number: "L3", start_date: "2000-01-01", end_date: "2001-01-01" },
  { id: "future-start", team_id: "team-a", driver_id: "d4", driver_name: "Future Start Driver", number: 4, licence_number: "L4", start_date: "2099-01-01", end_date: null },
];
let writes: string[] = [];

test.beforeEach(async ({ page }) => {
  writes = [];
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (request.method() !== "GET") {
      writes.push(`${request.method()} ${path}`);
      await route.fulfill({ status: 405, json: { detail: "Unexpected write" } });
      return;
    }
    const responses: Record<string, unknown> = {
      "/api/auth/me": { id: 1, email: "admin@example.test", full_name: "Admin", role: "ADMIN" },
      "/api/dashboard": { active_sessions: 0, scheduled_events: 0, open_incidents: 0, drivers: 0 },
      "/api/teams": [{ id: "team-a", name: "Apex Racing", principal_user_id: "p1", principal_name: "Principal" }],
      "/api/drivers": [{ id: "d1", full_name: "Open Driver", number: 1 }],
      "/api/users": [{ id: "p1", full_name: "Principal", role: "PRINCIPAL" }],
    };
    if (path === "/api/teams/team-a/memberships") {
      await route.fulfill({ status: 200, json: memberships });
    } else {
      await route.fulfill({ status: 200, json: responses[path] ?? [] });
    }
  });
});

test.afterEach(() => expect(writes).toEqual([]));

async function openTeam(page: Page) {
  await page.goto("/teams");
  await page.getByRole("row", { name: /Apex Racing/ }).click();
  return page.getByRole("dialog", { name: "Record details" });
}

test("team membership history loads in scope and nested roster supports safe Escape", async ({ page }) => {
  let release!: () => void;
  let requested!: () => void;
  const pending = new Promise<void>((resolve) => { release = resolve; });
  const started = new Promise<void>((resolve) => { requested = resolve; });
  await page.route("**/api/teams/team-a/memberships", async (route) => {
    requested();
    await pending;
    await route.fulfill({ status: 200, json: memberships });
  });
  await page.goto("/teams");
  await page.getByRole("row", { name: /Apex Racing/ }).click();
  const parent = page.getByRole("dialog", { name: "Record details" });
  await started;
  await expect(parent.getByTestId("state-loading")).toBeVisible();
  release();
  await expect(parent.getByText("Open Driver")).toBeVisible();
  await expect(parent.getByText("Future End Driver")).toBeVisible();
  const add = parent.getByRole("button", { name: "Add membership", exact: true });
  await expect(add).toBeVisible();
  await add.click();
  const nested = page.getByRole("dialog", { name: "Create team membership" });
  await expect(nested.getByText("Apex Racing", { exact: true })).toBeVisible();
  const roster = nested.locator("section").filter({ has: nested.getByRole("heading", { name: "Current roster", exact: true }) });
  await expect(roster.getByText("Open Driver", { exact: true })).toBeVisible();
  await expect(roster.getByText("Future End Driver", { exact: true })).toBeVisible();
  await expect(roster.getByText("Ended Driver", { exact: true })).toHaveCount(0);
  await expect(roster.getByText("Future Start Driver", { exact: true })).toHaveCount(0);
  await expect(page.locator('[data-primary="true"]')).toHaveCount(1);
  const initialViewport = await page.evaluate(() => ({ width: innerWidth, height: innerHeight }));
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBe(true);
  for (const [width, columns] of [[760, 1], [1000, 2]]) {
    await page.setViewportSize({ width, height: 800 });
    await expect.poll(() => nested.locator(".grid").evaluate((el) => getComputedStyle(el).gridTemplateColumns.split(" ").length)).toBe(columns);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBe(true);
  }
  await page.setViewportSize(initialViewport);
  const axe = new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]);
  expect((await axe.analyze()).violations).toEqual([]);
  await page.keyboard.press("Escape");
  await expect(nested).toHaveCount(0);
  await expect(parent).toBeVisible();
  await expect(page.locator('[data-primary="true"]')).toHaveCount(1);
  await expect(page.locator('[data-primary="true"]')).toHaveText("Save record");
  await page.keyboard.press("Escape");
  await expect(parent).toHaveCount(0);
  await expect(page.locator('[data-primary="true"]')).toHaveText("New record");
  await expect(page.getByRole("heading", { name: /Teams/ })).toBeVisible();
  expect(writes).toEqual([]);
});

test("membership history retry recovers after a server error", async ({ page }) => {
  let reads = 0;
  await page.route("**/api/teams/team-a/memberships", async (route) => {
    reads++;
    await route.fulfill(reads === 1
      ? { status: 503, json: { detail: "Roster service unavailable" } }
      : { status: 200, json: memberships });
  });
  const dialog = await openTeam(page);
  await expect(dialog.getByTestId("state-error")).toBeVisible();
  await expect(dialog.getByRole("alert")).toContainText("Roster service unavailable");
  await dialog.getByRole("button", { name: "Try again", exact: true }).click();
  await expect(dialog.getByText("Open Driver")).toBeVisible();
  expect(reads).toBe(2);
});

test("adding a membership without a selected record explains the empty roster", async ({ page }) => {
  await page.goto("/teams");
  await page.getByRole("button", { name: "Add membership", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "Create team membership" });
  await expect(dialog.getByText("Select a driver or team record to inspect its roster.")).toBeVisible();
  await expect(dialog.getByRole("heading", { name: "Current roster" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Save record", exact: true })).toHaveCount(1);
  expect(writes).toEqual([]);
});
