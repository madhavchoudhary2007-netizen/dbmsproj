import { expect, test, type Page } from "./mock-platform";

type Championship = { id: number; name: string; season: number };

async function mockApi(
  page: Page,
  championships: (request: import("@playwright/test").Route) => Promise<void>,
) {
  const writes: string[] = [];
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (request.method() !== "GET") {
      writes.push(`${request.method()} ${path}`);
      await route.fulfill({ status: 405, json: { detail: "Unexpected write" } });
      return;
    }
    if (path === "/api/auth/me") {
      await route.fulfill({
        status: 200,
        json: { id: 1, email: "admin@example.test", full_name: "Admin User", role: "ADMIN" },
      });
      return;
    }
    if (path === "/api/championships") {
      await championships(route);
      return;
    }
    await route.fulfill({ status: 200, json: [] });
  });
  return writes;
}

const row = (id: number, name = `Championship ${id}`): Championship => ({ id, name, season: 2026 });

test("resource loading resolves to the API empty state", async ({ page }) => {
  let release!: () => void;
  let requested!: () => void;
  const pending = new Promise<void>((resolve) => { release = resolve; });
  const requestStarted = new Promise<void>((resolve) => { requested = resolve; });
  const writes = await mockApi(page, async (route) => {
    requested();
    await pending;
    await route.fulfill({ status: 200, json: [] });
  });

  await page.goto("/championships");
  await requestStarted;
  await expect(page.getByRole("status")).toContainText("Loading from API…");
  release();
  await expect(page.getByRole("status")).toContainText("No records returned by the API.");
  expect(writes).toEqual([]);
});

test("a failed request shows an error and retry loads the returned row", async ({ page }) => {
  let allowRecovery = false;
  const writes = await mockApi(page, async (route) => {
    if (!allowRecovery) {
      await route.fulfill({ status: 503, json: { detail: "Temporary service failure" } });
    } else {
      await route.fulfill({ status: 200, json: [row(7, "Recovered championship")] });
    }
  });

  await page.goto("/championships");
  await expect(page.getByRole("alert")).toContainText("Temporary service failure");
  await expect(page.getByRole("button", { name: "Try again" })).toBeVisible();
  allowRecovery = true;
  await page.getByRole("button", { name: "Try again" }).click();
  await expect(page.getByRole("cell", { name: "Recovered championship" })).toBeVisible();
  expect(writes).toEqual([]);
});

test("filtering and paging keep the 50 row page boundary", async ({ page }) => {
  const rows = Array.from({ length: 51 }, (_, index) => row(index + 1));
  const writes = await mockApi(page, async (route) => {
    await route.fulfill({ status: 200, json: rows });
  });

  await page.goto("/championships");
  const table = page.locator("main table");
  await expect(table.locator("tbody tr")).toHaveCount(50);
  await expect(page.locator(".resource-range")).toHaveText("Showing 1–50 of 51");
  await page.getByRole("button", { name: "Next" }).click();
  await expect(table.locator("tbody tr")).toHaveCount(1);
  await expect(page.locator(".resource-range")).toHaveText("Showing 51–51 of 51");
  await page.getByRole("button", { name: "Previous" }).click();
  await expect(table.locator("tbody tr")).toHaveCount(50);
  await page.getByLabel("Filter records").fill("Championship 51");
  await expect(table.locator("tbody tr")).toHaveCount(1);
  await expect(page.locator(".resource-range")).toHaveText("Showing 1–1 of 1");
  await page.getByLabel("Filter records").fill("no matching championship");
  await expect(page.getByRole("status")).toContainText("No records match this filter.");
  expect(writes).toEqual([]);
});

test("the create dialog closes on Escape and restores focus without writing", async ({ page }) => {
  const writes = await mockApi(page, async (route) => {
    await route.fulfill({ status: 200, json: [] });
  });

  await page.goto("/championships");
  await expect(page.getByRole("status")).toContainText("No records returned by the API.");
  const create = page.getByRole("button", { name: "New record" });
  await create.click();
  await expect(page.getByRole("dialog", { name: "Create record" })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog", { name: "Create record" })).toHaveCount(0);
  await expect(create).toBeFocused();
  expect(writes).toEqual([]);
});
