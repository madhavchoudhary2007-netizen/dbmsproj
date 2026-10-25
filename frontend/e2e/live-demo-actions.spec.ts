import { expect, test, type Page } from "./mock-platform";

const race = {
  session_id: "s1",
  event_name: "Apex Demo",
  circuit_name: "Test Circuit",
  car_count: 12,
  total_laps: 56,
  state: "ACTIVE",
  created_at: "2026-10-25T00:00:00.000Z",
};
const session = { id: "s1", ...race };

async function setup(page: Page, initiallyPresent = false) {
  let present = initiallyPresent;
  let postCount = 0;
  let deleteCount = 0;
  const posted: unknown[] = [];
  const unexpected: string[] = [];

  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const { pathname } = new URL(request.url());
    if (request.method() === "GET" && pathname === "/api/auth/me") {
      await route.fulfill({ json: { id: 1, email: "qa@example.test", full_name: "QA", role: "ADMIN" } });
    } else if (request.method() === "GET" && pathname === "/api/dashboard") {
      await route.fulfill({ json: { active_sessions: 0, scheduled_events: 0, open_incidents: 0, drivers: 0 } });
    } else if (request.method() === "GET" && pathname === "/api/sessions") {
      await route.fulfill({ json: present ? [session] : [] });
    } else if (request.method() === "GET" && pathname === "/api/demo-races") {
      await route.fulfill({ json: present ? [race] : [] });
    } else if (request.method() === "GET" && pathname === "/api/sessions/s1/live") {
      await route.fulfill({ json: { session, drivers: [], packets: [] } });
    } else if (request.method() === "GET") {
      await route.fulfill({ json: [] });
    } else if (request.method() === "POST" && pathname === "/api/demo-races") {
      postCount += 1;
      const body = request.postDataJSON();
      posted.push(body);
      if (JSON.stringify(body) !== "{}") unexpected.push(`POST ${pathname} body ${JSON.stringify(body)}`);
      present = true;
      await route.fulfill({ status: 201, json: race });
    } else if (request.method() === "DELETE" && pathname === "/api/demo-races/s1") {
      deleteCount += 1;
      present = false;
      await route.fulfill({ status: 204, body: "" });
    } else {
      unexpected.push(`${request.method()} ${pathname}`);
      await route.fulfill({ status: 405, json: { detail: "Unexpected test write" } });
    }
  });

  await page.goto("/live");
  return {
    counts: () => ({ postCount, deleteCount }),
    posted,
    assertClean: () => expect(unexpected).toEqual([]),
  };
}

async function clickSameFrame(page: Page, locator: ReturnType<Page["getByRole"]>) {
  await locator.evaluate((element) => {
    for (let i = 0; i < 20; i += 1) {
      (element as HTMLButtonElement).click();
    }
  });
}

test("creates a generated race and shows its timing option and metadata", async ({ page }, testInfo) => {
  const api = await setup(page);
  const create = page.getByRole("button", { name: "Create live race", exact: true });
  await expect(create).toHaveCount(1);
  await expect(create).toHaveAttribute("data-primary", "true");
  await create.click();

  await expect(page.getByText("Apex Demo", { exact: true })).toBeVisible();
  await expect(page.getByText(/Test Circuit · 12 cars · 56 laps/)).toBeVisible();
  await expect(page.getByRole("option", { name: /Apex Demo/ })).toHaveCount(1);
  await expect(page.locator('.notice[role="status"]')).toContainText("Apex Demo is live with 12 cars.");
  await page.screenshot({ path: `../.agent/results/T383.live.${testInfo.project.name}.raw.png` });
  expect(api.counts().postCount).toBe(1);
  expect(api.posted).toEqual([{}]);
  api.assertClean();
});

test("keeps or confirms deletion through the generated race confirmation", async ({ page }) => {
  const api = await setup(page, true);
  const openDelete = page.getByRole("button", { name: "Delete Apex Demo s1", exact: true });
  await expect(openDelete).toHaveCount(1);
  await openDelete.click();
  await page.getByRole("button", { name: "Keep race", exact: true }).click();
  await expect(page.getByRole("dialog", { name: "Delete generated race?" })).toHaveCount(0);
  await openDelete.click();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog", { name: "Delete generated race?" })).toHaveCount(0);
  expect(api.counts().deleteCount).toBe(0);

  await openDelete.click();
  const confirm = page.getByRole("button", { name: "Delete race", exact: true });
  await expect(confirm).toHaveCount(1);
  await expect(confirm).toHaveAttribute("data-primary", "true");
  await confirm.click();
  await expect(page.getByRole("dialog", { name: "Delete generated race?" })).toHaveCount(0);
  const create = page.getByRole("button", { name: "Create live race", exact: true });
  await expect(create).toHaveCount(1);
  await expect(create).toHaveAttribute("data-primary", "true");
  expect(api.counts().deleteCount).toBe(1);
  api.assertClean();
});

test("same-frame Create clicks issue exactly one POST", async ({ page }) => {
  const api = await setup(page);
  const create = page.getByRole("button", { name: "Create live race", exact: true });
  await expect(create).toHaveCount(1);
  await clickSameFrame(page, create);
  await expect(page.locator('.notice[role="status"]')).toContainText("Apex Demo is live with 12 cars.");
  expect(api.counts().postCount).toBe(1);
  expect(api.posted).toEqual([{}]);
  api.assertClean();
});

test("same-frame confirmation clicks issue exactly one DELETE", async ({ page }) => {
  const api = await setup(page, true);
  await page.getByRole("button", { name: "Delete Apex Demo s1", exact: true }).click();
  const confirm = page.getByRole("button", { name: "Delete race", exact: true });
  await expect(confirm).toHaveCount(1);
  await clickSameFrame(page, confirm);
  await expect(page.getByRole("dialog", { name: "Delete generated race?" })).toHaveCount(0);
  expect(api.counts().deleteCount).toBe(1);
  api.assertClean();
});
