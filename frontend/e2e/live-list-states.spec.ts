import { expect, test, type Page } from "./mock-platform";

const races = Array.from({ length: 8 }, (_, index) => ({
  session_id: `race-${index + 1}`,
  event_name: `Generated ${index + 1}`,
  circuit_name: "Test Circuit",
  car_count: 12,
  total_laps: 56,
  state: index === 0 ? "ACTIVE" : "COMPLETED",
  created_at: `2026-10-${String(25 - index).padStart(2, "0")}T00:00:00.000Z`,
}));

async function visit(page: Page, options: {
  role?: "ADMIN" | "READER";
  races?: typeof races;
  gate?: Promise<void>;
  onRaceRequest?: (count: number) => { status?: number; json: unknown };
} = {}) {
  let raceRequests = 0;
  const writes: string[] = [];
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (request.method() !== "GET") {
      writes.push(`${request.method()} ${path}`);
      await route.fulfill({ status: 405, json: { detail: "Unexpected test write" } });
    } else if (path === "/api/auth/me") {
      await route.fulfill({ json: { id: 1, email: "qa@example.test", full_name: "QA", role: options.role ?? "ADMIN" } });
    } else if (path === "/api/demo-races") {
      raceRequests += 1;
      if (options.gate) await options.gate;
      const result = options.onRaceRequest?.(raceRequests) ?? { json: options.races ?? [] };
      await route.fulfill({ status: result.status ?? 200, json: result.json });
    } else if (path === "/api/sessions") {
      await route.fulfill({ json: [] });
    } else if (path === "/api/dashboard") {
      await route.fulfill({ json: { active_sessions: 0, scheduled_events: 0, open_incidents: 0, drivers: 0 } });
    } else {
      await route.fulfill({ json: [] });
    }
  });
  await page.goto("/live");
  return { requests: () => raceRequests, writes };
}

test("generated race list moves from loading to populated", async ({ page }) => {
  let release!: () => void;
  const gated = new Promise<void>((resolve) => { release = resolve; });
  const api = await visit(page, { races: [races[0]], gate: gated });
  await expect(page.getByTestId("state-loading")).toBeVisible();
  release();
  await expect(page.getByTestId("state-populated")).toContainText("Generated 1");
  expect(api.writes).toEqual([]);
});

test("empty list explains that no generated races are available", async ({ page }) => {
  await visit(page);
  await expect(page.getByTestId("state-empty")).toHaveText(/No generated races are available\./);
});

test("retry repeats the failed generated-race GET and populates the list", async ({ page }) => {
  const api = await visit(page, { onRaceRequest: (count) => count === 1
    ? { status: 503, json: { detail: "Initial generated-race failure" } }
    : { json: [races[0]] } });
  await expect(page.getByTestId("state-error")).toContainText("Initial generated-race failure");
  await page.getByRole("button", { name: "Try again" }).click();
  await expect(page.getByTestId("state-populated")).toContainText("Generated 1");
  expect(api.requests()).toBe(2);
  expect(api.writes).toEqual([]);
});

test("recent races can be expanded and restored", async ({ page }) => {
  await visit(page, { races });
  await expect(page.getByTestId("state-partial")).toContainText("Showing 6 of 8 generated races");
  await expect(page.locator(".demo-race-select")).toHaveCount(6);
  await expect(page.getByRole("button", { name: "Show all 8 generated races" })).toHaveCount(1);
  await page.getByRole("button", { name: "Show all 8 generated races" }).click();
  await expect(page.getByTestId("state-populated")).toContainText("Generated 8");
  await expect(page.locator(".demo-race-select")).toHaveCount(8);
  await page.getByRole("button", { name: "Show recent races" }).click();
  await expect(page.getByTestId("state-partial")).toContainText("Showing 6 of 8 generated races");
});

test("a list poll retains races after an error and retry recovers", async ({ page }) => {
  await page.clock.install();
  const api = await visit(page, { races, onRaceRequest: (count) => count === 2
    ? { status: 503, json: { detail: "Poll failure" } }
    : { json: races } });
  await expect(page.getByTestId("state-partial")).toContainText("Showing 6 of 8 generated races");
  await page.clock.fastForward(5000);
  await expect(page.getByTestId("state-partial")).toContainText("Poll failure");
  await page.getByRole("button", { name: "Retry generated races" }).click();
  await expect(page.getByTestId("state-partial")).toContainText("Showing 6 of 8 generated races");
  await expect(page.getByTestId("state-partial")).not.toContainText("Poll failure");
  expect(api.requests()).toBe(3);
  expect(api.writes).toEqual([]);
});

test("reader has Session as the only primary action and cannot create a race", async ({ page }) => {
  await visit(page, { role: "READER" });
  await expect(page.getByRole("button", { name: "Create live race" })).toHaveCount(0);
  await expect(page.locator('[data-primary="true"]')).toHaveCount(1);
  await expect(page.getByLabel("Session")).toHaveAttribute("data-primary", "true");
});
