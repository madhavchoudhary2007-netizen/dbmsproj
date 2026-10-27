import { defineConfig, devices } from "@playwright/test";

const port = process.env.PLAYWRIGHT_PORT ?? "3100";
const isProd = Boolean(process.env.CI || process.env.PLAYWRIGHT_USE_PROD);

export default defineConfig({
  testDir: "./e2e",
  testMatch: "**/*.spec.ts",
  use: { baseURL: `http://localhost:${port}`, trace: "retain-on-failure" },
  webServer: {
    command: isProd
      ? `npm run start -- --hostname 127.0.0.1 --port ${port}`
      : `npm run dev -- --hostname 127.0.0.1 --port ${port}`,
    url: `http://127.0.0.1:${port}`,
    reuseExistingServer: !process.env.CI,
  },
  projects: [
    { name: "mobile-320", use: { viewport: { width: 320, height: 568 }, hasTouch: true, isMobile: true } },
    { name: "mobile-375", use: { ...devices["iPhone 13"], browserName: "chromium", viewport: { width: 375, height: 812 } } },
    { name: "tablet-768", use: { viewport: { width: 768, height: 1024 }, hasTouch: true } },
    { name: "desktop-1440", use: { viewport: { width: 1440, height: 900 } } },
    { name: "ultrawide-32x9", use: { viewport: { width: 5120, height: 1440 } } },
  ],
});
