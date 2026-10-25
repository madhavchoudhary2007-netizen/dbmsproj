import { useCallback, useEffect, useState } from "react";
import { api, asArray, listAll, Row } from "@/lib/api";
import { useAuth } from "@/components/auth";
import { useStewardingLicences, useStewardingPenalties } from "@/lib/use-stewarding-records";

export function useStewardDesk() {
  const [rows, setRows] = useState<Row[]>([]),
    [drivers, setDrivers] = useState<Row[]>([]),
    [sessions, setSessions] = useState<Row[]>([]),
    [error, setError] = useState(""),
    [loading, setLoading] = useState(true),
    [active, setActive] = useState<Row | undefined>(),
    [busy, setBusy] = useState(false),
    [notes, setNotes] = useState(""),
    [points, setPoints] = useState(0),
    [seconds, setSeconds] = useState(0),
    [grid, setGrid] = useState(0),
    [message, setMessage] = useState("");
  const { user } = useAuth();
  const penalties = useStewardingPenalties();
  const licences = useStewardingLicences();
  const reloadPenalties = penalties.reload;
  const reloadLicences = licences.reload;
  const canSteward = user?.role === "ADMIN" || user?.role === "STEWARD";
  const load = useCallback(async (refreshRecords = true) => {
    setLoading(true);
    try {
      const [i, d, s] = await Promise.all([
        listAll("/incidents"),
        listAll("/drivers"),
        listAll("/sessions"),
      ]);
      setRows(asArray(i));
      setDrivers(asArray(d));
      setSessions(asArray(s));
      setError("");
      if (refreshRecords) await Promise.all([reloadPenalties(), reloadLicences()]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to load incidents");
    } finally {
      setLoading(false);
    }
  }, [reloadLicences, reloadPenalties]);
  useEffect(() => {
    void load(false);
  }, [load]);
  const report = async (v: Row) => {
    setBusy(true);
    try {
      await api("/incidents", { method: "POST", body: JSON.stringify(v) });
      setActive(undefined);
      await load();
    } finally {
      setBusy(false);
    }
  };
  const decide = async (approve: boolean) => {
    if (!active) return;
    setBusy(true);
    setMessage("");
    try {
      const result = await api<{
        driver?: { season_points?: number | string; eligibility?: string };
      }>(`/incidents/${active.id}/decision`, {
        method: "POST",
        body: JSON.stringify({
          approve,
          notes,
          points,
          time_seconds: seconds,
          grid_places: grid,
        }),
      });
      setMessage(
        `Decision recorded. Current driver points: ${result.driver?.season_points ?? "reported by API"} · eligibility: ${result.driver?.eligibility ?? "updated by database trigger"}`,
      );
      setActive(undefined);
      setNotes("");
      setPoints(0);
      setSeconds(0);
      setGrid(0);
      await load();
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Decision failed");
    } finally {
      setBusy(false);
    }
  };
  return {
    rows,
    drivers,
    sessions,
    error,
    loading,
    active,
    setActive,
    busy,
    notes,
    setNotes,
    points,
    setPoints,
    seconds,
    setSeconds,
    grid,
    setGrid,
    message,
    records: { penalties, licences },
    canSteward,
    load,
    report,
    decide,
  };
}
