import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import * as vm from "node:vm";

const require = createRequire(import.meta.url);
const typescript = require("../../node_modules/typescript");
const source = readFileSync(new URL("../../lib/live-list-refresh.ts", import.meta.url), "utf8");

async function load() {
  const realm = vm.createContext({ Promise, Error });
  const output = typescript.transpileModule(source, {
    compilerOptions: { module: typescript.ModuleKind.ESNext, target: typescript.ScriptTarget.ES2022 },
  }).outputText;
  const requests = [];
  const api = new vm.SyntheticModule(["asArray", "listAll"], function () {
    this.setExport("asArray", value => Array.isArray(value) ? value : []);
    this.setExport("listAll", path => new Promise((resolve, reject) => requests.push({ path, resolve, reject })));
  }, { context: realm, identifier: "@/lib/api" });
  const sourceModule = new vm.SourceTextModule(output, { context: realm, identifier: "./live-list-refresh.ts" });
  await sourceModule.link(specifier => {
    if (specifier === "@/lib/api") return api;
    throw new Error(`Unexpected runtime import: ${specifier}`);
  });
  await sourceModule.evaluate();
  return { refresh: sourceModule.namespace.refreshLiveLists, requests };
}

function fixture(refresh) {
  const request = { current: 0 };
  const calls = { sessions: [], races: [], clears: [], settled: [] };
  const setSessions = rows => calls.sessions.push(rows);
  const setRaces = rows => calls.races.push(rows);
  const clearError = source => calls.clears.push(source);
  const settled = error => calls.settled.push(error);
  return {
    calls, request,
    run: (...args) => args.length && args[0] === undefined
      ? refresh(request, setSessions, setRaces, clearError)
      : refresh(request, setSessions, setRaces, clearError, args[0] || settled),
  };
}

test("current success commits both live lists and reports settlement", async () => {
  const { refresh, requests } = await load();
  const f = fixture(refresh);
  const pending = f.run();
  assert.deepEqual(requests.map(({ path }) => path), ["/sessions", "/demo-races"]);
  const sessions = [{ id: 1 }];
  const races = [{ id: 2 }];
  requests[0].resolve(sessions);
  requests[1].resolve(races);
  const result = await pending;
  assert.equal(result.current, true);
  assert.equal(result.sessionRows, sessions);
  assert.equal(result.raceRows, races);
  assert.equal(f.calls.sessions.length, 1);
  assert.equal(f.calls.sessions[0], sessions);
  assert.equal(f.calls.races.length, 1);
  assert.equal(f.calls.races[0], races);
  assert.deepEqual(f.calls.clears, ["lists"]);
  assert.deepEqual(f.calls.settled, [""]);
});

test("current failure rethrows the same error and reports its message once", async () => {
  const { refresh, requests } = await load();
  const f = fixture(refresh);
  const failure = new Error("sessions unavailable");
  const pending = f.run();
  requests[0].reject(failure);
  requests[1].resolve([]);
  await assert.rejects(pending, error => error === failure);
  assert.deepEqual(f.calls.settled, ["sessions unavailable"]);
  assert.deepEqual(f.calls.sessions, []);
  assert.deepEqual(f.calls.races, []);
  assert.deepEqual(f.calls.clears, []);
});

test("empty Error and non-Error failures use the fallback message", async () => {
  for (const failure of [new Error(""), "offline"]) {
    const { refresh, requests } = await load();
    const f = fixture(refresh);
    const pending = f.run();
    requests[0].reject(failure);
    requests[1].resolve([]);
    await assert.rejects(pending, error => error === failure);
    assert.deepEqual(f.calls.settled, ["Unable to load live sessions"]);
  }
});

test("stale success returns rows without observing or committing them", async () => {
  const { refresh, requests } = await load();
  const f = fixture(refresh);
  const pending = f.run();
  f.request.current += 1;
  const sessions = [{ id: 3 }];
  const races = [{ id: 4 }];
  requests[0].resolve(sessions);
  requests[1].resolve(races);
  const result = await pending;
  assert.equal(result.current, false);
  assert.equal(result.sessionRows, sessions);
  assert.equal(result.raceRows, races);
  assert.deepEqual(f.calls, { sessions: [], races: [], clears: [], settled: [] });
});

test("stale failure rethrows without observing or committing it", async () => {
  const { refresh, requests } = await load();
  const f = fixture(refresh);
  const pending = f.run();
  f.request.current += 1;
  const failure = new Error("superseded request");
  requests[0].reject(failure);
  requests[1].resolve([]);
  await assert.rejects(pending, error => error === failure);
  assert.deepEqual(f.calls, { sessions: [], races: [], clears: [], settled: [] });
});

test("legacy caller without a settlement observer still commits current data", async () => {
  const { refresh, requests } = await load();
  const f = fixture(refresh);
  const pending = f.run(undefined);
  requests[0].resolve([{ id: 5 }]);
  requests[1].resolve([{ id: 6 }]);
  assert.equal((await pending).current, true);
  assert.equal(f.calls.sessions.length, 1);
  assert.equal(f.calls.races.length, 1);
  assert.deepEqual(f.calls.clears, ["lists"]);
  assert.deepEqual(f.calls.settled, []);
});
