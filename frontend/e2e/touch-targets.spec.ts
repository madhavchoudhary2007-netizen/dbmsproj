import { expect, test } from "./mock-platform";

const routes = [
  "/login", "/dashboard", "/live", "/sessions", "/stewards", "/pit-wall",
  "/championships", "/events", "/circuits", "/standings", "/teams",
  "/drivers", "/users", "/analytics", "/dbms",
] as const;
const controls = [
  "a[href]",
  "button:not([disabled])",
  "input:not([disabled]):not([type=hidden])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  "[role=button]:not([aria-disabled=true])",
  "[role=link]:not([aria-disabled=true])",
  "[tabindex]:not([tabindex='-1']):not([aria-disabled=true])",
].join(", ");

for (const routePath of routes) {
  test(`G07 touch targets are at least 44×44px at 375px on ${routePath}`, async ({ page }) => {
    const writes: string[] = [];
    await page.setViewportSize({ width: 375, height: 812 });
    await page.route("**/api/**", async (request) => {
      if (request.request().method() !== "GET") {
        writes.push(`${request.request().method()} ${new URL(request.request().url()).pathname}`);
        await request.abort();
        return;
      }
      const pathname = new URL(request.request().url()).pathname;
      if (pathname === "/api/auth/me" && routePath === "/login") {
        await request.fulfill({ status: 401, json: { detail: "Authentication required" } });
        return;
      }
      const body = pathname === "/api/auth/me"
        ? { id: 999, email: "responsive@example.test", full_name: "Responsive Audit", role: "admin" }
        : {};
      await request.fulfill({ json: body });
    });
    await page.goto(routePath, { waitUntil: "domcontentloaded" });
    await expect(page).toHaveURL((url) => new URL(url).pathname === routePath);
    await expect.poll(() => page.locator("body").innerText()).toMatch(/\S/);
    const small = await page.locator(controls).evaluateAll((elements) => elements.flatMap((element) => {
      const style = getComputedStyle(element);
      const rect = element.getBoundingClientRect();
      if (style.display === "none" || style.visibility === "hidden" || rect.width === 0 || rect.height === 0) return [];
      if (element.matches("[data-next-mark], [data-nextjs-dev-tools-button='true']") || element.closest("nextjs-portal")) return [];
      if (element.matches("a[href]") && element.closest("p")) return [];
      if (rect.width >= 44 && rect.height >= 44) return [];
      const inputLabel = element instanceof HTMLInputElement ? element.labels?.[0]?.textContent : "";
      return [{
        label: element.getAttribute("aria-label") || inputLabel?.trim() || element.textContent?.trim().replace(/\s+/g, " ").slice(0, 50) || element.tagName.toLowerCase(),
        html: element.outerHTML.slice(0, 100), width: Math.round(rect.width * 10) / 10,
        height: Math.round(rect.height * 10) / 10,
      }];
    }));
    const undersized = small.map((item) => ({ route: routePath, ...item }));
    expect(writes, "the audit must not submit mutations").toEqual([]);
    expect(
      undersized.length,
      `G07 undersized controls (route, label, HTML, width, height): ${JSON.stringify(undersized)}`,
    ).toBe(0);
  });
}
