import { useCallback, useEffect, useRef, useState } from "react";
import { DashboardData } from "./dashboard-feed";
import { ViewState } from "./data-state";
import { deriveDashboardState, loadDashboardSources, HealthData } from "./dashboard-load";

export type { HealthData } from "./dashboard-load";

function messageOf(reason: unknown): string {
  return reason instanceof Error ? reason.message : String(reason);
}

export function useDashboard(): {
  data: DashboardData | null;
  health: HealthData | null;
  err: string;
  healthError: string;
  load: boolean;
  state: ViewState<DashboardData>;
  fetchData: () => void;
} {
  const [data, setData] = useState<DashboardData | null>(null),
    [health, setHealth] = useState<HealthData | null>(null),
    [err, setErr] = useState(""),
    [healthError, setHealthError] = useState(""),
    [load, setLoad] = useState(true);
  const initialLoad = useRef(true);
  const request = useRef<AbortController | null>(null);
  const generation = useRef(0);
  const fetchData = useCallback(() => {
    if (request.current) return;
    const controller = new AbortController();
    request.current = controller;
    const current = ++generation.current;
    const useCache = initialLoad.current;
    initialLoad.current = false;
    setLoad(true);
    setErr("");
    setHealthError("");
    void loadDashboardSources(!useCache, controller.signal).then((results) => {
      if (controller.signal.aborted || generation.current !== current) return;
      if (results.dashboard.status === "fulfilled") {
        setData(results.dashboard.value);
        setErr("");
      } else setErr(messageOf(results.dashboard.reason));
      if (results.health.status === "fulfilled") {
        setHealth(results.health.value);
        setHealthError("");
      } else setHealthError(messageOf(results.health.reason));
      setLoad(false);
      request.current = null;
    });
  }, []);
  useEffect(() => {
    fetchData();
    return () => {
      generation.current += 1;
      request.current?.abort();
      request.current = null;
    };
  }, [fetchData]);
  const classification = deriveDashboardState(data, load, err, healthError);
  let state: ViewState<DashboardData>;
  if (classification.status === "error")
    state = { ...classification, retry: fetchData };
  else if (classification.status === "partial")
    state = { ...classification, filter: { ...classification.filter, clear: fetchData } };
  else state = classification;
  return { data, health, err, healthError, load, state, fetchData };
}
