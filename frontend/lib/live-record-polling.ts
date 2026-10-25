import { api, asArray, type Row } from "./api";

export function startLiveRecordPolling(
  session: string,
  clearError: (source?: "snapshot") => void,
  setCompletedLaps: (rows: Row[]) => void,
  setLiveIncidents: (rows: Row[]) => void,
  setLivePitStops: (rows: Row[]) => void,
  setRecordsError: (message: string) => void,
): (() => void) | undefined {
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
}
