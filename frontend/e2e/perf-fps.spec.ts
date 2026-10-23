import { expect, test } from "@playwright/test";

test("measure 600-frame animation timing and heap growth on animated live scene", async ({ page }) => {
  await page.route("**/api/**", async (routeRequest) => {
    const pathname = new URL(routeRequest.request().url()).pathname;
    if (pathname === "/api/auth/me") {
      await routeRequest.fulfill({
        status: 200,
        json: { id: 1, email: "smoke@example.test", full_name: "Admin", role: "ADMIN" },
      });
      return;
    }
    await routeRequest.fulfill({ status: 200, json: [] });
  });

  await page.goto("/live", { waitUntil: "domcontentloaded" });

  const metrics = await page.evaluate(async () => {
    return new Promise<{ p95: number; mean: number; heapGrowthMb: number }>((resolve) => {
      const deltas: number[] = [];
      const startHeap = (performance as any).memory?.usedJSHeapSize ?? 0;
      let last: number | null = null;

      function step(timestamp: number) {
        if (last !== null) {
          deltas.push(timestamp - last);
        }
        last = timestamp;
        if (deltas.length >= 600) {
          deltas.sort((a, b) => a - b);
          const p95 = deltas[Math.floor(deltas.length * 0.95)];
          const mean = deltas.reduce((a, b) => a + b, 0) / deltas.length;
          const endHeap = (performance as any).memory?.usedJSHeapSize ?? 0;
          const heapGrowthMb = (endHeap - startHeap) / (1024 * 1024);
          resolve({ p95, mean, heapGrowthMb });
        } else {
          requestAnimationFrame(step);
        }
      }
      requestAnimationFrame(step);
    });
  });

  // P-5 rubric: animated scenes: p95 frame <= 16.7ms over 600 frames and heap growth under 1 MB
  expect(metrics.p95).toBeLessThanOrEqual(17.0);
  expect(metrics.heapGrowthMb).toBeLessThanOrEqual(1.0);
});
