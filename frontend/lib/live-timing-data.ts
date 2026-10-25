import type { Row } from "./api";

export function deriveLiveTimingData(
  packets: Row[],
  driver: string,
  sessionDrivers: Row[],
  timing: { cars?: Row[]; [key: string]: unknown },
  completedLaps: Row[],
  demoRaces: Row[],
  showCompletedDemos: boolean,
  showAllLaps: boolean,
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
  const driverIds = new Set([
    ...latestByDriver.keys(),
    ...timingByDriver.keys(),
  ]);
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
    return {
      ...car,
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
    orderRows,
    chartPackets,
    hasTireTemperatures,
    visibleDemoRaces,
    selectedLaps,
    visibleLaps,
  };
}
