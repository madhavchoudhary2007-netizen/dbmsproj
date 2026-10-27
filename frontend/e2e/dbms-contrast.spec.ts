import { expect, test } from "./mock-platform";

const overview = {
  active_sessions: 1,
  completed_sessions: 12,
  open_incidents: 2,
  reserved_pit_stops: 3,
  completed_pit_stops: 8,
  official_results: 12,
  telemetry_samples: 480,
  postgres: "up",
  mongodb: "up",
  updated_at: "2026-10-27T12:00:00Z",
};

test("populated DBMS overview labels and connection text meet WCAG AA contrast", async ({ page }) => {
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const pathname = new URL(request.url()).pathname;
    if (request.method() !== "GET") {
      await route.abort();
      return;
    }
    if (pathname === "/api/auth/me") {
      await route.fulfill({
        status: 200,
        json: {
          id: "contrast-admin",
          email: "contrast@example.test",
          full_name: "Contrast Fixture",
          role: "ADMIN",
        },
      });
      return;
    }
    if (pathname === "/api/dbms/overview") {
      await route.fulfill({ status: 200, json: overview });
      return;
    }
    await route.fulfill({ status: 200, json: [] });
  });

  await page.goto("/dbms", { waitUntil: "domcontentloaded" });
  const statusPanel = page.locator(".dbms-status-panel");
  await expect(statusPanel).toContainText("PostgreSQL · up");
  await expect(statusPanel).toContainText("MongoDB · up");
  await expect(statusPanel).not.toContainText("Connecting…");
  await expect(statusPanel.locator(".dbms-stat small")).toHaveText([
    "Active sessions",
    "Completed sessions",
    "Open incidents",
    "Reserved pit stops",
    "Completed pit stops",
    "Official results",
    "Mongo samples",
  ]);
  await expect(statusPanel.locator(".dbms-stat strong")).toHaveText([
    "1", "12", "2", "3", "8", "12", "480",
  ]);

  const samples = await statusPanel.evaluate((panel) => {
    const parseColor = (value: string): [number, number, number, number] => {
      const match = value.match(/^rgba?\((.+)\)$/);
      if (!match) throw new Error(`Unsupported computed color: ${value}`);
      const channels = match[1].replace(/\s*\/\s*/, " ").split(/[\s,]+/).map(Number);
      return [channels[0], channels[1], channels[2], channels[3] ?? 1];
    };
    const composite = (
      foreground: [number, number, number, number],
      background: [number, number, number],
    ): [number, number, number] => [
      foreground[0] * foreground[3] + background[0] * (1 - foreground[3]),
      foreground[1] * foreground[3] + background[1] * (1 - foreground[3]),
      foreground[2] * foreground[3] + background[2] * (1 - foreground[3]),
    ];
    const luminance = ([red, green, blue]: [number, number, number]) => {
      const linear = [red, green, blue].map((channel) => {
        const normalized = channel / 255;
        return normalized <= 0.04045
          ? normalized / 12.92
          : ((normalized + 0.055) / 1.055) ** 2.4;
      });
      return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2];
    };

    return Array.from(panel.querySelectorAll(".dbms-stat small, .dbms-connection span"))
      .map((element) => {
        const style = getComputedStyle(element);
        const ancestors: Element[] = [];
        for (let ancestor: Element | null = element; ancestor; ancestor = ancestor.parentElement) {
          ancestors.push(ancestor);
        }
        let background: [number, number, number] = [255, 255, 255];
        for (const ancestor of ancestors.reverse()) {
          background = composite(parseColor(getComputedStyle(ancestor).backgroundColor), background);
        }
        const foreground = composite(parseColor(style.color), background);
        const light = Math.max(luminance(foreground), luminance(background));
        const dark = Math.min(luminance(foreground), luminance(background));
        return {
          label: element.textContent?.trim() || "unlabelled DBMS status text",
          foreground: style.color,
          background: `rgb(${background.map((channel) => Math.round(channel)).join(", ")})`,
          contrast: (light + 0.05) / (dark + 0.05),
        };
      });
  });

  expect(samples).toHaveLength(9);
  for (const sample of samples) {
    expect(
      sample.contrast,
      `${sample.label}: ${sample.foreground} on ${sample.background}`,
    ).toBeGreaterThanOrEqual(4.5);
  }
});
