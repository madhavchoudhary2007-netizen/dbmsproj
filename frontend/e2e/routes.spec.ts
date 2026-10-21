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
    page.on("pageerror", (error) => failures.push(error.message));
    page.on("response", (response) => {
      if (response.status() >= 500) failures.push(`${response.status()} ${response.url()}`);
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
