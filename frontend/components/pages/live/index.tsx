"use client";
import { useCallback, useEffect } from "react";
import { TriangleAlert } from "lucide-react";
import { refreshLiveLists } from "@/lib/live-list-refresh";
import { createLiveDemoActions } from "@/lib/live-demo-actions";
import { deriveLiveTimingData } from "@/lib/live-timing-data";
import { startLiveRecordPolling } from "@/lib/live-record-polling";
import { startInitialLiveSelection, startLiveListPolling } from "@/lib/live-list-polling";
import { startLiveStream } from "@/lib/live-stream";
import { PageHeader } from "@/components/ui";
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
    snapshot, setSnapshot, timing, setTiming, status, setStatus, error, setError,
    demoBusy, setDemoBusy, showCompletedDemos, setShowCompletedDemos,
    showAllLaps, setShowAllLaps, deleteRace, setDeleteRace, demoMessage,
    setDemoMessage, canManageDemos, autoFollow, listRequest, reportError, clearError,
  } = useLiveTimingState();
  const refreshLists = useCallback(async () => {
    return refreshLiveLists(listRequest, setSessions, setDemoRaces, clearError);
  }, [clearError, listRequest, setDemoRaces, setSessions]);
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
