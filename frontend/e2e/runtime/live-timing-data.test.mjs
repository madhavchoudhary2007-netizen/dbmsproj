import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import * as vm from "node:vm";

const require = createRequire(import.meta.url);
const typescript = require("../../node_modules/typescript");
const source = readFileSync(new URL("../../lib/live-timing-data.ts", import.meta.url), "utf8");

async function load() {
  const realm = vm.createContext({ Date, Map, Set, Number, String, Array });
  const output = typescript.transpileModule(source, {
    compilerOptions: { module: typescript.ModuleKind.ESNext, target: typescript.ScriptTarget.ES2022 },
  }).outputText;
  const sourceModule = new vm.SourceTextModule(output, { context: realm, identifier: "./live-timing-data.ts" });
  await sourceModule.link(() => { throw new Error("Unexpected runtime import"); });
  await sourceModule.evaluate();
  return sourceModule.namespace;
}

const plain = value => JSON.parse(JSON.stringify(value));

test("keeps names, sectors, and best laps attached to drivers across shuffled packets", async () => {
  const { deriveLiveTimingData } = await load();
  const data = deriveLiveTimingData(
    [{ driver_id: "2", lap: 4 }, { driver_id: "1", lap: 5 }, { driver_id: "2", lap: 5 }],
    "", [{ id: "1", full_name: "One" }, { id: "2", full_name: "Two" }],
    { cars: [{ driver_id: "2", position: 2, sector_ms: [110, 120, 130] }, { driver_id: "1", position: 1, sector_ms: [100, 105, 110] }] },
    [{ driver_id: "1", lap_time_ms: 90000 }, { driver_id: "2", lap_time_ms: 92000 }, { driver_id: "1", lap_time_ms: 88000 }], [], false, false,
  );
  assert.deepEqual(plain(data.orderRows.map(row => [row.driver_id, row.driver_name, row.sector_times_ms, row.best_lap_ms, row.lap])), [
    ["1", "One", "100 / 105 / 110", 88000, 5], ["2", "Two", "110 / 120 / 130", 92000, 5],
  ]);
});

test("limits selected driver charts to the latest 80 and laps to the latest 100 by default", async () => {
  const { deriveLiveTimingData } = await load();
  const packets = Array.from({ length: 110 }, (_, i) => ({ driver_id: i % 2 ? "a" : "b", sample: i, tire_temp_c: [i, i + 1, i + 2, i + 3] }));
  const laps = Array.from({ length: 240 }, (_, i) => ({ driver_id: i % 2 ? "a" : "b", lap_time_ms: i + 1 }));
  const selected = deriveLiveTimingData(packets, "a", [], {}, laps, [], false, false);
  assert.equal(selected.chartPackets.length, 55);
  assert.deepEqual(plain(selected.chartPackets.at(-1)), { driver_id: "a", sample: 109, tire_temp_c: [109, 110, 111, 112], temp_fl: 109, temp_fr: 110, temp_rl: 111, temp_rr: 112 });
  assert.deepEqual(plain([selected.selectedLaps.length, selected.visibleLaps.length, selected.visibleLaps[0].lap_time_ms, selected.visibleLaps.at(-1).lap_time_ms]), [120, 100, 42, 240]);
  const all = deriveLiveTimingData(packets, "a", [], {}, laps, [], false, true);
  assert.equal(all.visibleLaps.length, 120);
  const history = deriveLiveTimingData(Array.from({ length: 100 }, (_, i) => ({ driver_id: "a", sample: i })), "a", [], {}, [], [], false, false);
  assert.deepEqual(plain([history.chartPackets.length, history.chartPackets[0].sample]), [80, 20]);
});

test("labels the leader, lapped cars, sector gaps, and elapsed time gaps", async () => {
  const { deriveLiveTimingData } = await load();
  const { orderRows } = deriveLiveTimingData([
    { driver_id: "l", position: 1, lap: 3, sector: 2, elapsed_ms: 120000 },
    { driver_id: "x", position: 2, lap: 3, sector: 2, elapsed_ms: 121234 },
    { driver_id: "s", position: 3, lap: 3, sector: 1, elapsed_ms: 121000 },
    { driver_id: "b", position: 4, lap: 2, sector: 1, elapsed_ms: 110000 },
  ], "", [], {}, [], [], false, false);
  assert.deepEqual(plain(orderRows.map(row => row.gap)), ["LEADER", "+1.234 s", "+1 sector", "+1 lap"]);
});

test("shows active and paused demos with five recent completed demos unless all are requested", async () => {
  const { deriveLiveTimingData } = await load();
  const races = [{ id: "active", state: "ACTIVE" }, { id: "paused", state: "PAUSED" }, ...Array.from({ length: 7 }, (_, i) => ({ id: `done${i}`, state: "COMPLETED" }))];
  const recent = deriveLiveTimingData([], "", [], {}, [], races, false, false).visibleDemoRaces;
  const all = deriveLiveTimingData([], "", [], {}, [], races, true, false).visibleDemoRaces;
  assert.deepEqual(plain(recent.map(race => race.id)), ["active", "paused", "done0", "done1", "done2", "done3", "done4"]);
  assert.deepEqual(plain(all.map(race => race.id)), races.map(race => race.id));
});

