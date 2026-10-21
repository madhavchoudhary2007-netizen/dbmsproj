import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "e2e",
  use: { baseURL: "http://localhost:4173", trace: "retain-on-failure" },
  webServer: { command: "pnpm build && pnpm preview --port 4173", port: 4173, reuseExistingServer: true },
  projects: [
    { name: "mobile-320", use: { viewport: { width: 320, height: 568 }, hasTouch: true, isMobile: true } },
    { name: "mobile-375", use: { ...devices["iPhone 13"], viewport: { width: 375, height: 812 } } },
    { name: "tablet-768", use: { viewport: { width: 768, height: 1024 }, hasTouch: true } },
    { name: "desktop-1440", use: { viewport: { width: 1440, height: 900 } } },
    { name: "ultrawide-32x9", use: { viewport: { width: 5120, height: 1440 } } },
  ],
});
