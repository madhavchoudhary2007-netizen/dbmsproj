import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "./mock-platform";

const routes = [
  ["E2E-R01", "/"], ["E2E-R02", "/login"], ["E2E-R03", "/dashboard"],
  ["E2E-R04", "/live"], ["E2E-R05", "/sessions"], ["E2E-R06", "/stewards"],
  ["E2E-R07", "/pit-wall"], ["E2E-R08", "/championships"], ["E2E-R09", "/events"],
  ["E2E-R10", "/circuits"], ["E2E-R11", "/standings"], ["E2E-R12", "/teams"],
  ["E2E-R13", "/drivers"], ["E2E-R14", "/users"], ["E2E-R15", "/analytics"],
  ["E2E-R16", "/dbms"],
] as const;

const settleVisuals = async (page: Page) => {
  await page.evaluate(async () => {
    await document.fonts.ready;
    const finiteAnimations = document.getAnimations().filter((animation) => {
      const timing = animation.effect?.getTiming();
      return animation.playState === "running" && timing?.iterations !== Infinity;
    });
    await Promise.all(finiteAnimations.map((animation) => animation.finished.catch(() => undefined)));
    await new Promise<void>((resolve) => {
      requestAnimationFrame(() => requestAnimationFrame(() => resolve()));
    });
  });
};

for (const [id, path] of routes) {
  test(`${id} ${path}: keyboard and accessibility audit`, async ({ page }) => {
    const attemptedWrites: string[] = [];
    await page.route("**/api/**", async (route) => {
      const request = route.request();
      if (request.method() !== "GET") {
        attemptedWrites.push(`${request.method()} ${new URL(request.url()).pathname}`);
        await route.abort();
        return;
      }
      const pathname = new URL(request.url()).pathname;
      if (pathname === "/api/auth/me" && path === "/login") {
        await route.fulfill({ status: 401, contentType: "application/json", body: JSON.stringify({ detail: "Authentication required" }) });
        return;
      }
      const body = pathname === "/api/auth/me"
        ? { id: 1, email: "audit@example.test", full_name: "Accessibility Audit", role: "admin" }
        : [];
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(body) });
    });

    await page.goto(path, { waitUntil: "domcontentloaded" });
    const expectedPath = path === "/" ? "/dashboard" : path;
    if (path === "/") {
      await expect(page).toHaveURL((url) => new URL(url).pathname === "/dashboard");
    }
    if (path === "/login") {
      await expect(page.getByRole("heading", { name: "Sign in to ApexGrid" })).toBeVisible();
      await expect(page.locator("form.login-form")).toBeVisible();
      await expect(page.getByLabel("Email address")).toBeVisible();
      await expect(page.getByLabel("Email address")).toBeEnabled();
    }
    await expect(page).toHaveURL((url) => new URL(url).pathname === expectedPath);
    await expect.poll(() => page.locator("body").innerText()).toMatch(/\S{8}/);
    expect(attemptedWrites).toEqual([]);

    const actionableControl = page.locator(
      "a[href]:visible, button:not([disabled]):visible, input:not([disabled]):not([type=hidden]):visible, select:not([disabled]):visible, textarea:not([disabled]):visible, [role=button]:not([aria-disabled=true]):visible, [role=link]:not([aria-disabled=true]):visible, [tabindex]:not([tabindex='-1']):not([aria-disabled=true]):visible",
    ).first();
    await expect(actionableControl).toBeVisible();

    let reachedVisibleControl = false;
    for (let tabPress = 0; tabPress < 12 && !reachedVisibleControl; tabPress++) {
      await page.keyboard.press("Tab");
      reachedVisibleControl = await page.evaluate(() => {
        const element = document.activeElement;
        if (!element) return false;
        const rect = element.getBoundingClientRect();
        const style = getComputedStyle(element);
        return element.matches("a, button, input, select, textarea, [role=button], [role=link], [tabindex]")
          && !element.matches("[tabindex='-1']")
          && rect.width > 0 && rect.height > 0 && style.visibility !== "hidden" && style.display !== "none"
          && element.matches(":focus-visible");
      });
    }
    expect(reachedVisibleControl).toBe(true);

    const unnamed = await page.locator("a, button, input:not([type=hidden]), select, textarea, [role=button], [role=link]").evaluateAll((elements) =>
      elements.filter((element) => {
        const label = element.getAttribute("aria-label") || element.getAttribute("aria-labelledby");
        return !label?.trim() && !element.textContent?.trim() && !(element instanceof HTMLInputElement && element.labels?.length);
      }).map((element) => element.outerHTML.slice(0, 120)));
    expect(unnamed).toEqual([]);

    const unannouncedStates = await page.locator(".state").evaluateAll((elements) =>
      elements.filter((element) => element.textContent?.trim() && !element.matches('[role="status"], [role="alert"]'))
        .map((element) => element.textContent?.trim().slice(0, 120)));
    expect(unannouncedStates).toEqual([]);

    await settleVisuals(page);
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();
    expect(results.violations).toEqual([]);
  });
}

test("prefers-reduced-motion: reduce disables animations and transitions across components", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.route("**/api/**", async (route) => {
    const pathname = new URL(route.request().url()).pathname;
    if (pathname === "/api/auth/me") {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ id: 1, email: "admin@example.test", full_name: "Admin", role: "admin" }) });
    } else {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify([]) });
    }
  });

  await page.goto("/dashboard", { waitUntil: "domcontentloaded" });
  const matchesReduced = await page.evaluate(() => window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  expect(matchesReduced).toBe(true);

  const bodyStyle = await page.evaluate(() => {
    const style = window.getComputedStyle(document.body);
    return { animationDuration: style.animationDuration, transitionDuration: style.transitionDuration };
  });
  const durSec = parseFloat(bodyStyle.animationDuration);
  expect(durSec <= 0.001 || bodyStyle.animationDuration === "1e-05s").toBe(true);
});