test("filters live-run packets by session and run start while retaining missing or invalid timestamp fallback", async () => {
  const { belongsToLiveRun } = await load();
  const start = "2026-01-01T00:00:00Z";
  assert.deepEqual([
    belongsToLiveRun({ session_id: "other", ts: start }, "session", start),
    belongsToLiveRun({ session_id: "session", ts: "2025-12-31T23:59:59Z" }, "session", start),
    belongsToLiveRun({ session_id: "session", ts: start }, "session", start),
    belongsToLiveRun({ session_id: "session", ts: "2026-01-01T00:00:01Z" }, "session", start),
    belongsToLiveRun({ session_id: "session" }, "session", start),
    belongsToLiveRun({ session_id: "session", ts: "invalid" }, "session", start),
    belongsToLiveRun({ session_id: "session", ts: start }, "session", "invalid"),
    belongsToLiveRun({ session_id: "session", ts: start }, "session", undefined),
  ], [false, false, true, true, true, true, true, true]);
});

test("derives intervals from the preceding car while preserving leader gaps", async () => {
  const { deriveLiveTimingData } = await load();
  const { orderRows } = deriveLiveTimingData([
    { driver_id: "l", position: 1, lap: 4, sector: 3, elapsed_ms: 120000 },
    { driver_id: "a", position: 2, lap: 4, sector: 3, elapsed_ms: 123000 },
    { driver_id: "b", position: 3, lap: 4, sector: 3, elapsed_ms: 123450 },
    { driver_id: "s", position: 4, lap: 4, sector: 2, elapsed_ms: 123500 },
    { driver_id: "x", position: 5, lap: 3, sector: 3, elapsed_ms: 110000 },
    { driver_id: "u", position: 6, lap: 4, sector: 3, elapsed_ms: null },
    { driver_id: "n", position: 7, lap: 4, sector: 3, elapsed_ms: "124000" },
  ], "", [], {}, [], [], false, false);
  assert.deepEqual(plain(orderRows.map(row => [row.interval, row.gap])), [
    ["LEADER", "LEADER"], ["+3.000 s", "+3.000 s"], ["+0.450 s", "+3.450 s"],
    ["+1 sector", "+1 sector"], ["+1 lap", "+1 lap"], ["—", "+0.000 s"], ["—", "+4.000 s"],
  ]);
});

test("derives three sector cells from shuffled driver history without mutating inputs", async () => {
  const { deriveLiveTimingData } = await load();
  const packets = [
    { driver_id: "a", position: 1, sector_ms: [90, 200, 301] },
    { driver_id: "b", position: 2, sector_ms: [120, 180, 290] },
    { driver_id: "c", position: 3, sector_ms: [130, 400, 320] },
    { driver_id: "d", position: 4 },
  ];
  const history = [
    { driver_id: "b", sector_ms: [110, 180] },
    { driver_id: "a", sector_ms: [100, 200] },
    { driver_id: "a", sector_ms: [95, null] },
    { driver_id: "z", sector_ms: [0, -5, NaN] },
  ];
  const before = plain([packets, history]);
  const { orderRows } = deriveLiveTimingData(packets, "", [], {}, history, [], false, false);
  assert.deepEqual(plain(orderRows.map(row => row.sector_cells)), [
    [{ ms: 90, kind: "overall" }, { ms: 200, kind: "personal" }, { ms: 301, kind: "unknown" }],
    [{ ms: 120, kind: "slower" }, { ms: 180, kind: "overall" }, { ms: 290, kind: "unknown" }],
    [{ ms: 130, kind: "unknown" }, { ms: 400, kind: "unknown" }, { ms: 320, kind: "unknown" }],
    [{ ms: null, kind: "unknown" }, { ms: null, kind: "unknown" }, { ms: null, kind: "unknown" }],
  ]);
  assert.deepEqual(plain([packets, history]), before);
});

test("marks every tied positive fastest lap and leaves drivers without one unmarked", async () => {
  const { deriveLiveTimingData } = await load();
  const { orderRows } = deriveLiveTimingData([
    { driver_id: "a", position: 1 }, { driver_id: "b", position: 2 },
    { driver_id: "c", position: 3 }, { driver_id: "d", position: 4 },
  ], "", [], {}, [
    { driver_id: "b", lap_time_ms: 85000 }, { driver_id: "a", lap_time_ms: 85000 },
    { driver_id: "c", lap_time_ms: 0 }, { driver_id: "c", lap_time_ms: -1 },
    { driver_id: "c", lap_time_ms: NaN },
  ], [], false, false);
  assert.deepEqual(plain(orderRows.map(row => [row.best_lap_ms, row.fastest_lap])), [
    [85000, true], [85000, true], [null, false], [null, false],
  ]);
  assert.equal(orderRows[2].best_lap_ms, undefined);
  assert.equal(orderRows[3].best_lap_ms, undefined);
});
