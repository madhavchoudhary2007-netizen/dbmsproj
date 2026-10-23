import { expect, test } from "@playwright/test";

const routes = [
  ["E2E-R01", "/"],
  ["E2E-R02", "/login"],
  ["E2E-R03", "/dashboard"],
  ["E2E-R04", "/live"],
  ["E2E-R05", "/sessions"],
  ["E2E-R06", "/stewards"],
  ["E2E-R07", "/pit-wall"],
  ["E2E-R08", "/championships"],
  ["E2E-R09", "/events"],
  ["E2E-R10", "/circuits"],
  ["E2E-R11", "/standings"],
  ["E2E-R12", "/teams"],
  ["E2E-R13", "/drivers"],
  ["E2E-R14", "/users"],
  ["E2E-R15", "/analytics"],
  ["E2E-R16", "/dbms"],
] as const;

for (const [id, route] of routes) {
  test(`${id} loads ${route} or its login redirect`, async ({ page }) => {
    const failures: string[] = [];
    page.on("pageerror", (error) => failures.push(`pageerror: ${error.message}`));
    page.on("console", (msg) => {
      if (msg.type() === "error") failures.push(`console: ${msg.text()}`);
    });
    page.on("response", (response) => {
      if (response.status() >= 500) failures.push(`${response.status()} ${response.url()}`);
    });
    await page.route("**/api/**", async (routeRequest) => {
      const pathname = new URL(routeRequest.request().url()).pathname;
      if (pathname === "/api/auth/me" && route === "/login") {
        await routeRequest.fulfill({ status: 401, json: { detail: "Authentication required" } });
        return;
      }
      const body = pathname === "/api/auth/me"
        ? { id: 999, email: "smoke@example.test", full_name: "Smoke Audit", role: "admin" }
        : {};
      await routeRequest.fulfill({ json: body });
    });

    const response = await page.goto(route, { waitUntil: "domcontentloaded" });
    if (response && response.status() >= 500) {
      failures.push(`${response.status()} ${response.url()}`);
    }
    await expect(page).toHaveURL((url) => {
      const pathname = new URL(url).pathname;
      return pathname === route || pathname === "/login";
    });
    await expect.poll(() => page.locator("body").innerText()).toMatch(/\S/);
    expect(failures).toEqual([]);
  });
}
