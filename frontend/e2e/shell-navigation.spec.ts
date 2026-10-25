import { expect, test } from "./mock-platform";

const adminUser = {
  id: "fixture-admin",
  email: "fixture@example.test",
  full_name: "Fixture Admin",
  role: "ADMIN",
};

let writes: string[] = [];
async function expectTouchSized(page: import("@playwright/test").Page) {
  const controls = page.locator(".app-shell button:visible, .app-shell a:visible");
  for (let index = 0; index < await controls.count(); index += 1) {
    const box = await controls.nth(index).boundingBox();
    expect(box?.width ?? 0).toBeGreaterThanOrEqual(44);
    expect(box?.height ?? 0).toBeGreaterThanOrEqual(44);
  }
}
test.beforeEach(async ({ page }) => {
  writes = [];
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const pathname = new URL(request.url()).pathname;
    if (request.method() !== "GET") {
      writes.push(`${request.method()} ${pathname}`);
      await route.abort();
      return;
    }
    if (pathname === "/api/auth/me") {
      await route.fulfill({ status: 200, json: adminUser });
      return;
    }
    if (pathname === "/api/dashboard") {
      await route.fulfill({
        status: 200,
        json: {
          active_sessions: 0,
          scheduled_events: 0,
          open_incidents: 0,
          drivers: 0,
          active_session: null,
          next_event: null,
        },
      });
      return;
    }
    if (pathname === "/api/health") {
      await route.fulfill({
        status: 200,
        json: { status: "healthy", services: { postgres: "healthy", mongodb: "healthy" } },
      });
      return;
    }
    await route.fulfill({ status: 200, json: [] });
  });
});
test.afterEach(() => expect(writes).toEqual([]));

test("authenticated shell keeps the drawer usable across viewport changes", async ({ page }) => {
  await page.goto("/dashboard", { waitUntil: "domcontentloaded" });
  await page.evaluate(() => document.fonts.ready);
  const app = page.locator(".app-shell.nb-shell");
  const sidebar = page.locator(".sidebar");
  const background = page.locator(".main-shell");
  await expect(app).toBeVisible();
  await expect(page.getByRole("heading", { name: "Race operations" })).toBeVisible();
  await expect(sidebar).toBeVisible();
  const palette = await sidebar.evaluate((element) => {
    const root = document.querySelector<HTMLElement>(".app-shell")!;
    const resolve = (name: string) => {
      const probe = document.createElement("span");
      probe.style.backgroundColor = `var(${name})`;
      root.append(probe);
      const value = getComputedStyle(probe).backgroundColor;
      probe.remove();
      return value;
    };
    const style = getComputedStyle(element);
    const probe = document.createElement("span");
    probe.style.color = "var(--nb-ink)";
    root.append(probe);
    const ink = getComputedStyle(probe).color;
    probe.remove();
    return { background: style.backgroundColor, cream: resolve("--nb-cream"), color: style.color, ink };
  });
  expect(palette.background).toBe(palette.cream);
  expect(palette.color).toBe(palette.ink);
  const viewport = page.viewportSize()!;
  if (viewport.width >= 1000) {
    const expectedWidth = viewport.width >= 1200 ? 264 : 232;
    await expect.poll(() => sidebar.evaluate((element) => Math.round(element.getBoundingClientRect().width))).toBe(expectedWidth);
    await expectTouchSized(page);
    expect(await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBeLessThanOrEqual(0);
    return;
  }

  await expect(sidebar).toHaveAttribute("aria-hidden", "true");
  expect(await sidebar.evaluate((element) => (element as HTMLElement).inert)).toBe(true);
  const trigger = page.getByRole("button", { name: "Open navigation" });
  await trigger.focus();
  for (let index = 0; index < 20; index += 1) {
    await page.keyboard.press("Tab");
    expect(await page.evaluate(() => Boolean(document.activeElement?.closest(".sidebar")))).toBe(false);
  }
  await trigger.click();
  await expect(sidebar).toHaveClass(/show/);
  await expect(sidebar).toHaveRole("dialog");
  await expect(sidebar).toHaveAttribute("aria-modal", "true");
  expect(await sidebar.evaluate((element) => (element as HTMLElement).inert)).toBe(false);
  expect(await background.evaluate((element) => (element as HTMLElement).inert)).toBe(true);
  expect(await page.evaluate(() => document.body.style.overflow)).toBe("hidden");
  const close = sidebar.getByRole("button", { name: "Close navigation" });
  const signOut = sidebar.getByRole("button", { name: "Sign out" });
  await expect(close).toBeFocused();
  await expectTouchSized(page);
  await close.press("Shift+Tab");
  await expect(signOut).toBeFocused();
  await signOut.press("Tab");
  await expect(close).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(sidebar).not.toHaveClass(/show/);
  await expect(trigger).toBeFocused();
  expect(await background.evaluate((element) => (element as HTMLElement).inert)).toBe(false);
  expect(await page.evaluate(() => document.body.style.overflow)).toBe("");
  await trigger.click();
  await sidebar.getByRole("button", { name: "Close navigation" }).press("Escape");
  await expect(trigger).toBeFocused();
  await trigger.click();
  await page.getByRole("button", { name: "Close navigation" }).last().click();
  await expect(trigger).toBeFocused();
  await trigger.click();
  await page.setViewportSize({ width: 1000, height: viewport.height });
  await expect(sidebar).not.toHaveClass(/show/);
  expect(await sidebar.evaluate((element) => (element as HTMLElement).inert)).toBe(false);
  expect(await background.evaluate((element) => (element as HTMLElement).inert)).toBe(false);
  expect(await page.evaluate(() => document.body.style.overflow)).toBe("");
  await page.setViewportSize(viewport);
  await trigger.click();
  await page.getByRole("link", { name: "Live timing" }).click();
  await expect(page).toHaveURL(/\/live$/);
  await expect(trigger).toBeFocused();
});

test("reduced motion removes the drawer transition", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/dashboard", { waitUntil: "domcontentloaded" });
  await page.evaluate(() => document.fonts.ready);
  await expect(page.locator(".app-shell.nb-shell")).toBeVisible();
  await expect.poll(() => page.locator(".sidebar").evaluate((element) => getComputedStyle(element).transitionProperty)).toBe("none");
});
