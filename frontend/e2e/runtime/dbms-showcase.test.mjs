import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import * as vm from "node:vm";

const require = createRequire(import.meta.url);
const typescript = require("../../node_modules/typescript");
const source = readFileSync(new URL("../../lib/dbms-showcase.ts", import.meta.url), "utf8");

async function loadShowcaseModule() {
  const requests = [];
  const realm = vm.createContext({ Promise, URLSearchParams, String });
  const output = typescript.transpileModule(source, {
    compilerOptions: { module: typescript.ModuleKind.ESNext, target: typescript.ScriptTarget.ES2022 },
  }).outputText;

  const react = new vm.SyntheticModule(["useCallback", "useEffect", "useState"], function () {
    for (const name of ["useCallback", "useEffect", "useState"]) {
      this.setExport(name, () => {});
    }
  }, { context: realm, identifier: "react" });

  const mockedApi = new vm.SyntheticModule(["api"], function () {
    this.setExport("api", async (path, options = {}) => {
      requests.push({ path, options });
      return { ok: true, path, options };
    });
  }, { context: realm, identifier: "@/lib/api" });

  const sourceModule = new vm.SourceTextModule(output, { context: realm, identifier: "./dbms-showcase.ts" });
  await sourceModule.link(specifier => {
    if (specifier === "react") return react;
    if (specifier === "@/lib/api" || specifier === "./api") return mockedApi;
    throw new Error(`Unexpected import: ${specifier}`);
  });
  await sourceModule.evaluate();

  return { namespace: sourceModule.namespace, requests };
}

test("fetchIsolationDemo asserts correct query strings and GET method", async () => {
  const { namespace, requests } = await loadShowcaseModule();

  await namespace.fetchIsolationDemo();
  assert.equal(requests[0].path, "/dbms/isolation-demo?level=read_committed");
  assert.equal(requests[0].options.method ?? "GET", "GET");

  await namespace.fetchIsolationDemo("repeatable_read");
  assert.equal(requests[1].path, "/dbms/isolation-demo?level=repeatable_read");
  assert.equal(requests[1].options.method ?? "GET", "GET");

  await namespace.fetchIsolationDemo("serializable");
  assert.equal(requests[2].path, "/dbms/isolation-demo?level=serializable");
  assert.equal(requests[2].options.method ?? "GET", "GET");
});

test("triggerDeadlockDemo asserts path /dbms/deadlock-demo and method POST", async () => {
  const { namespace, requests } = await loadShowcaseModule();

  await namespace.triggerDeadlockDemo();
  assert.equal(requests.length, 1);
  assert.equal(requests[0].path, "/dbms/deadlock-demo");
  assert.equal(requests[0].options.method, "POST");
});

test("fetchViews asserts path /dbms/views and method GET", async () => {
  const { namespace, requests } = await loadShowcaseModule();

  await namespace.fetchViews();
  assert.equal(requests.length, 1);
  assert.equal(requests[0].path, "/dbms/views");
  assert.equal(requests[0].options.method ?? "GET", "GET");
});

test("triggerRefreshStandingsMV asserts path /dbms/refresh-standings-mv and method POST", async () => {
  const { namespace, requests } = await loadShowcaseModule();

  await namespace.triggerRefreshStandingsMV();
  assert.equal(requests.length, 1);
  assert.equal(requests[0].path, "/dbms/refresh-standings-mv");
  assert.equal(requests[0].options.method, "POST");
});

test("fetchAnalyticsGaps asserts path /analytics/gaps?session_id=... and method GET", async () => {
  const { namespace, requests } = await loadShowcaseModule();
  const sessionId = "a1b2c3d4-0000-4000-8000-000000000001";

  await namespace.fetchAnalyticsGaps(sessionId);
  assert.equal(requests.length, 1);
  assert.equal(requests[0].path, `/analytics/gaps?session_id=${sessionId}`);
  assert.equal(requests[0].options.method ?? "GET", "GET");
});

test("fetchExplainPlan asserts path /dbms/explain?analyze=true&query_name=... and method GET", async () => {
  const { namespace, requests } = await loadShowcaseModule();

  await namespace.fetchExplainPlan("standings_rollup", true);
  assert.equal(requests[0].path, "/dbms/explain?analyze=true&query_name=standings_rollup");
  assert.equal(requests[0].options.method ?? "GET", "GET");

  await namespace.fetchExplainPlan(undefined, true);
  assert.equal(requests[1].path, "/dbms/explain?analyze=true");
  assert.equal(requests[1].options.method ?? "GET", "GET");

  await namespace.fetchExplainPlan("lap_telemetry_window", false);
  assert.equal(requests[2].path, "/dbms/explain?analyze=false&query_name=lap_telemetry_window");
  assert.equal(requests[2].options.method ?? "GET", "GET");
});

test("fetchAuditLog asserts path /dbms/audit?table=...&limit=... and method GET", async () => {
  const { namespace, requests } = await loadShowcaseModule();

  await namespace.fetchAuditLog();
  assert.equal(requests[0].path, "/dbms/audit");
  assert.equal(requests[0].options.method ?? "GET", "GET");

  await namespace.fetchAuditLog("penalties", 25);
  assert.equal(requests[1].path, "/dbms/audit?table=penalties&limit=25");
  assert.equal(requests[1].options.method ?? "GET", "GET");

  await namespace.fetchAuditLog("results");
  assert.equal(requests[2].path, "/dbms/audit?table=results");
  assert.equal(requests[2].options.method ?? "GET", "GET");

  await namespace.fetchAuditLog(undefined, 100);
  assert.equal(requests[3].path, "/dbms/audit?limit=100");
  assert.equal(requests[3].options.method ?? "GET", "GET");
});

test("fetchSecurity asserts path /dbms/security and method GET", async () => {
  const { namespace, requests } = await loadShowcaseModule();

  await namespace.fetchSecurity();
  assert.equal(requests.length, 1);
  assert.equal(requests[0].path, "/dbms/security");
  assert.equal(requests[0].options.method ?? "GET", "GET");
});
