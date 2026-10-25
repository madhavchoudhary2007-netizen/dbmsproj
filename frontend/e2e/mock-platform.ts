import { expect, test as base, type Page } from "@playwright/test";

type PlatformFixtures = { mockPlatform: void };

export const test = base.extend<PlatformFixtures>({
  mockPlatform: [async ({ page }, use) => {
    const unexpected: string[] = [];
    await page.route("**/health/ready", async (route) => {
      const request = route.request();
      if (new URL(request.url()).pathname !== "/health/ready") {
        await route.continue();
      } else if (request.method() !== "GET") {
        unexpected.push(`HTTP ${request.method()} ${request.url()}`);
        await route.fulfill({ status: 405, json: { detail: "Unexpected readiness method" } });
      } else {
        await route.fulfill({
          status: 200,
          json: { status: "ready", services: { postgres: "up", mongodb: "up", runtime_lease: "up" } },
        });
      }
    });
    page.routeWebSocket("**/api/ws/sessions/*", (socket) => {
      socket.onMessage(() => {
        unexpected.push("Unexpected session WebSocket message");
        socket.close({ code: 1008, reason: "Unexpected client message" });
      });
    });
    await use();
    expect(unexpected).toEqual([]);
  }, { auto: true }],
});

export { expect };
export type { Page };
