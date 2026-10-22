import { expect, test } from "@playwright/test";

const user = {
  id: "cookie-user",
  email: "operator@apexgrid.test",
  full_name: "Race Operator",
  role: "admin",
};
const apiPattern = "http://localhost:8000/api/**";

test("G11 cookie-only reload authenticates through /auth/me", async ({ page }) => {
  let meCookie: string | undefined;
  let meCalls = 0;
  await page.route(apiPattern, async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (path === "/api/auth/me") {
      meCalls += 1;
      meCookie = request.headers().cookie;
      await route.fulfill({ status: 200, json: user });
      return;
    }
    await route.fulfill({ status: 200, json: [] });
  });
  await page.context().addCookies([{
    name: "apexgrid_session",
    value: "fixture-session-cookie",
    domain: "localhost",
    path: "/",
    httpOnly: true,
    sameSite: "Lax",
  }]);
  await page.addInitScript(() => localStorage.removeItem("apexgrid_token"));

  await page.goto("/dashboard");
  await expect.poll(() => meCalls).toBeGreaterThan(0);
  await expect.poll(() => meCookie ?? "").toContain("apexgrid_session=fixture-session-cookie");
  await expect(page).toHaveURL(/\/dashboard$/);
  expect(await page.evaluate(() => localStorage.getItem("apexgrid_token"))).toBeNull();
});

test("G11 login keeps the session out of localStorage", async ({ page }) => {
  await page.route(apiPattern, async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path === "/api/auth/login") {
      await route.fulfill({ status: 200, json: { user } });
      return;
    }
    if (path === "/api/auth/me") {
      await route.fulfill({ status: 401, json: { detail: "Authentication required" } });
      return;
    }
    await route.fulfill({ status: 200, json: [] });
  });

  await page.goto("/login");
  await page.getByLabel("Email address").fill(user.email);
  await page.getByLabel("Password").fill("fixture-password");
  await page.getByRole("button", { name: "Sign in" }).click();

  await expect(page).toHaveURL(/\/dashboard$/);
  expect(await page.evaluate(() => localStorage.getItem("apexgrid_token"))).toBeNull();
});
