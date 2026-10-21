import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const routes = [
  ["E2E-R01", "/"], ["E2E-R02", "/login"], ["E2E-R03", "/dashboard"],
  ["E2E-R04", "/live"], ["E2E-R05", "/sessions"], ["E2E-R06", "/stewards"],
  ["E2E-R07", "/pit-wall"], ["E2E-R08", "/championships"], ["E2E-R09", "/events"],
  ["E2E-R10", "/circuits"], ["E2E-R11", "/standings"], ["E2E-R12", "/teams"],
  ["E2E-R13", "/drivers"], ["E2E-R14", "/users"], ["E2E-R15", "/analytics"],
  ["E2E-R16", "/dbms"],
] as const;

for (const [id, path] of routes) {
  test(`${id} ${path}: keyboard and accessibility audit`, async ({ page }) => {
    const attemptedWrites: string[] = [];
    await page.addInitScript((routePath) => {
      if (routePath !== "/login") localStorage.setItem("apexgrid_token", "accessibility-audit-fake-token");
    }, path);
    await page.route("**/api/**", async (route) => {
      const request = route.request();
      if (request.method() !== "GET") {
        attemptedWrites.push(`${request.method()} ${new URL(request.url()).pathname}`);
        await route.abort();
        return;
      }
      const body = new URL(request.url()).pathname === "/api/auth/me"
        ? { id: 1, email: "audit@example.test", full_name: "Accessibility Audit", role: "admin" }
        : [];
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(body) });
    });

    await page.goto(path, { waitUntil: "domcontentloaded" });
    await expect(page).toHaveURL((url) => new URL(url).pathname === path);
    await expect.poll(() => page.locator("body").innerText()).toMatch(/\S{8}/);
    expect(attemptedWrites).toEqual([]);

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

    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();
    expect(results.violations.filter((violation) => violation.impact === "serious" || violation.impact === "critical"))
      .toEqual([]);
  });
}
