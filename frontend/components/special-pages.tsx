"use client";
import { useAnalytics } from "@/lib/use-analytics";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Activity,
  Plus,
  Trash2,
  RefreshCw,
  Radio,
  TriangleAlert,
} from "lucide-react";
import { api, asArray, listAll, Row, pretty, API_BASE } from "@/lib/api";
import {
  Button,
  DataTable,
  Modal,
  PageHeader,
  ReloadButton,
  SearchBox,
  StateMessage,
} from "./ui";
import { useAuth } from "./auth";
import { TelemetryCharts } from "./pages/live/telemetry-charts";
export { Dashboard } from "@/components/pages/dashboard";
export { SessionPage } from "@/components/pages/sessions";
export { StewardDesk } from "@/components/pages/stewards";
export { DbmsCenter } from "./pages/dbms-center";
export { PitWall } from "./pages/pit-wall";
export function LiveTiming() {
  const [sessions, setSessions] = useState<Row[]>([]),
    [demoRaces, setDemoRaces] = useState<Row[]>([]),
    [session, setSession] = useState(""),
    [sessionDrivers, setSessionDrivers] = useState<Row[]>([]),
    [driver, setDriver] = useState(""),
    [packets, setPackets] = useState<Row[]>([]),
    [completedLaps, setCompletedLaps] = useState<Row[]>([]),
    [liveIncidents, setLiveIncidents] = useState<Row[]>([]),
    [livePitStops, setLivePitStops] = useState<Row[]>([]),
    [recordsError, setRecordsError] = useState(""),
    [snapshot, setSnapshot] = useState<Record<string, unknown> | null>(null),
    [timing, setTiming] = useState<{ cars?: Row[]; safety_car?: boolean; [key: string]: unknown }>({ cars: [], safety_car: false }),
    [status, setStatus] = useState("Choose an active session"),
    [error, setError] = useState(""),
    [demoBusy, setDemoBusy] = useState(false),
    [showCompletedDemos, setShowCompletedDemos] = useState(false),
    [showAllLaps, setShowAllLaps] = useState(false),
    [deleteRace, setDeleteRace] = useState<Row | null>(null),
    [demoMessage, setDemoMessage] = useState("");
  const { user } = useAuth();
  const canManageDemos = user?.role === "ADMIN" || user?.role === "STEWARD";
  const autoFollow = useRef(true);
  const listRequest = useRef(0);
  const errorSource = useRef<"lists" | "snapshot" | "demo" | "">("");
  const reportError = useCallback((source: "lists" | "snapshot" | "demo", message: string) => {
    errorSource.current = source;
    setError(message);
  }, []);
  const clearError = useCallback((source?: "lists" | "snapshot" | "demo") => {
    if (!source || errorSource.current === source) {
      errorSource.current = "";
      setError("");
    }
  }, []);
  const refreshLists = useCallback(async () => {
    const request = ++listRequest.current;
    const [s, r] = await Promise.all([
      listAll("/sessions"),
      listAll("/demo-races"),
    ]);
    const sessionRows = asArray(s);
    const raceRows = asArray(r);
    if (request === listRequest.current) {
      setSessions(sessionRows);
      setDemoRaces(raceRows);
      clearError("lists");
    }
    return { sessionRows, raceRows, current: request === listRequest.current };
  }, [clearError]);
  useEffect(() => {
    let disposed = false;
    refreshLists()
      .then(({ sessionRows, raceRows, current }) => {
        if (disposed || !current || !autoFollow.current) return;
        const activeDemo = raceRows.find((r: Row) => r.state === "ACTIVE");
        const active = activeDemo
          ? sessionRows.find((r: Row) => String(r.id) === String(activeDemo.session_id))
          : sessionRows.find((r: Row) => r.state === "ACTIVE");
        if (active) setSession(String(active.id));
      })
      .catch((e) => { if (!disposed) reportError("lists", e instanceof Error ? e.message : "Unable to load live sessions"); });
    return () => { disposed = true; };
  }, [refreshLists, reportError]);
  useEffect(() => {
    let disposed = false;
    let timer: ReturnType<typeof setTimeout>;
    const poll = async () => {
      try {
        const { sessionRows, raceRows, current } = await refreshLists();
        if (!disposed && current && autoFollow.current) {
          const active = raceRows.find((race: Row) => race.state === "ACTIVE");
          if (active) {
            const selected = sessionRows.find((row: Row) => String(row.id) === session);
            if (!selected || selected.state === "COMPLETED") {
              const nextSession = String(active.session_id);
              if (nextSession !== session) {
                setSession(nextSession);
                setDriver("");
              }
            }
          }
        }
      } catch {}
      if (!disposed) timer = setTimeout(() => { void poll(); }, 5000);
    };
    timer = setTimeout(() => { void poll(); }, 5000);
    return () => { disposed = true; listRequest.current += 1; clearTimeout(timer); };
  }, [refreshLists, session]);
  useEffect(() => {
    if (!session) { clearError("snapshot"); setCompletedLaps([]); setLiveIncidents([]); setLivePitStops([]); setRecordsError(""); return; }
    let alive = true;
    setCompletedLaps([]);
    setLiveIncidents([]);
    setLivePitStops([]);
    setRecordsError("");
    clearError("snapshot");
    let timer: ReturnType<typeof setTimeout> | undefined;
    const load = async () => {
      try {
        const value = await api<{ laps?: Row[]; incidents?: Row[]; pit_reservations?: Row[] }>(`/sessions/${session}/laps`);
        if (alive) {
          setCompletedLaps(asArray(value.laps));
          setLiveIncidents(asArray(value.incidents));
          setLivePitStops(asArray(value.pit_reservations));
          setRecordsError("");
        }
      } catch (e) {
        if (alive) setRecordsError(e instanceof Error ? e.message : "Unable to load lap and race-control records");
      } finally {
        if (alive) timer = setTimeout(() => { void load(); }, 5000);
      }
    };
    void load();
    return () => { alive = false; if (timer) clearTimeout(timer); };
  }, [clearError, session]);
  const createDemoRace = async () => {
    setDemoBusy(true);
    clearError();
    setDemoMessage("");
    try {
      const created = await api<{ session_id?: string | number; event_name?: string; car_count?: number } & Record<string, unknown>>("/demo-races", {
        method: "POST",
        body: JSON.stringify({}),
      });
      const { sessionRows } = await refreshLists();
      const newSession = sessionRows.find((r) => String(r.id) === String(created.session_id));
      if (newSession) setSession(String(newSession.id));
      setDriver("");
      setDemoMessage(`${created.event_name || "Generated race"} is live with ${created.car_count} cars.`);
    } catch (e) {
      reportError("demo", e instanceof Error ? e.message : "Unable to create live race");
    } finally {
      setDemoBusy(false);
    }
  };
  const removeDemoRace = async () => {
    if (!deleteRace) return;
    const race = deleteRace;
    setDemoBusy(true);
    clearError();
    try {
      await api(`/demo-races/${encodeURIComponent(String(race.session_id))}`, { method: "DELETE" });
      const { sessionRows, raceRows } = await refreshLists();
      if (session === String(race.session_id)) {
        const activeDemo = raceRows.find((r: Row) => r.state === "ACTIVE");
        const next = activeDemo && sessionRows.find((r) => String(r.id) === String(activeDemo.session_id));
        const nextSession = String(next?.id || sessionRows.find((r: Row) => r.state === "ACTIVE")?.id || "");
        setSession(nextSession);
        if (!nextSession) {
          setPackets([]);
          setTiming({ cars: [], safety_car: false });
          setSnapshot(null);
          setStatus("Choose an active session");
        }
        setDriver("");
      }
      setDeleteRace(null);
      setDemoMessage("Generated race deleted.");
    } catch (e) {
      reportError("demo", e instanceof Error ? e.message : "Unable to delete generated race");
    } finally {
      setDemoBusy(false);
    }
  };
  useEffect(() => {
    if (!session) { setStatus("Choose an active session"); return; }
    setStatus("Connecting · live stream");
    setSessionDrivers([]);
    setPackets([]);
    setTiming({ cars: [], safety_car: false });
    setSnapshot(null);
    let alive = true,
      ws: WebSocket | undefined,
      timer: ReturnType<typeof setTimeout> | undefined,
      attempt = 0,
      startedAt: string | undefined,
      refreshRequest = 0,
      sessionState = "",
      streamConnected = false;
    const updateStreamStatus = () => {
      if (sessionState === "COMPLETED") setStatus("Completed · final timing");
      else if (sessionState === "PAUSED") setStatus(streamConnected ? "Paused · stream connected" : "Paused · reconnecting");
      else if (sessionState === "SCHEDULED") setStatus("Scheduled · waiting to start");
      else if (sessionState === "CANCELLED") setStatus("Cancelled · stream stopped");
      else setStatus(streamConnected ? "Connected · live stream" : "Connecting · live stream");
    };
    const belongsToCurrentRun = (packet: Row) => {
      if (String(packet.session_id || session) !== session) return false;
      if (!startedAt || !packet.ts) return true;
      const packetTime = new Date(String(packet.ts)).getTime();
      const runStart = new Date(String(startedAt)).getTime();
      return (
        !Number.isFinite(packetTime) ||
        !Number.isFinite(runStart) ||
        packetTime >= runStart
      );
    };
    const refresh = async () => {
      const request = ++refreshRequest;
      try {
        const s = await api<{ session?: Row; drivers?: Row[]; packets?: Row[] } & Record<string, unknown>>(`/sessions/${session}/live`);
        if (!alive || request !== refreshRequest) return;
        if (alive) {
          const sessionData = s.session || s;
          sessionState = String(sessionData.state || sessionState);
          setSnapshot(sessionData);
          setSessionDrivers(asArray(s.drivers));
          startedAt = (sessionData.started_at as string | undefined) || startedAt;
          setTiming((prev) => ({
            ...prev,
            safety_car: (s.session?.safety_car as boolean | undefined) ?? prev.safety_car,
          }));
          if (Array.isArray(s.packets))
            setPackets(s.packets.filter(belongsToCurrentRun));
          clearError("snapshot");
          updateStreamStatus();
          if (sessionState === "COMPLETED" || sessionState === "CANCELLED")
            ws?.close();
        }
      } catch (e) {
        if (alive && request === refreshRequest)
          reportError("snapshot", e instanceof Error ? e.message : "Unable to fetch snapshot");
      }
    };
    const connect = () => {
      if (!alive) return;
      const wsBase = API_BASE.replace(/^http/, "ws");
      ws = new WebSocket(`${wsBase}/api/ws/sessions/${session}`);
      ws.onopen = () => {
        if (!alive) return;
        attempt = 0;
        streamConnected = true;
        updateStreamStatus();
      };
      ws.onmessage = (e) => {
        if (!alive) return;
        try {
          const msg = JSON.parse(e.data);
          if (
            msg.type === "session.state" &&
            String(msg.session_id || session) === session
          ) {
            const stateData = msg.data || {};
            const nextStartedAt = stateData.started_at || msg.started_at;
            const startsNewRun = Boolean(nextStartedAt && startedAt && String(nextStartedAt) !== startedAt);
            const resetsRun = stateData.state === "PAUSED" &&
              Object.prototype.hasOwnProperty.call(stateData, "started_at") &&
              !stateData.started_at && Boolean(startedAt);
            if (startsNewRun || resetsRun) {
              setPackets([]);
              setCompletedLaps([]);
              setLiveIncidents([]);
              setLivePitStops([]);
              setTiming({ cars: [], safety_car: false });
              if (resetsRun) startedAt = undefined;
            }
            if (nextStartedAt) startedAt = String(nextStartedAt);
            sessionState = String(stateData.state || sessionState);
            updateStreamStatus();
            if (sessionState === "CANCELLED") ws?.close();
            void refresh();
          }
          setSnapshot((prev) => ({
            ...prev,
            ...(msg.data || {}),
            last_event: msg,
          }));
          if (
            msg.type === "timing.update" &&
            String(msg.session_id || session) === session &&
            !Array.isArray(msg.data)
          ) {
            setTiming(msg.data || { cars: [] });
          }
          if (
            msg.type === "telemetry.sample" &&
            belongsToCurrentRun(msg.data || {})
          )
            setPackets((p) => [...p, msg.data].slice(-100));
        } catch {}
      };
      ws.onerror = () => {
        if (!alive) return;
        streamConnected = false;
        if (sessionState === "COMPLETED" || sessionState === "PAUSED" || sessionState === "SCHEDULED" || sessionState === "CANCELLED") updateStreamStatus();
        else setStatus("Stream interrupted · reconnecting");
      };
      ws.onclose = () => {
        if (!alive) return;
        streamConnected = false;
        if (sessionState === "COMPLETED" || sessionState === "PAUSED" || sessionState === "SCHEDULED" || sessionState === "CANCELLED") updateStreamStatus();
        else setStatus("Disconnected · reconnecting");
        if (sessionState === "COMPLETED" || sessionState === "CANCELLED") return;
        const delay = Math.min(1000 * 2 ** attempt++, 15000);
        timer = setTimeout(() => {
          void refresh();
          connect();
        }, delay);
      };
    };
    void refresh();
    connect();
    return () => {
      alive = false;
      clearTimeout(timer);
      ws?.close();
    };
  }, [clearError, reportError, session]);
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
  return (
    <>
      <PageHeader
        eyebrow="RACE CONTROL / LIVE TIMING"
        title="Live session"
        description="A fresh session snapshot and MongoDB telemetry stream, updated over WebSocket."
      />
      {canManageDemos && (
        <section className="demo-race-hero panel" aria-labelledby="demo-race-title">
          <div>
            <div className="eyebrow">LIVE DEMO / READY TO RUN</div>
            <h2 id="demo-race-title">Put a full grid on track</h2>
            <p>Start a generated race with 8–16 fictional drivers and live timing. Sessions support up to 72 laps.</p>
          </div>
          <Button disabled={demoBusy} data-primary="true" onClick={() => void createDemoRace()}>
            <Plus size={15} /> {demoBusy ? "Starting race…" : "Create live race"}
          </Button>
        </section>
      )}
      {demoMessage && <div className="notice" role="status">{demoMessage}</div>}
      {demoRaces.length > 0 && (
        <section className="panel demo-races-panel" aria-labelledby="demo-races-title">
          <div className="panel-heading">
            <div><div className="eyebrow">GENERATED SESSIONS</div><h2 id="demo-races-title">Live race demos</h2></div>
            <span className="muted">{demoRaces.length} race{demoRaces.length === 1 ? "" : "s"}</span>
          </div>
          <div className="demo-race-list">
            {visibleDemoRaces.map((race: Row) => (
              <div className="demo-race-row" key={String(race.session_id)}>
                <button className="demo-race-select" onClick={() => { autoFollow.current = false; setSession(String(race.session_id)); setDriver(""); }} aria-label={`Show ${race.event_name} ${String(race.session_id).slice(0, 8)} live timing`}>
                  <span className="demo-race-name">{String(race.event_name || "Generated race")}</span>
                  <span className="demo-race-meta">{String(race.circuit_name || "Circuit pending")} · {String(race.car_count)} cars · {String(race.total_laps)} laps · {String(race.created_at || "").slice(0, 10)} · {String(race.session_id).slice(0, 8)}</span>
                </button>
                <span className={`demo-state ${race.state === "ACTIVE" ? "is-active" : ""}`}>{String(race.state)}</span>
                {canManageDemos && <button className="icon-button danger-icon" aria-label={`Delete ${race.event_name} ${String(race.session_id).slice(0, 8)}`} disabled={demoBusy} onClick={() => setDeleteRace(race)}><Trash2 size={15} /></button>}
              </div>
            ))}
          </div>
          {demoRaces.length > visibleDemoRaces.length && <Button kind="secondary" onClick={() => setShowCompletedDemos(true)}>Show all {demoRaces.length} generated races</Button>}
          {showCompletedDemos && demoRaces.length > 6 && <Button kind="secondary" onClick={() => setShowCompletedDemos(false)}>Show recent races</Button>}
        </section>
      )}
      <div className="toolbar select-toolbar">
        <label>
          Session
          <select value={session} onChange={(e) => { autoFollow.current = false; setSession(e.target.value); setDriver(""); }}>
            <option value="">Select session</option>
            {sessions.map((s) => (
              <option key={String(s.id)} value={String(s.id)}>
                {String(s.event_name || s.session_type || s.id)} · {String(s.state)} · {String(s.scheduled_at || "").slice(0, 10)} · {String(s.id).slice(0, 8)}
              </option>
            ))}
          </select>
        </label>
        <label>
          Driver
          <select value={driver} onChange={(e) => setDriver(e.target.value)}>
            <option value="">All drivers</option>
            {[...namedDrivers.values()].filter((d) => driverIds.has(String(d.id))).map((d) => (
              <option key={String(d.id)} value={String(d.id)}>
                {String(d.full_name || d.number || d.id)}
              </option>
            ))}
          </select>
        </label>
        <span className="stream-state">
          <i
            className={
              status.startsWith("Connected") ? "green-dot" : "amber-dot"
            }
          />
          {status}
        </span>
      </div>
      {error && <div className="notice error-notice">{error}</div>}
      {session && (
        <>
          {Boolean(timing.safety_car ?? snapshot?.safety_car) && (
            <div className="safety-car-banner">
              <TriangleAlert size={16} /> SAFETY CAR DEPLOYED
            </div>
          )}
          <div className="panel running-order-panel">
            <div className="panel-heading">
              <div>
                <div className="eyebrow">LIVE TIMING / RUNNING ORDER</div>
                <h2>{orderRows.length} cars on timing</h2>
              </div>
              <span className="live-badge">
                <i /> {status}
              </span>
            </div>
            {orderRows.length ? (
              <DataTable
                rows={orderRows.map((car) => ({
                  ...car,
                  position: car.position ?? "—",
                  sector: car.sector ?? "—",
                  last_lap_ms: car.last_lap_ms ?? "—",
                  best_lap_ms: car.best_lap_ms ?? "—",
                  tire_compound: car.tire_compound ?? "—",
                  tire_age_laps: car.tire_age_laps ?? "—",
                  tire_wear_pct: car.tire_wear_pct ?? "—",
                  pit_state: car.pit_state ?? "—",
                }))}
                columns={[
                  "position",
                  "number",
                  "driver_name",
                  "licence_number",
                  "team_name",
                  "gap",
                  "lap",
                  "sector",
                  "sector_times_ms",
                  "last_lap_ms",
                  "best_lap_ms",
                  "tire_compound",
                  "tire_age_laps",
                  "tire_wear_pct",
                  "pit_state",
                  "pit_box_number",
                ]}
              />
            ) : (
              <StateMessage empty="Waiting for timing and telemetry packets from this session." />
            )}
          </div>
          <div className="panel">
            <div className="panel-heading"><div><div className="eyebrow">RECORDED LAPS</div><h2>Driver lap and sector history</h2></div><span className="muted">{selectedLaps.length} completed driver laps</span></div>
            {recordsError && <div className="notice error-notice" role="status">Lap and race-control records could not be refreshed: {recordsError}. Retrying automatically in 5 seconds.</div>}
            {selectedLaps.length > 100 && <div className="inline-form"><span className="muted">Showing {showAllLaps ? "all" : "latest 100"} laps</span><Button kind="secondary" onClick={() => setShowAllLaps((value) => !value)}>{showAllLaps ? "Show latest 100" : "Show all laps"}</Button></div>}
            <DataTable rows={visibleLaps.map((lap) => ({
              driver_name: namedDrivers.get(String(lap.driver_id))?.full_name || lap.driver_id,
              lap: lap.lap,
              sector_1_ms: Array.isArray(lap.sector_ms) ? lap.sector_ms[0] : null,
              sector_2_ms: Array.isArray(lap.sector_ms) ? lap.sector_ms[1] : null,
              sector_3_ms: Array.isArray(lap.sector_ms) ? lap.sector_ms[2] : null,
              lap_time_ms: lap.lap_time_ms,
              position: lap.position,
            }))} columns={["driver_name","lap","sector_1_ms","sector_2_ms","sector_3_ms","lap_time_ms","position"]} />
          </div>
          <div className="panel">
            <div className="panel-heading"><div><div className="eyebrow">RACE CONTROL RECORDS</div><h2>Incidents and pit stops</h2></div></div>
            <h3>Incidents</h3>
            <DataTable rows={liveIncidents} columns={["driver_name","lap","description","state"]} />
            <h3>Pit stops</h3>
            <DataTable rows={livePitStops} columns={["driver_name","team_name","box_number","starts_at","ends_at","status"]} />
          </div>
          <div className="snapshot-strip">
            {Object.entries(snapshot || {})
              .filter(
                ([k, v]) =>
                  !["participants", "drivers", "timing", "safety_car"].includes(
                    k,
                  ) && typeof v !== "object",
              )
              .map(([k, v]) => (
                <div key={k}>
                  <small>{k.replaceAll("_", " ")}</small>
                  <b>{pretty(v)}</b>
                </div>
              ))}
          </div>
          <TelemetryCharts
            driver={driver}
            shown={shown}
            chartPackets={chartPackets}
            hasTireTemperatures={hasTireTemperatures}
          />
          <div className="panel">
            <div className="panel-heading">
              <div>
                <div className="eyebrow">LATEST TELEMETRY</div>
                <h2>{shown.length} samples in view</h2>
              </div>
              <span className="live-badge">
                <i /> {status}
              </span>
            </div>
            <DataTable
              rows={shown.slice(-30).reverse()}
              columns={[
                "ts",
                "driver_id",
                "lap",
                "sector",
                "position",
                "speed_kph",
                "throttle_pct",
                "brake_pct",
                "tire_compound",
                "pit_state",
                "pit_box_number",
                "pit_reservation_id",
              ]}
            />
          </div>
        </>
      )}
      {deleteRace && (
        <Modal title="Delete generated race?" close={() => !demoBusy && setDeleteRace(null)}>
          <div className="decision-form">
            <p>Delete <strong>{String(deleteRace.event_name || "this generated race")}</strong> and its generated drivers and telemetry? This action cannot be undone.</p>
            <div className="form-actions">
              <Button kind="secondary" disabled={demoBusy} onClick={() => setDeleteRace(null)}>Keep race</Button>
              <Button kind="danger" disabled={demoBusy} onClick={() => void removeDemoRace()}>{demoBusy ? "Deleting…" : "Delete race"}</Button>
            </div>
          </div>
        </Modal>
      )}
    </>
  );
}
export function Analytics() {
  const {
    rows, page, setPage, champ, setChamp, season, setSeason, circuit,
    setCircuit, driver, setDriver, team, setTeam, opts, error, hasQueried,
    busy, search, analyticsPages, analyticsColumns, displayAnalyticsRows,
  } = useAnalytics();
  return (
    <>
      <PageHeader
        eyebrow="CHAMPIONSHIP / PERFORMANCE"
        title="Driver analytics"
        description="Filter driver metrics using the analytics API. Results and comparisons reflect returned data."
      />
      <div className="filter-panel">
        {(
          [
            ["Championship", champ, setChamp, opts.championships],
            ["Circuit", circuit, setCircuit, opts.circuits],
            ["Driver", driver, setDriver, opts.drivers],
            ["Team", team, setTeam, opts.teams],
          ] as [string, string, (val: string) => void, Row[]][]
        ).map(([title, value, setter, items]) => (
          <label key={title}>
            {title}
            <select value={value} onChange={(e) => setter(e.target.value)}>
              <option value="">All</option>
              {items.map((r: Row) => (
                <option key={String(r.id)} value={String(r.id)}>
                  {title === "Driver" ? `${String(r.full_name || r.id)} · #${String(r.number || "—")} · ${String(r.licence_number || "")}` : String(r.name || r.full_name || r.id)}
                </option>
              ))}
            </select>
          </label>
        ))}
        <label>
          Season
          <input
            value={season}
            onChange={(e) => setSeason(e.target.value)}
            placeholder="Season"
          />
        </label>
        <Button data-primary="true" onClick={() => void search()} disabled={busy}>
          {busy ? "Loading…" : "Apply filters"}
        </Button>
      </div>
      {error && <div className="notice error-notice">{error}</div>}
      <div className="panel">
        <div className="panel-heading">
          <div>
            <div className="eyebrow">API RESULTS</div>
            <h2>{hasQueried ? `${rows.length} driver records` : "Driver records"}</h2>
          </div>
        </div>
        {busy ? (
          <StateMessage loading />
        ) : !hasQueried ? (
          <p className="muted">Apply filters to load driver analytics.</p>
        ) : (
          <DataTable
            rows={displayAnalyticsRows}
            columns={analyticsColumns}
          />
        )}
        {analyticsPages > 1 && <div className="dbms-pagination"><Button kind="secondary" disabled={page === 0} onClick={() => setPage((value) => value - 1)}>Previous</Button><span className="muted">Page {page + 1} of {analyticsPages}</span><Button kind="secondary" disabled={page >= analyticsPages - 1} onClick={() => setPage((value) => value + 1)}>Next</Button></div>}
      </div>
    </>
  );
}
