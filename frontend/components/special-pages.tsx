"use client";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Activity,
  RefreshCw,
  Radio,
  TriangleAlert,
} from "lucide-react";
import { api, asArray, listAll, Row, API_BASE } from "@/lib/api";
import { refreshLiveLists } from "@/lib/live-list-refresh";
import { createLiveDemoActions } from "@/lib/live-demo-actions";
import { belongsToLiveRun, deriveLiveTimingData } from "@/lib/live-timing-data";
import { startLiveRecordPolling } from "@/lib/live-record-polling";
import { startInitialLiveSelection, startLiveListPolling } from "@/lib/live-list-polling";
import { startLiveStream } from "@/lib/live-stream";
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
import { LiveSelectors } from "./pages/live/live-selectors";
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
    return refreshLiveLists(listRequest, setSessions, setDemoRaces, clearError);
  }, [clearError]);
  useEffect(() => {
    return startInitialLiveSelection(refreshLists, autoFollow, setSession, reportError);
  }, [refreshLists, reportError]);
  useEffect(() => {
    return startLiveListPolling(refreshLists, session, autoFollow, listRequest, setSession, setDriver);
  }, [refreshLists, session]);
  useEffect(() => {
    return startLiveRecordPolling(session, clearError, setCompletedLaps, setLiveIncidents, setLivePitStops, setRecordsError);
  }, [clearError, session]);
  const demoActions = () => createLiveDemoActions({
    session,
    deleteRace,
    refreshLists,
    clearError,
    reportError,
    setDemoBusy,
    setDemoMessage,
    setSession,
    setDriver,
    setPackets,
    setTiming,
    setSnapshot,
    setStatus,
    setDeleteRace,
  });
  const createDemoRace = () => demoActions().createDemoRace();
  const removeDemoRace = () => demoActions().removeDemoRace();
  useEffect(() => {
    return startLiveStream({
      session, clearError, reportError, setStatus, setSessionDrivers,
      setPackets, setCompletedLaps, setLiveIncidents, setLivePitStops,
      setTiming, setSnapshot,
    });
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
      <LiveSelectors
        session={session}
        setSession={setSession}
        driver={driver}
        setDriver={setDriver}
        autoFollow={autoFollow}
        sessions={sessions}
        namedDrivers={namedDrivers}
        driverIds={driverIds}
        status={status}
      />
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
