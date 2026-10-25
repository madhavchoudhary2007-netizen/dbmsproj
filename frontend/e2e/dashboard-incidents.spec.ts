import { expect, test } from "./mock-platform";

const admin = { id: 999, email: "qa@example.test", full_name: "QA", role: "ADMIN" };
const incident = { id: "incident-7", driver_name: "A. Racer", event_name: "Night Grand Prix", lap: 12, state: "OPEN" };
type Reply = { status?: number; json: unknown };

function gate() {
  let release!: (reply: Reply) => void;
  const promise = new Promise<Reply>((resolve) => { release = resolve; });
  return { promise, release };
}

async function mockApi(page: import("@playwright/test").Page, incidents: (count: number) => Promise<Reply>) {
  const calls: Record<string, number> = {};
  const incidentLimits: string[] = [];
  const writes: string[] = [];
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (request.method() !== "GET") {
      writes.push(`${request.method()} ${path}`);
      await route.fulfill({ status: 405, json: { detail: "Unexpected write" } });
      return;
    }
    calls[path] = (calls[path] || 0) + 1;
    let reply: Reply;
    if (path === "/api/auth/me") reply = { json: admin };
    else if (path === "/api/incidents") {
      incidentLimits.push(new URL(request.url()).searchParams.get("limit") ?? "");
      reply = await incidents(calls[path]);
    }
    else reply = { json: [] };
    await route.fulfill({ status: reply.status ?? 200, json: reply.json });
  });
  return { calls, incidentLimits, writes };
}

function incidentsCard(page: import("@playwright/test").Page) {
  return page.getByRole("heading", { name: "Latest incidents" })
    .locator("xpath=ancestor::div[contains(concat(' ',normalize-space(@class),' '),' mt-4 ')][1]");
}

test("shows loading then the empty incidents state", async ({ page }) => {
  const pending = gate();
  const api = await mockApi(page, () => pending.promise);
  await page.goto("/dashboard");
  const card = incidentsCard(page);
  await expect(card.getByTestId("state-loading")).toBeVisible();
  pending.release({ json: [] });
  await expect(card.getByTestId("state-empty")).toContainText("No incidents have been reported.");
  expect(api.writes).toEqual([]);
});

test("renders populated incidents from the source fixture", async ({ page }) => {
  const api = await mockApi(page, async () => ({ json: [incident] }));
  await page.goto("/dashboard");
  const card = incidentsCard(page);
  await expect(card.getByTestId("state-populated")).toBeVisible();
  for (const value of [incident.driver_name, incident.event_name, String(incident.lap), incident.state]) {
    await expect(card.getByRole("cell", { name: value, exact: true })).toBeVisible();
  }
  expect(api.writes).toEqual([]);
});

test("shows source error and recovers on retry", async ({ page }) => {
  let unavailable = true;
  const api = await mockApi(page, async () => unavailable
    ? { status: 503, json: { detail: "Incident source unavailable" } }
    : { json: [incident] });
  await page.goto("/dashboard");
  const card = incidentsCard(page);
  const error = card.getByTestId("state-error");
  await expect(error).toContainText("Incident source unavailable");
  unavailable = false;
  await error.getByRole("button", { name: "Try again" }).click();
  await expect(card.getByTestId("state-populated")).toBeVisible();
  expect(api.writes).toEqual([]);
});

test("keeps the dashboard usable when the incidents response is malformed", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  const api = await mockApi(page, async () => ({ json: {} }));
  await page.goto("/dashboard");
  const card = incidentsCard(page);
  await expect(card.getByTestId("state-error")).toContainText("Invalid latest incidents response");
  await expect(page.getByRole("heading", { name: "Race operations" })).toBeVisible();
  await expect(page.locator(".dashboard-summary")).toBeVisible();
  expect(errors).toEqual([]);
  expect(api.writes).toEqual([]);
});

test("retains incidents after reload failure and retries the source", async ({ page }) => {
  let unavailable = false;
  const api = await mockApi(page, async () => unavailable
    ? { status: 503, json: { detail: "Incident source unavailable" } }
    : { json: [incident] });
  await page.goto("/dashboard");
  const card = incidentsCard(page);
  await expect(card.getByTestId("state-populated")).toBeVisible();
  unavailable = true;
  await card.getByRole("button", { name: "Reload incidents" }).click();
  const partial = card.getByTestId("state-partial");
  await expect(partial).toContainText("Incident source unavailable");
  await expect(partial.getByRole("cell", { name: incident.driver_name })).toBeVisible();
  unavailable = false;
  await partial.getByRole("button", { name: "Retry incidents" }).click();
  await expect(card.getByTestId("state-populated")).toBeVisible();
  expect(api.writes).toEqual([]);
});

test("coalesces same-frame reloads while incidents are pending", async ({ page }) => {
  const pending = gate();
  let defer = false;
  const api = await mockApi(page, () => defer ? pending.promise : Promise.resolve({ json: [incident] }));
  await page.goto("/dashboard");
  const card = incidentsCard(page);
  await expect(card.getByTestId("state-populated")).toBeVisible();
  const baseline = api.calls["/api/incidents"];
  defer = true;
  const reload = card.getByRole("button", { name: "Reload incidents" });
  await reload.click();
  await expect.poll(() => api.calls["/api/incidents"]).toBe(baseline + 1);
  expect(api.incidentLimits.at(-1)).toBe("5");
  await reload.evaluate((button) => {
    for (let i = 0; i < 20; i++) button.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  });
  await expect.poll(() => api.calls["/api/incidents"]).toBe(baseline + 1);
  pending.release({ json: [incident] });
  await expect(card.getByTestId("state-populated")).toBeVisible();
  expect(api.calls["/api/incidents"]).toBe(baseline + 1);
  expect(api.writes).toEqual([]);
});

test("ignores incident completion after navigation while the request is pending", async ({ page }) => {
  const pending = gate();
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  const api = await mockApi(page, () => pending.promise);
  await page.goto("/dashboard");
  await expect(incidentsCard(page).getByTestId("state-loading")).toBeVisible();
  await page.getByRole("link", { name: "Open live timing" }).click();
  await expect(page).toHaveURL(/\/live$/);
  pending.release({ json: [incident] });
  await expect.poll(() => errors.length).toBe(0);
  expect(api.writes).toEqual([]);
});
