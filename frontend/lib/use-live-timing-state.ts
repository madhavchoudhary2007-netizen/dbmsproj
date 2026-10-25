import { useCallback, useRef, useState } from "react";
import { Row } from "@/lib/api";
import { useAuth } from "@/components/auth";

export function useLiveTimingState() {
  const [sessions, setSessions] = useState<Row[]>([]),
    [demoRaces, setDemoRaces] = useState<Row[]>([]),
    [listLoading, setListLoading] = useState(true),
    [listError, setListError] = useState(""),
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
  const demoInFlight = useRef(false);
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
  return {
    sessions, setSessions, demoRaces, setDemoRaces, listLoading, listError,
    setListLoading, setListError, session, setSession,
    sessionDrivers, setSessionDrivers, driver, setDriver, packets, setPackets,
    completedLaps, setCompletedLaps, liveIncidents, setLiveIncidents,
    livePitStops, setLivePitStops, recordsError, setRecordsError,
    snapshot, setSnapshot, timing, setTiming, status, setStatus, error, setError,
    demoBusy, setDemoBusy, showCompletedDemos, setShowCompletedDemos,
    showAllLaps, setShowAllLaps, deleteRace, setDeleteRace, demoMessage,
    setDemoMessage, canManageDemos, autoFollow, demoInFlight, listRequest, reportError, clearError,
  };
}
