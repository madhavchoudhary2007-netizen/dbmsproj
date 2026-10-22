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

test("G11 logout sends session and CSRF cookies, then navigates to login", async ({ page }) => {
  let logoutHeaders: Record<string, string> | undefined;
  await page.route(apiPattern, async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (path === "/api/auth/me") {
      await route.fulfill({ status: 200, json: user });
      return;
    }
    if (path === "/api/auth/logout") {
      logoutHeaders = request.headers();
      await route.fulfill({ status: 200, json: { detail: "Signed out" } });
      return;
    }
    await route.fulfill({ status: 200, json: [] });
  });
  await page.context().addCookies([
    { name: "apexgrid_session", value: "fixture-session-cookie", domain: "localhost", path: "/", httpOnly: true, sameSite: "Lax" },
    { name: "apexgrid_csrf", value: "fixture-csrf-value", domain: "localhost", path: "/", sameSite: "Lax" },
  ]);
  await page.addInitScript(() => localStorage.removeItem("apexgrid_token"));

  await page.goto("/dashboard");
  await page.getByRole("button", { name: "Sign out" }).click();

  await expect(page).toHaveURL(/\/login$/);
  expect(logoutHeaders?.["x-csrf-token"]).toBe("fixture-csrf-value");
  expect(logoutHeaders?.cookie).toContain("apexgrid_session=fixture-session-cookie");
  expect(await page.evaluate(() => localStorage.getItem("apexgrid_token"))).toBeNull();
});

test("G11 failed logout explains retry and a second attempt signs out", async ({ page }) => {
  let logoutCalls = 0;
  let alertMessage = "";
  await page.route(apiPattern, async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path === "/api/auth/me") {
      await route.fulfill({ status: 200, json: user });
      return;
    }
    if (path === "/api/auth/logout") {
      logoutCalls += 1;
      if (logoutCalls === 1) {
        await route.fulfill({ status: 503, json: { detail: "Service temporarily unavailable" } });
      } else {
        await route.fulfill({ status: 200, json: { detail: "Signed out" } });
      }
      return;
    }
    await route.fulfill({ status: 200, json: [] });
  });
  await page.context().addCookies([
    { name: "apexgrid_session", value: "fixture-session-cookie", domain: "localhost", path: "/", httpOnly: true, sameSite: "Lax" },
    { name: "apexgrid_csrf", value: "fixture-csrf-value", domain: "localhost", path: "/", sameSite: "Lax" },
  ]);
  await page.addInitScript(() => localStorage.removeItem("apexgrid_token"));
  page.on("dialog", async (dialog) => {
    alertMessage = dialog.message();
    await dialog.accept();
  });

  await page.goto("/dashboard");
  await page.getByRole("button", { name: "Sign out" }).click();
  await expect.poll(() => alertMessage).toContain("503 Service Unavailable: Service temporarily unavailable");
  expect(alertMessage).toContain("Please try again.");
  await expect(page).toHaveURL(/\/dashboard$/);

  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page).toHaveURL(/\/login$/);
  expect(logoutCalls).toBe(2);
  expect(await page.evaluate(() => localStorage.getItem("apexgrid_token"))).toBeNull();
});
