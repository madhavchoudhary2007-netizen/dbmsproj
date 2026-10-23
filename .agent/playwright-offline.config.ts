import { defineConfig } from "../frontend/node_modules/@playwright/test";
export default defineConfig({
  testDir: process.env.TASK_BROWSER_TEST_DIR ?? "../frontend/e2e",
  workers: 1,
  reporter: "line",
  outputDir: "./workspaces/browser-output",
  use: { browserName: "chromium", headless: true },
});
