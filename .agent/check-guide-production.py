"""Root-owned production-only route check on a temporary loopback port."""
import os
import pathlib
import signal
import socket
import subprocess
import time
import urllib.error
import urllib.request

with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
with pathlib.Path(".agent/results/guide-production.server.raw.log").open("w") as log:
    process = subprocess.Popen(["npm", "--prefix", "frontend", "run", "start", "--",
                                "--hostname", "127.0.0.1", "--port", str(port)],
                               stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        for attempt in range(60):
            if process.poll() is not None:
                raise RuntimeError("production preview exited")
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/login", timeout=2).close()
                break
            except urllib.error.URLError:
                time.sleep(0.5)
        else:
            raise RuntimeError("production preview not ready")
        check = r"""
import { chromium, expect } from "@playwright/test";
const browser = await chromium.launch();
try {
 const page = await browser.newPage(); const writes = [];
 await page.route("**/api/**", async route => {
  if (route.request().method() !== "GET") { writes.push(route.request().method()); await route.abort(); return; }
  const body = new URL(route.request().url()).pathname === "/api/auth/me"
   ? {id:"production-audit",email:"audit@example.test",full_name:"Production Audit",role:"ADMIN"} : [];
  await route.fulfill({status:200,contentType:"application/json",body:JSON.stringify(body)});
 });
 const response = await page.goto(process.argv[1] + "/__nb");
 expect([200,404]).toContain(response.status());
 await expect(page.getByText("This page could not be found.", {exact:true})).toBeVisible();
 await expect(page.getByTestId("nb-guide")).toHaveCount(0);
 await expect(page.locator('meta[name="robots"]')).toHaveAttribute("content", /noindex/);
 expect(writes).toEqual([]);
 console.log(`PASS production /__nb status=${response.status()}, not-found visible, noindex, guide absent, zero writes`);
} finally { await browser.close(); }
"""
        subprocess.run(["node", "--input-type=module", "-e", check,
                        f"http://127.0.0.1:{port}"], cwd="frontend", check=True)
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
