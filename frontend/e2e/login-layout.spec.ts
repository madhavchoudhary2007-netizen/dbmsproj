import { expect, test, type Page } from "@playwright/test";

const viewports = [320, 375, 768, 1440, 5120];

async function mockLoginApi(page: Page) {
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const pathname = new URL(request.url()).pathname;
    if (request.method() === "GET" && pathname === "/api/auth/me") {
      await route.fulfill({ status: 401, json: { detail: "Authentication required" } });
      return;
    }
    if (request.method() === "POST" && pathname === "/api/auth/login") {
      await route.fulfill({ status: 404, json: { detail: "Unexpected eager login" } });
      return;
    }
    await route.fulfill({ status: 404, json: { detail: "Fixture not configured" } });
  });
}

async function waitForLogin(page: Page) {
  await expect(page.getByRole("heading", { name: "Sign in to ApexGrid" })).toBeVisible();
  await expect(page.locator("form.login-form")).toBeVisible();
  await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all(
      document.getAnimations()
        .filter((animation) => animation.effect?.getComputedTiming().iterations !== Infinity)
        .map((animation) => animation.finished.catch(() => undefined)),
    );
  });
}

test("login art stays contained across supported viewport widths", async ({ page }) => {
  await mockLoginApi(page);

  for (const width of viewports) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/login", { waitUntil: "domcontentloaded" });
    await waitForLogin(page);

    const art = page.locator(".login-visual");
    const artRect = await art.boundingBox();
    expect(artRect).not.toBeNull();
    if (!artRect) continue;
    const documentOverflow = await page.evaluate(() => ({
      width: document.documentElement.scrollWidth,
      viewport: window.innerWidth,
    }));
    expect(documentOverflow.width).toBeLessThanOrEqual(documentOverflow.viewport + 1);

    if (width < 1000) {
      expect(artRect.height).toBe(240);
      for (const selector of [".nb-login-sticker", ".nb-login-checker", ".nb-login-marquee"]) {
        const item = page.locator(selector);
        const box = await item.boundingBox();
        expect(box).not.toBeNull();
        if (!box) continue;
        expect(box.width).toBeGreaterThan(0);
        expect(box.height).toBeGreaterThan(0);
        expect(box.x).toBeGreaterThanOrEqual(artRect.x - 1);
        expect(box.y).toBeGreaterThanOrEqual(artRect.y - 1);
        expect(box.x + box.width).toBeLessThanOrEqual(artRect.x + artRect.width + 1);
        expect(box.y + box.height).toBeLessThanOrEqual(artRect.y + artRect.height + 1);
      }
      const feedItems = page.locator(".nb-login-marquee li");
      expect(await feedItems.count()).toBe(5);
      for (let index = 0; index < await feedItems.count(); index++) {
        const item = feedItems.nth(index);
        await item.scrollIntoViewIfNeeded();
        const box = await item.boundingBox();
        expect(box).not.toBeNull();
        if (!box) continue;
        expect(box.x).toBeGreaterThanOrEqual(artRect.x - 1);
        expect(box.x + box.width).toBeLessThanOrEqual(artRect.x + artRect.width + 1);
        expect(box.y).toBeGreaterThanOrEqual(artRect.y - 1);
        expect(box.y + box.height).toBeLessThanOrEqual(artRect.y + artRect.height + 1);
      }
    } else {
      expect(artRect.width / width).toBeCloseTo(0.6, 1);
      const formPaper = page.locator(".login-main");
      await expect(formPaper).toBeVisible();
      const paperColor = await formPaper.evaluate((element) => getComputedStyle(element).backgroundColor);
      expect(paperColor).toBe("rgb(255, 255, 255)");
      const inputStyles = await page.locator(".login-form input").evaluateAll((inputs) =>
        inputs.map((input) => {
          const style = getComputedStyle(input);
          return [style.borderWidth, style.backgroundColor, style.color];
        }),
      );
      expect(inputStyles).toEqual([
        ["4px", "rgb(255, 255, 255)", "rgb(0, 0, 0)"],
        ["4px", "rgb(255, 255, 255)", "rgb(0, 0, 0)"],
      ]);
      const checker = await page.locator(".nb-login-checker").boundingBox();
      expect(checker).not.toBeNull();
      if (checker) {
        const panelBorders = await art.evaluate((element) => {
          const style = getComputedStyle(element);
          return parseFloat(style.borderLeftWidth) + parseFloat(style.borderRightWidth);
        });
        expect(checker.width).toBeCloseTo(artRect.width - panelBorders, 1);
      }
    }
  }
});

test("login keeps typed values while the invalid login is busy and errored", async ({ page }) => {
  let releaseLogin: (() => void) | undefined;
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const pathname = new URL(request.url()).pathname;
    if (request.method() === "GET" && pathname === "/api/auth/me") {
      await route.fulfill({ status: 401, json: { detail: "Authentication required" } });
      return;
    }
    if (request.method() === "POST" && pathname === "/api/auth/login") {
      await new Promise<void>((resolve) => { releaseLogin = resolve; });
      await route.fulfill({ status: 401, json: { detail: "Invalid email or password" } });
      return;
    }
    await route.fulfill({ status: 404, json: { detail: "Fixture not configured" } });
  });

  await page.goto("/login", { waitUntil: "domcontentloaded" });
  const email = page.getByPlaceholder("name@team.com");
  const password = page.getByPlaceholder("Enter your password");
  const submit = page.locator(".login-submit");
  await email.fill("driver@apexgrid.test");
  await password.fill("WrongPassword!");
  await expect(submit).toHaveAccessibleName("Sign in");
  await submit.click();

  await expect(email).toBeDisabled();
  await expect(password).toBeDisabled();
  await expect(submit).toBeDisabled();
  await expect(submit).toHaveText(/Authenticating…/);
  await expect(submit).toHaveAttribute("aria-busy", "true");
  await expect.poll(() => Boolean(releaseLogin)).toBe(true);
  releaseLogin?.();

  await expect(email).toBeEnabled();
  await expect(password).toBeEnabled();
  await expect(email).toHaveValue("driver@apexgrid.test");
  await expect(password).toHaveValue("WrongPassword!");
  await expect(page.getByRole("alert")).toHaveText("Invalid email or password");
  await expect(email).toHaveAttribute("aria-describedby", "form-error");
  await expect(password).toHaveAttribute("aria-describedby", "form-error");
  await expect(page.locator("#form-error")).toHaveAttribute("id", "form-error");
});
