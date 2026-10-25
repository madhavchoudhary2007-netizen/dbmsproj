import { api, type Row } from "./api";

export interface LiveDemoActionContext {
  session: string;
  deleteRace: Row | null;
  refreshLists(): Promise<{ sessionRows: Row[]; raceRows: Row[]; current: boolean }>;
  clearError(source?: "lists" | "snapshot" | "demo"): void;
  reportError(source: "lists" | "snapshot" | "demo", message: string): void;
  setDemoBusy(busy: boolean): void;
  setDemoMessage(message: string): void;
  setSession(session: string): void;
  setDriver(driver: string): void;
  setPackets(packets: Row[]): void;
  setTiming(timing: { cars: Row[]; safety_car: boolean }): void;
  setSnapshot(snapshot: null): void;
  setStatus(status: string): void;
  setDeleteRace(race: Row | null): void;
}

export function createLiveDemoActions(context: LiveDemoActionContext, guard: { current: boolean } = { current: false }) {
  const {
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
  } = context;

  const createDemoRace = async () => {
    if (guard.current) return;
    guard.current = true;
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
      guard.current = false;
    }
  };

  const removeDemoRace = async () => {
    if (!deleteRace) return;
    if (guard.current) return;
    guard.current = true;
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
      guard.current = false;
    }
  };

  return { createDemoRace, removeDemoRace };
}
