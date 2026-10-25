import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import * as vm from "node:vm";

const require = createRequire(import.meta.url);
const typescript = require("../../node_modules/typescript");
const source = readFileSync(new URL("../../lib/live-demo-actions.ts", import.meta.url), "utf8");

async function load(context, api) {
  const realm = vm.createContext({ Promise, Error });
  const output = typescript.transpileModule(source, {
    compilerOptions: { module: typescript.ModuleKind.ESNext, target: typescript.ScriptTarget.ES2022 },
  }).outputText;
  const mockedApi = new vm.SyntheticModule(["api"], function () {
    this.setExport("api", api);
  }, { context: realm, identifier: "./api" });
  const module = new vm.SourceTextModule(output, { context: realm, identifier: "./live-demo-actions.ts" });
  await module.link(specifier => {
    if (specifier === "./api") return mockedApi;
    throw new Error(`Unexpected import: ${specifier}`);
  });
  await module.evaluate();
  return { actions: module.namespace.createLiveDemoActions(context), Error: vm.runInContext("Error", realm) };
}

function fixture(overrides = {}) {
  const state = { session: "old", deleteRace: null, events: [], ...overrides };
  const requests = [];
  const api = (path, options = {}) => new Promise((resolve, reject) => requests.push({ path, options, resolve, reject }));
  const context = {
    get session() { return state.session; },
    get deleteRace() { return state.deleteRace; },
    refreshLists: async () => ({ sessionRows: [], raceRows: [], current: true }),
    clearError: source => state.events.push(["clearError", source]),
    reportError: (source, message) => state.events.push(["reportError", source, message]),
    setDemoBusy: value => state.events.push(["busy", value]),
    setDemoMessage: value => state.events.push(["message", value]),
    setSession: value => { state.session = value; state.events.push(["session", value]); },
    setDriver: value => state.events.push(["driver", value]),
    setPackets: value => state.events.push(["packets", value]),
    setTiming: value => state.events.push(["timing", value]),
    setSnapshot: value => state.events.push(["snapshot", value]),
    setStatus: value => state.events.push(["status", value]),
    setDeleteRace: value => { state.deleteRace = value; state.events.push(["deleteRace", value]); },
    ...overrides.context,
  };
  return { state, requests, api, context };
}

test("create posts an empty body, selects the new session and clears driver", async () => {
  const f = fixture();
  f.context.refreshLists = async () => ({ sessionRows: [{ id: 42 }], raceRows: [], current: true });
  const { actions: { createDemoRace } } = await load(f.context, f.api);
  const pending = createDemoRace();
  assert.deepEqual(f.requests.map(({ path, options }) => [path, options.method, JSON.parse(options.body)]), [["/demo-races", "POST", {}]]);
  f.requests[0].resolve({ session_id: "42", event_name: "Monaco", car_count: 20 });
  await pending;
  assert.ok(f.state.events.some(event => event[0] === "session" && event[1] === "42"));
  assert.ok(f.state.events.some(event => event[0] === "driver" && event[1] === ""));
  assert.ok(f.state.events.some(event => event[0] === "message" && event[1] === "Monaco is live with 20 cars."));
  assert.deepEqual(f.state.events.filter(event => event[0] === "busy"), [["busy", true], ["busy", false]]);
});

test("create rejection preserves selection and reports a scoped error", async () => {
  const f = fixture();
  const { actions: { createDemoRace }, Error: RealmError } = await load(f.context, f.api);
  const pending = createDemoRace();
  f.requests[0].reject(new RealmError("creation failed"));
  await pending;
  assert.equal(f.state.session, "old");
  assert.ok(f.state.events.some(event => event[0] === "reportError" && event[1] === "demo" && event[2] === "creation failed"));
  assert.deepEqual(f.state.events.filter(event => event[0] === "busy"), [["busy", true], ["busy", false]]);
});

test("deleting the selected last session resets live state and closes the modal", async () => {
  const race = { session_id: "session/a ?" };
  const f = fixture({ session: race.session_id, deleteRace: race });
  f.context.refreshLists = async () => ({ sessionRows: [], raceRows: [], current: true });
  const { actions: { removeDemoRace } } = await load(f.context, f.api);
  const pending = removeDemoRace();
  assert.equal(f.requests[0].path, "/demo-races/session%2Fa%20%3F");
  assert.equal(f.requests[0].options.method, "DELETE");
  f.requests[0].resolve(undefined);
  await pending;
  for (const event of [["session", ""], ["packets", []], ["timing", { cars: [], safety_car: false }], ["snapshot", null], ["status", "Choose an active session"], ["driver", ""], ["deleteRace", null], ["message", "Generated race deleted."]]) {
    assert.ok(f.state.events.some(actual => JSON.stringify(actual) === JSON.stringify(event)), `missing event ${event[0]}`);
  }
  assert.deepEqual(f.state.events.filter(event => event[0] === "busy"), [["busy", true], ["busy", false]]);
});

test("delete rejection retains modal and selection, and null selection makes no request", async () => {
  const noSelection = fixture();
  const { actions: emptyActions } = await load(noSelection.context, noSelection.api);
  await emptyActions.removeDemoRace();
  assert.equal(noSelection.requests.length, 0);
  assert.deepEqual(noSelection.state.events, []);

  const race = { session_id: "old" };
  const f = fixture({ session: "old", deleteRace: race });
  const { actions: { removeDemoRace }, Error: RealmError } = await load(f.context, f.api);
  const pending = removeDemoRace();
  f.requests[0].reject(new RealmError("delete failed"));
  await pending;
  assert.equal(f.state.session, "old");
  assert.equal(f.state.deleteRace, race);
  assert.ok(f.state.events.some(event => event[0] === "reportError" && event[1] === "demo" && event[2] === "delete failed"));
  assert.deepEqual(f.state.events.filter(event => event[0] === "busy"), [["busy", true], ["busy", false]]);
});
