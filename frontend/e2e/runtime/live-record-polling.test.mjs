import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import * as vm from "node:vm";

const require = createRequire(import.meta.url);
const ts = require("../../node_modules/typescript");
const source = readFileSync(new URL("../../lib/live-record-polling.ts", import.meta.url), "utf8");

async function load(session = "race-1") {
  const requests = [], timers = new Map();
  let nextTimer = 1;
  const context = vm.createContext({ Error,
    setTimeout: (callback, delay) => { const id = nextTimer++; timers.set(id, { callback, delay }); return id; },
    clearTimeout: id => timers.delete(id),
  });
  const output = ts.transpileModule(source, { compilerOptions: {
    module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022,
  }}).outputText;
  const api = new vm.SyntheticModule(["api", "asArray"], function () {
    this.setExport("api", path => new Promise((resolve, reject) => requests.push({ path, resolve, reject })));
    this.setExport("asArray", value => Array.isArray(value) ? value : []);
  }, { context });
  const mod = new vm.SourceTextModule(output, { context });
  await mod.link(specifier => { if (specifier === "./api") return api; throw new Error(`Unexpected import: ${specifier}`); });
  await mod.evaluate();
  const calls = { laps: [], incidents: [], pits: [], errors: [], clears: [], loading: [] };
  const retryRef = { current: null };
  const stop = mod.namespace.startLiveRecordPolling(session,
    value => calls.clears.push(value), value => calls.laps.push(value),
    value => calls.incidents.push(value), value => calls.pits.push(value),
    value => calls.errors.push(value), { retryRef, setLoading: value => calls.loading.push(value) });
  return { calls, requests, timers, retryRef, stop };
}

const flush = async () => { await Promise.resolve(); await Promise.resolve(); };
const rows = (laps, incidents = [], pits = []) => ({ laps, incidents, pit_reservations: pits });

test("missing session resets records and settles without a GET", async () => {
  const h = await load("");
  assert.equal(h.stop, undefined);
  assert.deepEqual(h.requests, []);
  assert.equal(h.calls.laps.length, 1); assert.equal(h.calls.laps[0].length, 0);
  assert.equal(h.calls.incidents.length, 1); assert.equal(h.calls.incidents[0].length, 0);
  assert.equal(h.calls.pits.length, 1); assert.equal(h.calls.pits[0].length, 0);
  assert.deepEqual(h.calls.errors, [""]);
  assert.deepEqual(h.calls.loading, [false]);
  assert.deepEqual(h.calls.clears, ["snapshot"]);
});

test("selected session loads actual response rows and starts one five second poll", async () => {
  const h = await load();
  assert.deepEqual(h.requests.map(r => r.path), ["/sessions/race-1/laps"]);
  assert.deepEqual(h.calls.loading, [true]);
  const data = rows([{ id: 1 }], [{ id: 2 }], [{ id: 3 }]);
  h.requests[0].resolve(data);
  await flush();
  assert.equal(h.calls.laps.at(-1), data.laps);
  assert.equal(h.calls.incidents.at(-1), data.incidents);
  assert.equal(h.calls.pits.at(-1), data.pit_reservations);
  assert.deepEqual(h.calls.loading, [true, false]);
  assert.equal(h.timers.size, 1);
  assert.equal([...h.timers.values()][0].delay, 5000);
  h.stop();
});

test("poll failure preserves prior rows and schedules only one next poll", async () => {
  const h = await load();
  const previous = rows([{ id: 1 }], [{ id: 2 }], [{ id: 3 }]);
  h.requests[0].resolve(previous); await flush();
  const before = [h.calls.laps.at(-1), h.calls.incidents.at(-1), h.calls.pits.at(-1)];
  const timer = [...h.timers.values()][0];
  h.timers.clear(); timer.callback(); await flush();
  h.requests[1].reject(new Error("records offline")); await flush();
  assert.deepEqual([h.calls.laps.at(-1), h.calls.incidents.at(-1), h.calls.pits.at(-1)], before);
  assert.deepEqual(h.calls.errors, ["", "", "records offline"]);
  assert.equal(h.timers.size, 1);
  assert.equal([...h.timers.values()][0].delay, 5000);
  h.stop();
});

test("manual retry replaces the pending timer, loads rows, and clears error", async () => {
  const h = await load();
  h.requests[0].reject(new Error("offline")); await flush();
  const priorTimer = [...h.timers.keys()][0];
  h.retryRef.current();
  assert.equal(h.timers.has(priorTimer), false);
  assert.deepEqual(h.calls.loading, [true, false, true]);
  const result = rows([{ id: 4 }]);
  h.requests[1].resolve(result); await flush();
  assert.equal(h.calls.laps.at(-1), result.laps);
  assert.deepEqual(h.calls.errors, ["", "offline", ""]);
  assert.equal(h.timers.size, 1);
  h.stop();
});

test("overlapping retries ignore stale success and failure without extra timers", async () => {
  for (const fail of [false, true]) {
    const h = await load();
    h.retryRef.current();
    const writes = [h.calls.laps.length, h.calls.incidents.length, h.calls.pits.length, h.calls.errors.length];
    if (fail) h.requests[0].reject(new Error("stale")); else h.requests[0].resolve(rows([{ id: 0 }]));
    await flush();
    assert.deepEqual([h.calls.laps.length, h.calls.incidents.length, h.calls.pits.length, h.calls.errors.length], writes);
    assert.equal(h.timers.size, 0);
    h.requests[1].resolve(rows([{ id: 9 }])); await flush();
    assert.equal(h.calls.laps.at(-1)[0].id, 9);
    assert.equal(h.timers.size, 1);
    h.stop();
  }
});

test("cleanup clears its timer and retry ref and ignores a late result", async () => {
  const h = await load();
  h.requests[0].resolve(rows([{ id: 1 }])); await flush();
  const id = [...h.timers.keys()][0];
  const writes = h.calls.laps.length;
  h.stop();
  assert.equal(h.timers.has(id), false);
  assert.equal(h.retryRef.current, null);
  h.timers.clear();
  const late = await load();
  late.stop();
  late.requests[0].resolve(rows([{ id: 2 }])); await flush();
  assert.equal(late.calls.laps.length, 1);
  assert.equal(late.calls.laps[0].length, 0);
  assert.equal(late.timers.size, 0);
  assert.ok(writes > 0);
});

test("older cleanup leaves a newer retry callback assigned to the shared ref", async () => {
  const old = await load();
  const newer = await load();
  const current = newer.retryRef.current;
  old.retryRef.current = current;
  old.stop();
  assert.equal(old.retryRef.current, current);
  newer.stop();
});
