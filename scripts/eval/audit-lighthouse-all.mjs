import pkg from "../../frontend/node_modules/@playwright/test/index.js";
const { chromium } = pkg;
import { spawn, execSync } from "child_process";
import http from "http";
import fs from "fs";

const routes = [
  "/",
  "/login",
  "/dashboard",
  "/live",
  "/sessions",
  "/stewards",
  "/pit-wall",
  "/championships",
  "/events",
  "/circuits",
  "/standings",
  "/teams",
  "/drivers",
  "/users",
  "/analytics",
  "/dbms",
];

function waitForHttp(url, timeoutMs = 30000) {
  return new Promise((resolve, reject) => {
    const start = Date.now();
    function check() {
      http
        .get(url, (res) => {
          if (res.statusCode && res.statusCode < 500) {
            resolve(true);
          } else {
            retry();
          }
        })
        .on("error", retry);
    }
    function retry() {
      if (Date.now() - start > timeoutMs) {
        reject(new Error(`Timeout waiting for ${url}`));
      } else {
        setTimeout(check, 250);
      }
    }
    check();
  });
}

async function main() {
  console.log("Starting backend uvicorn on port 18000...");
  const backend = spawn(
    process.cwd() + "/.venv/bin/python",
    ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "18000"],
    {
      cwd: process.cwd() + "/backend",
      env: {
        ...process.env,
        DATABASE_URL: "postgresql://apexgrid:apexgrid@localhost:15432/apexgrid",
        MONGODB_URL: "mongodb://localhost:27018",
        MONGODB_DATABASE: "apexgrid",
        APP_ENV: "local",
        PYTHONPATH: process.cwd() + "/backend",
        CORS_ORIGINS: "http://localhost:3100,http://127.0.0.1:3100,http://localhost:3000,http://127.0.0.1:3000",
      },
      stdio: "ignore",
    }
  );

  console.log("Starting Next.js production server on port 3100...");
  const frontend = spawn(
    "npm",
    ["run", "start", "--", "--port", "3100", "--hostname", "127.0.0.1"],
    {
      cwd: process.cwd() + "/frontend",
      env: {
        ...process.env,
        NEXT_PUBLIC_API_URL: "http://127.0.0.1:18000",
      },
      stdio: "ignore",
    }
  );

  const cleanup = () => {
    try { backend.kill("SIGKILL"); } catch (_) {}
    try { frontend.kill("SIGKILL"); } catch (_) {}
  };
  process.on("exit", cleanup);
  process.on("SIGINT", cleanup);
  process.on("SIGTERM", cleanup);

  try {
    await waitForHttp("http://127.0.0.1:18000/api/health");
    console.log("Backend healthy on 18000");

    await waitForHttp("http://127.0.0.1:3100/login");
    console.log("Frontend healthy on 3100");

    console.log("Launching Chromium with remote debugging port 9222...");
    const browser = await chromium.launch({
      args: ["--remote-debugging-port=9222"],
      headless: true,
    });
    const page = await browser.newPage();

    console.log("Logging in via /login...");
    await page.goto("http://127.0.0.1:3100/login", { waitUntil: "networkidle" });
    await page.fill("input[type='email']", "admin@apexgrid.test");
    await page.fill("input[type='password']", "ApexGrid2026!");
    await page.click(".login-submit");
    await page.waitForURL("**/dashboard", { timeout: 15000 });
    console.log("Successfully logged in! Session cookie active.");

    const results = [];

    for (const route of routes) {
      const url = `http://127.0.0.1:3100${route}`;
      console.log(`Running Lighthouse on ${route}...`);
      try {
        const out = execSync(
          `npx --yes lighthouse "${url}" --port=9222 --form-factor=mobile --disable-storage-reset --output=json --only-categories=performance --chrome-flags='--headless'`,
          { encoding: "utf-8", timeout: 90000, maxBuffer: 20 * 1024 * 1024 }
        );
        const data = JSON.parse(out);
        const score = Math.round((data.categories?.performance?.score ?? 0) * 100);
        const lcpMs = data.audits?.["largest-contentful-paint"]?.numericValue ?? 0;
        const cls = data.audits?.["cumulative-layout-shift"]?.numericValue ?? 0;
        const tbtMs = data.audits?.["total-blocking-time"]?.numericValue ?? 0;
        const item = {
          route,
          score,
          lcpSec: Number((lcpMs / 1000).toFixed(2)),
          cls: Number(cls.toFixed(3)),
          tbtMs: Math.round(tbtMs),
        };
        console.log(`  -> Score: ${item.score}/100, LCP: ${item.lcpSec}s, CLS: ${item.cls}, TBT: ${item.tbtMs}ms`);
        results.push(item);
      } catch (err) {
        console.error(`  -> Failed on ${route}:`, err.message);
        results.push({
          route,
          error: err.message,
        });
      }
    }

    await browser.close();

    fs.writeFileSync(
      process.cwd() + "/.agent/eval/lighthouse_results.json",
      JSON.stringify(results, null, 2)
    );
    console.log("Wrote .agent/eval/lighthouse_results.json");
  } catch (err) {
    console.error("Fatal error:", err.message);
  } finally {
    cleanup();
  }
}

main();
