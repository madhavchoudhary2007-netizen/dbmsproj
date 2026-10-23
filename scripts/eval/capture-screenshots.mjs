import { createRequire } from "module";
import fs from "fs";
import path from "path";
const require = createRequire(import.meta.url);
const { chromium } = require(path.resolve("frontend/node_modules/playwright"));

const prefix = process.argv[2] || "head"; // "before-t204" or "head"
const outDir = path.resolve(".agent/screenshots");
const artifactDir = "/Users/madhavchoudhary/.gemini/antigravity-ide/brain/11e0cda9-a1e9-42cf-b8e5-aa784a9ffbf2/screenshots";

if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });
if (!fs.existsSync(artifactDir)) fs.mkdirSync(artifactDir, { recursive: true });

const adminUser = {
  id: 999,
  email: "smoke@example.test",
  full_name: "Smoke Audit",
  role: "ADMIN",
};

const viewports = [
  { name: "375px", width: 375, height: 812, isMobile: true, hasTouch: true },
  { name: "1440px", width: 1440, height: 900, isMobile: false, hasTouch: false },
];

const routes = [
  { path: "/dashboard", name: "dashboard" },
  { path: "/live", name: "live" },
  { path: "/dbms", name: "dbms" },
];

async function main() {
  const browser = await chromium.launch();

  for (const vp of viewports) {
    const context = await browser.newContext({
      viewport: { width: vp.width, height: vp.height },
      isMobile: vp.isMobile,
      hasTouch: vp.hasTouch,
    });

    await context.route("**/api/**", async (route) => {
      const pathname = new URL(route.request().url()).pathname;
      if (pathname === "/api/auth/me") {
        await route.fulfill({ status: 200, json: adminUser });
        return;
      }
      if (pathname === "/api/dashboard") {
        await route.fulfill({
          status: 200,
          json: { active_sessions: 1, scheduled_events: 2, open_incidents: 0, drivers: 20 },
        });
        return;
      }
      if (pathname === "/api/health") {
        await route.fulfill({
          status: 200,
          json: { status: "HEALTHY", services: { postgres: "UP", redis: "UP" } },
        });
        return;
      }
      if (pathname === "/api/sessions") {
        await route.fulfill({
          status: 200,
          json: [
            { id: "sess-1", name: "Grand Prix", session_type: "RACE", state: "ACTIVE", scheduled_at: "2026-06-01T14:00:00" },
          ],
        });
        return;
      }
      if (pathname === "/api/demo-races") {
        await route.fulfill({ status: 200, json: [] });
        return;
      }
      if (pathname === "/api/drivers") {
        await route.fulfill({
          status: 200,
          json: [{ id: 1, full_name: "Apex Driver 1", number: 44, eligibility: "ACTIVE" }],
        });
        return;
      }
      if (pathname === "/api/dbms/overview") {
        await route.fulfill({
          status: 200,
          json: {
            tables: [
              { name: "sessions", row_count: 10, size_bytes: 4096 },
              { name: "drivers", row_count: 20, size_bytes: 8192 },
            ],
          },
        });
        return;
      }
      await route.fulfill({ status: 200, json: [] });
    });

    const page = await context.newPage();

    for (const r of routes) {
      await page.goto(`http://localhost:3100${r.path}`, { waitUntil: "networkidle" });
      await page.waitForTimeout(1000); // allow animations/charts to settle

      const filename = `${prefix}_${r.name}_${vp.name}.png`;
      const outPath = path.join(outDir, filename);
      const artifactPath = path.join(artifactDir, filename);

      await page.screenshot({ path: outPath, fullPage: false });
      fs.copyFileSync(outPath, artifactPath);
      console.log(`Saved screenshot: ${filename} (${fs.statSync(outPath).size} bytes)`);
    }

    await context.close();
  }

  await browser.close();
}

main().catch((err) => {
  console.error("Screenshot capture failed:", err);
  process.exit(1);
});
