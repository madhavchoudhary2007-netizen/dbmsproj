import { api, asArray, type Row } from "./api";

export function startLiveRecordPolling(
  session: string,
  clearError: (source?: "snapshot") => void,
  setCompletedLaps: (rows: Row[]) => void,
  setLiveIncidents: (rows: Row[]) => void,
  setLivePitStops: (rows: Row[]) => void,
  setRecordsError: (message: string) => void,
  options: { setLoading?: (value: boolean) => void; retryRef?: { current: (() => void) | null } } = {},
): (() => void) | undefined {
  if (!session) { options.setLoading?.(false); clearError("snapshot"); setCompletedLaps([]); setLiveIncidents([]); setLivePitStops([]); setRecordsError(""); return; }
  let alive = true;
  setCompletedLaps([]);
  setLiveIncidents([]);
  setLivePitStops([]);
  setRecordsError("");
  clearError("snapshot");
  let timer: ReturnType<typeof setTimeout> | undefined;
  let generation = 0;
  const load = async (showLoading = false) => {
    if (timer) clearTimeout(timer);
    const request = ++generation;
    if (showLoading) options.setLoading?.(true);
    try {
      const value = await api<{ laps?: Row[]; incidents?: Row[]; pit_reservations?: Row[] }>(`/sessions/${session}/laps`);
      if (alive && request === generation) {
        setCompletedLaps(asArray(value.laps));
        setLiveIncidents(asArray(value.incidents));
        setLivePitStops(asArray(value.pit_reservations));
        setRecordsError("");
      }
    } catch (e) {
      if (alive && request === generation) setRecordsError(e instanceof Error ? e.message : "Unable to load lap and race-control records");
    } finally {
      if (alive && request === generation) {
        options.setLoading?.(false);
        timer = setTimeout(() => { void load(); }, 5000);
      }
    }
  };
  const retry = () => { if (alive) void load(true); };
  if (options.retryRef) options.retryRef.current = retry;
  void load(true);
  return () => { alive = false; if (options.retryRef?.current === retry) options.retryRef.current = null; if (timer) clearTimeout(timer); };
}
