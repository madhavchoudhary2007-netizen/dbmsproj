import type { Row } from "./api";

export function belongsToLiveRun(
  packet: Row,
  session: string,
  startedAt: string | undefined,
): boolean {
  if (String(packet.session_id || session) !== session) return false;
  if (!startedAt || !packet.ts) return true;
  const packetTime = new Date(String(packet.ts)).getTime();
  const runStart = new Date(String(startedAt)).getTime();
  return (
    !Number.isFinite(packetTime) ||
    !Number.isFinite(runStart) ||
    packetTime >= runStart
  );
}

export function deriveLiveTimingData(
  packets: Row[],
  driver: string,
  sessionDrivers: Row[],
  timing: { cars?: Row[]; [key: string]: unknown },
  completedLaps: Row[],
  demoRaces: Row[],
  showCompletedDemos: boolean,
  showAllLaps: boolean,
  pitStops?: Row[],
) {
  const shown = packets.filter((p) => !driver || p.driver_id === driver);
  const namedDrivers = new Map<string, Row>();
  for (const person of sessionDrivers) namedDrivers.set(String(person.id), person);
  const latestByDriver = new Map<string, Row>();
  for (const packet of packets) {
    if (packet.driver_id) latestByDriver.set(String(packet.driver_id), packet);
  }
  const timingCars: Row[] = Array.isArray(timing.cars) ? timing.cars : [];
  const timingByDriver = new Map(
    timingCars.map((car) => [String(car.driver_id), car]),
  );
  const validMs = (value: unknown): value is number =>
    typeof value === "number" && Number.isFinite(value) && value > 0;
  const validIndex = (value: unknown): value is number =>
    typeof value === "number" && Number.isFinite(value) && value >= 0;
  const sectorHistory = new Map<string, number[]>();
  const overallSectorBest: number[] = [];
  let fastestLapMs: number | undefined;
  for (const sample of completedLaps) {
    if (validMs(sample.lap_time_ms)) {
      fastestLapMs = fastestLapMs === undefined
        ? sample.lap_time_ms
        : Math.min(fastestLapMs, sample.lap_time_ms);
    }
    if (!Array.isArray(sample.sector_ms)) continue;
    const id = String(sample.driver_id);
    const personal = sectorHistory.get(id) || [];
    sample.sector_ms.forEach((value: unknown, sector: number) => {
      if (!validMs(value)) return;
      personal[sector] = personal[sector] === undefined
        ? value
        : Math.min(personal[sector], value);
      overallSectorBest[sector] = overallSectorBest[sector] === undefined
        ? value
        : Math.min(overallSectorBest[sector], value);
    });
    sectorHistory.set(id, personal);
  }
  const driverIds = new Set([
    ...latestByDriver.keys(),
    ...timingByDriver.keys(),
  ]);
  const pitStopCounts = new Map<string, { ids: Set<string>; withoutId: number }>();
  for (const stop of pitStops || []) {
    if (typeof stop.driver_id !== "string" || !stop.driver_id || stop.status !== "COMPLETED") continue;
    const count = pitStopCounts.get(stop.driver_id) || { ids: new Set<string>(), withoutId: 0 };
    if (stop.id === undefined || stop.id === null) count.withoutId += 1;
    else count.ids.add(String(stop.id));
    pitStopCounts.set(stop.driver_id, count);
  }
  const runningOrder: Row[] = [...driverIds]
    .map((id): Row => {
      const packet = latestByDriver.get(id) || {};
      const car = timingByDriver.get(id) || {};
      const person = namedDrivers.get(id) || {};
      const laps = completedLaps
        .filter((sample) => String(sample.driver_id) === id)
        .map((sample) => Number(sample.lap_time_ms))
        .filter((time) => Number.isFinite(time) && time > 0);
      return {
        ...packet,
        ...car,
        driver_id: id,
        driver_name: person.full_name || person.number || id,
        team_name: person.team_name || "—",
        number: person.number,
        licence_number: person.licence_number || "—",
        pit_count: pitStops === undefined
          ? undefined
          : (pitStopCounts.get(id)?.ids.size || 0) + (pitStopCounts.get(id)?.withoutId || 0),
        last_lap_ms: car.last_lap_ms ?? packet.last_lap_ms ?? car.lap_time_ms ?? packet.lap_time_ms,
        best_lap_ms: laps.length ? Math.min(...laps) : undefined,
        sector_times_ms: Array.isArray(car.sector_ms)
          ? car.sector_ms.join(" / ")
          : Array.isArray(packet.sector_ms)
            ? packet.sector_ms.join(" / ")
            : undefined,
      };
    })
    .sort(
      (a: Row, b: Row) =>
        Number(a.position || 9999) - Number(b.position || 9999),
    );
  const leaderElapsed = Number(runningOrder[0]?.elapsed_ms);
  const orderRows: Row[] = runningOrder.map((car: Row, index): Row => {
    const elapsed = Number(car.elapsed_ms);
    const currentSectors = Array.isArray(car.sector_ms)
      ? car.sector_ms
      : Array.isArray(latestByDriver.get(String(car.driver_id))?.sector_ms)
        ? latestByDriver.get(String(car.driver_id))?.sector_ms as unknown[]
        : [];
    const personalBest = sectorHistory.get(String(car.driver_id)) || [];
    const sector_cells = Array.from({ length: 3 }, (_, sector) => {
      const value: unknown = currentSectors[sector];
      if (!validMs(value)) return { ms: null, kind: "unknown" as const };
      const overall = overallSectorBest[sector];
      const personal = personalBest[sector];
      if (overall !== undefined && value <= overall)
        return { ms: value, kind: "overall" as const };
      if (personal !== undefined && value <= personal)
        return { ms: value, kind: "personal" as const };
      return personal !== undefined
        ? { ms: value, kind: "slower" as const }
        : { ms: value, kind: "unknown" as const };
    });
    const preceding = runningOrder[index - 1];
    const lapDelta = preceding && validIndex(car.lap) && validIndex(preceding.lap)
      ? preceding.lap - car.lap
      : undefined;
    const sectorDelta = preceding && lapDelta === 0 &&
      Number.isFinite(car.sector) && Number.isFinite(preceding.sector)
      ? Number(preceding.sector) - Number(car.sector)
      : undefined;
    const prevElapsed = preceding?.elapsed_ms;
    const intervalMs = preceding && lapDelta === 0 && sectorDelta === 0 &&
      validMs(car.elapsed_ms) && validMs(prevElapsed)
      ? Math.max(0, car.elapsed_ms - prevElapsed)
      : undefined;
    return {
      ...car,
      interval: index === 0
        ? "LEADER"
        : lapDelta !== undefined && lapDelta > 0
          ? `+${lapDelta} lap${lapDelta === 1 ? "" : "s"}`
          : sectorDelta !== undefined && sectorDelta > 0
            ? `+${sectorDelta} sector${sectorDelta === 1 ? "" : "s"}`
            : intervalMs !== undefined
              ? `+${(intervalMs / 1000).toFixed(3)} s`
              : "—",
      sector_cells,
      fastest_lap: fastestLapMs !== undefined && car.best_lap_ms === fastestLapMs,
      gap:
        index === 0
          ? "LEADER"
          : Number.isFinite(elapsed) && Number.isFinite(leaderElapsed)
            ? Number(car.lap || 0) < Number(runningOrder[0]?.lap || 0)
              ? `+${Number(runningOrder[0]?.lap || 0) - Number(car.lap || 0)} lap${Number(runningOrder[0]?.lap || 0) - Number(car.lap || 0) === 1 ? "" : "s"}`
              : Number(car.sector || 0) < Number(runningOrder[0]?.sector || 0)
                ? `+${Number(runningOrder[0]?.sector || 0) - Number(car.sector || 0)} sector${Number(runningOrder[0]?.sector || 0) - Number(car.sector || 0) === 1 ? "" : "s"}`
                : `+${(Math.max(0, elapsed - leaderElapsed) / 1000).toFixed(3)} s`
            : "—",
    };
  });
  const chartPackets = shown.slice(-80).map((packet) => {
    const temps = Array.isArray(packet.tire_temp_c) ? packet.tire_temp_c : [];
    return {
      ...packet,
      temp_fl: temps[0],
      temp_fr: temps[1],
      temp_rl: temps[2],
      temp_rr: temps[3],
    };
  });
  const hasTireTemperatures = shown.some(
    (packet) =>
      Array.isArray(packet.tire_temp_c) && packet.tire_temp_c.length > 0,
  );
  const visibleDemoRaces = showCompletedDemos
    ? demoRaces
    : demoRaces.filter((race) => race.state === "ACTIVE" || race.state === "PAUSED")
      .concat(demoRaces.filter((race) => race.state !== "ACTIVE" && race.state !== "PAUSED").slice(0, 5));
  const selectedLaps = completedLaps.filter((lap) => !driver || String(lap.driver_id) === driver);
  const visibleLaps = showAllLaps ? selectedLaps : selectedLaps.slice(-100);
  return {
    shown,
    namedDrivers,
    driverIds,
    orderRows,
    chartPackets,
    hasTireTemperatures,
    visibleDemoRaces,
    selectedLaps,
    visibleLaps,
  };
}
