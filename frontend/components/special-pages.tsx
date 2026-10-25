"use client";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Activity,
  RefreshCw,
  Radio,
  TriangleAlert,
} from "lucide-react";
import { api, asArray, listAll, Row, API_BASE } from "@/lib/api";
import { createLiveDemoActions } from "@/lib/live-demo-actions";
import { deriveLiveTimingData } from "@/lib/live-timing-data";
import { startLiveRecordPolling } from "@/lib/live-record-polling";
import {
  PageHeader,
  ReloadButton,
  SearchBox,
  StateMessage,
} from "./ui";
import { useAuth } from "./auth";
import { TelemetryCharts } from "./pages/live/telemetry-charts";
import { RaceRecords } from "./pages/live/race-records";
import { TimingTower } from "./pages/live/timing-tower";
import { LatestTelemetry } from "./pages/live/latest-telemetry";
import { SnapshotStrip } from "./pages/live/snapshot-strip";
import { DemoControls } from "./pages/live/demo-controls";
import { DeleteDemoModal } from "./pages/live/delete-demo-modal";
export { Dashboard } from "@/components/pages/dashboard";
export { SessionPage } from "@/components/pages/sessions";
export { StewardDesk } from "@/components/pages/stewards";
export { DbmsCenter } from "./pages/dbms-center";
export { PitWall } from "./pages/pit-wall";
export { Analytics } from "./pages/analytics";
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
    return startLiveRecordPolling(session, clearError, setCompletedLaps, setLiveIncidents, setLivePitStops, setRecordsError);
  }, [clearError, session]);
  const createDemoRace = () => createLiveDemoActions({ session, deleteRace, refreshLists, clearError, reportError, setDemoBusy, setDemoMessage, setSession, setDriver, setPackets, setTiming, setSnapshot, setStatus, setDeleteRace }).createDemoRace();
  const removeDemoRace = () => createLiveDemoActions({ session, deleteRace, refreshLists, clearError, reportError, setDemoBusy, setDemoMessage, setSession, setDriver, setPackets, setTiming, setSnapshot, setStatus, setDeleteRace }).removeDemoRace();
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
  const {
    shown,
    namedDrivers,
    driverIds,
    orderRows,
    chartPackets,
    hasTireTemperatures,
    visibleDemoRaces,
    selectedLaps,
    visibleLaps,
  } = deriveLiveTimingData(
    packets,
    driver,
    sessionDrivers,
    timing,
    completedLaps,
    demoRaces,
    showCompletedDemos,
    showAllLaps,
  );
  return (
    <>
      <PageHeader
        eyebrow="RACE CONTROL / LIVE TIMING"
        title="Live session"
        description="A fresh session snapshot and MongoDB telemetry stream, updated over WebSocket."
      />
      <DemoControls
        canManageDemos={canManageDemos}
        demoBusy={demoBusy}
        createDemoRace={createDemoRace}
        demoMessage={demoMessage}
        demoRaces={demoRaces}
        visibleDemoRaces={visibleDemoRaces}
        autoFollow={autoFollow}
        setSession={setSession}
        setDriver={setDriver}
        setDeleteRace={setDeleteRace}
        setShowCompletedDemos={setShowCompletedDemos}
        showCompletedDemos={showCompletedDemos}
      />
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
          <TimingTower orderRows={orderRows} status={status} />
          <RaceRecords selectedLaps={selectedLaps} recordsError={recordsError} showAllLaps={showAllLaps} setShowAllLaps={setShowAllLaps} visibleLaps={visibleLaps} namedDrivers={namedDrivers} liveIncidents={liveIncidents} livePitStops={livePitStops} />
          <SnapshotStrip snapshot={snapshot} />
          <TelemetryCharts
            driver={driver}
            shown={shown}
            chartPackets={chartPackets}
            hasTireTemperatures={hasTireTemperatures}
          />
          <LatestTelemetry shown={shown} status={status} />
        </>
      )}
      <DeleteDemoModal
        deleteRace={deleteRace}
        demoBusy={demoBusy}
        setDeleteRace={setDeleteRace}
        removeDemoRace={removeDemoRace}
      />
    </>
  );
}
