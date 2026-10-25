"use client";
import { useCallback, useEffect } from "react";
import { TriangleAlert } from "lucide-react";
import { refreshLiveLists } from "@/lib/live-list-refresh";
import { createLiveDemoActions } from "@/lib/live-demo-actions";
import { deriveLiveTimingData } from "@/lib/live-timing-data";
import { startLiveRecordPolling } from "@/lib/live-record-polling";
import { startInitialLiveSelection, startLiveListPolling } from "@/lib/live-list-polling";
import { startLiveStream } from "@/lib/live-stream";
import { NbBadge } from "@/components/nb/badge";
import { NbCard } from "@/components/nb/card";
import { useLiveTimingState } from "@/lib/use-live-timing-state";
import { TelemetryCharts } from "./telemetry-charts";
import { RaceRecords } from "./race-records";
import { TimingTower } from "./timing-tower";
import { LatestTelemetry } from "./latest-telemetry";
import { SnapshotStrip } from "./snapshot-strip";
import { DemoControls } from "./demo-controls";
import { DeleteDemoModal } from "./delete-demo-modal";
import { LiveSelectors } from "./live-selectors";

export function LiveTiming() {
  const {
    sessions, setSessions, demoRaces, setDemoRaces, session, setSession,
    sessionDrivers, setSessionDrivers, driver, setDriver, packets, setPackets,
    completedLaps, setCompletedLaps, liveIncidents, setLiveIncidents,
    livePitStops, setLivePitStops, recordsError, setRecordsError,
    setListLoading, setListError,
    snapshot, setSnapshot, timing, setTiming, status, setStatus, error, setError,
    demoBusy, setDemoBusy, showCompletedDemos, setShowCompletedDemos,
    showAllLaps, setShowAllLaps, deleteRace, setDeleteRace, demoMessage,
    setDemoMessage, canManageDemos, autoFollow, listRequest, reportError, clearError,
  } = useLiveTimingState();
  const refreshLists = useCallback(async () => {
    return refreshLiveLists(listRequest, setSessions, setDemoRaces, clearError, (error) => {
      setListLoading(false);
      setListError(error);
    });
  }, [clearError, listRequest, setDemoRaces, setListError, setListLoading, setSessions]);
  useEffect(() => {
    return startInitialLiveSelection(refreshLists, autoFollow, setSession, reportError);
  }, [refreshLists, reportError, autoFollow, setSession]);
  useEffect(() => {
    return startLiveListPolling(refreshLists, session, autoFollow, listRequest, setSession, setDriver);
  }, [refreshLists, session, autoFollow, listRequest, setSession, setDriver]);
  useEffect(() => {
    return startLiveRecordPolling(session, clearError, setCompletedLaps, setLiveIncidents, setLivePitStops, setRecordsError);
  }, [clearError, session, setCompletedLaps, setLiveIncidents, setLivePitStops, setRecordsError]);
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
  }, [clearError, reportError, session, setStatus, setSessionDrivers, setPackets, setCompletedLaps, setLiveIncidents, setLivePitStops, setTiming, setSnapshot]);
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
      <NbCard tone="cream" className="min-w-0">
        <div className="flex min-w-0 flex-wrap items-center justify-between gap-4">
          <div className="min-w-0">
            <p className="mb-2 text-[length:var(--fs-label)] font-bold uppercase tracking-widest">RACE CONTROL / LIVE TIMING</p>
            <div className="flex min-w-0 flex-wrap items-center gap-3">
              <h1 className="min-w-0 break-words text-[length:var(--fs-h1)] font-bold uppercase">Live session</h1>
              <NbBadge status="LIVE">LIVE</NbBadge>
            </div>
            <p className="mt-2 break-words">A fresh session snapshot and MongoDB telemetry stream, updated over WebSocket.</p>
          </div>
          <span className="inline-flex min-w-0 flex-wrap items-center gap-2 border-4 border-ink px-3 py-2 text-[length:var(--fs-label)] font-bold">
            <i aria-hidden="true" className={`h-3 w-3 shrink-0 rounded-full ${status.startsWith("Connected") ? "bg-mint" : "bg-yellow"}`} />
            <span className="min-w-0 break-words">{status}</span>
          </span>
        </div>
      </NbCard>
      <DemoControls
        canManageDemos={canManageDemos}
        demoBusy={demoBusy}
        createPrimary={!deleteRace}
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
