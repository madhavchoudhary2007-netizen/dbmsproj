import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import * as vm from "node:vm";

const require = createRequire(import.meta.url);
const typescript = require("../../node_modules/typescript");
const source = readFileSync(new URL("../../lib/use-dashboard-connectivity.ts", import.meta.url), "utf8");

async function load(apiBase) {
  const realm = vm.createContext({ Promise });
  const output = typescript.transpileModule(source, {
    compilerOptions: { module: typescript.ModuleKind.ESNext, target: typescript.ScriptTarget.ES2022 },
  }).outputText;
  const react = new vm.SyntheticModule(["useCallback", "useEffect", "useRef", "useState"], function () {
    for (const name of ["useCallback", "useEffect", "useRef", "useState"]) {
      this.setExport(name, () => { throw new Error(`Unexpected hook call: ${name}`); });
    }
  }, { context: realm, identifier: "react" });
  const api = new vm.SyntheticModule(["API_BASE"], function () {
    this.setExport("API_BASE", apiBase);
  }, { context: realm, identifier: "./api" });
  const sourceModule = new vm.SourceTextModule(output, { context: realm, identifier: "./use-dashboard-connectivity.ts" });
  await sourceModule.link(specifier => {
    if (specifier === "react") return react;
    if (specifier === "./api") return api;
    throw new Error(`Unexpected import: ${specifier}`);
  });
  await sourceModule.evaluate();
  return sourceModule.namespace;
}

test("readRuntimeLease preserves both lease values for ready and not_ready responses", async () => {
  const { readRuntimeLease } = await load("https://api.example.test");
  for (const [status, readiness] of [[200, "ready"], [503, "not_ready"]]) {
    assert.equal(readRuntimeLease(status, { status: readiness, services: { runtime_lease: "up" } }), "up");
    assert.equal(readRuntimeLease(status, { status: readiness, services: { runtime_lease: "down" } }), "down");
  }
});

test("readRuntimeLease rejects malformed response bodies, services, and lease values", async () => {
  const { readRuntimeLease } = await load("https://api.example.test");
  for (const body of [null, [], "ready", { status: "ready" }, { status: "ready", services: null },
    { status: "ready", services: [] }, { status: "ready", services: { runtime_lease: "unknown" } }]) {
    assert.throws(() => readRuntimeLease(200, body), /Invalid readiness response/);
  }
  assert.throws(() => readRuntimeLease(200, { status: "ready", services: { runtime_lease: "missing" } }), /runtime lease status is missing/);
});

test("readRuntimeLease rejects status and readiness combinations outside the contract", async () => {
  const { readRuntimeLease } = await load("https://api.example.test");
  for (const [status, readiness] of [[200, "not_ready"], [503, "ready"], [500, "ready"]]) {
    assert.throws(() => readRuntimeLease(status, { status: readiness, services: { runtime_lease: "up" } }),
      new RegExp(`Readiness request failed \\(${status}\\)`));
  }
});

test("sessionWebSocketUrl maps HTTP schemes and encodes the complete session path", async () => {
  const httpsModule = await load("https://api.example.test/root");
  const httpModule = await load("http://api.example.test/root");
  const sessionId = "team /session?#value";
  const encoded = encodeURIComponent(sessionId);
  assert.equal(httpsModule.sessionWebSocketUrl(sessionId), `wss://api.example.test/root/api/ws/sessions/${encoded}`);
  assert.equal(httpModule.sessionWebSocketUrl(sessionId), `ws://api.example.test/root/api/ws/sessions/${encoded}`);
});
