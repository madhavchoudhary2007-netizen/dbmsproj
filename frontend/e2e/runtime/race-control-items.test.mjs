import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import * as vm from "node:vm";

const require = createRequire(import.meta.url);
const typescript = require("../../node_modules/typescript");
const source = readFileSync(new URL("../../lib/race-control-items.ts", import.meta.url), "utf8");

function loadMapper() {
  const output = typescript.transpileModule(source, {
    compilerOptions: { module: typescript.ModuleKind.CommonJS, target: typescript.ScriptTarget.ES2022 },
  }).outputText;
  const compiledModule = { exports: {} };
  vm.runInNewContext(output, { module: compiledModule, exports: compiledModule.exports });
  return compiledModule.exports.raceControlItems;
}

test("maps actual race-control fields with exact labels and preserves input", () => {
  const raceControlItems = loadMapper();
  const map = (value) => Array.from(raceControlItems(value));
  const data = {
    active_session: { event_name: "  Grand Prix  ", name: "Fallback Event", circuit_name: "  Circuit  " },
    open_incidents: 0,
    next_event: { name: "  Next Grand Prix  ", circuit_name: "  Next Circuit  " },
    scheduled_events: [{ name: "Scheduled Event" }],
    id: "fabricated-event-id",
  };
  const snapshot = structuredClone(data);
  const expected = [
    "ACTIVE: Grand Prix — Circuit",
    "OPEN INCIDENTS: 0",
    "NEXT: Next Grand Prix — Next Circuit",
  ];

  assert.deepEqual(map(data), expected);
  assert.deepEqual(data, snapshot);
  assert.deepEqual(map(data), expected);
});

test("uses active fallback names, trims optional fields, and ignores invalid counts", () => {
  const raceControlItems = loadMapper();
  const map = (value) => Array.from(raceControlItems(value));
  assert.deepEqual(map({
    active_session: { event_name: "   ", name: "  Fallback Event  ", circuit_name: [] },
    next_event: { name: "  Next Event  ", circuit_name: {} },
    open_incidents: 0,
  }), ["ACTIVE: Fallback Event", "OPEN INCIDENTS: 0", "NEXT: Next Event"]);

  for (const open_incidents of [NaN, Infinity, -Infinity, -1, "2", true, {}, []]) {
    assert.deepEqual(map({ open_incidents }), []);
  }
});

test("requires a real next event name and safely ignores malformed shapes", () => {
  const raceControlItems = loadMapper();
  const map = (value) => Array.from(raceControlItems(value));
  assert.deepEqual(map({ scheduled_events: [{ name: "Scheduled Event" }], id: "event-1" }), []);
  assert.deepEqual(map({ next_event: { circuit_name: "Circuit" } }), []);
  assert.deepEqual(map({ next_event: { name: "  ", circuit_name: "Circuit" } }), []);

  for (const value of [null, undefined, [], "", 0, {},
    { active_session: [] },
    { active_session: { event_name: [], name: {}, circuit_name: [] }, next_event: [] },
    { active_session: "bad", next_event: "bad", open_incidents: true }]) {
    assert.deepEqual(map(value), []);
  }
});
