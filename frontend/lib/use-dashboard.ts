import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";
import { DashboardData, readDashboardFeed } from "./dashboard-feed";

export interface HealthData {
  services?: Record<string, unknown>;
  status?: unknown;
  [key: string]: unknown;
}

export function useDashboard(): {
  data: DashboardData | null;
  health: HealthData | null;
  err: string;
  load: boolean;
  fetchData: () => void;
} {
  const [data, setData] = useState<DashboardData | null>(null),
    [health, setHealth] = useState<HealthData | null>(null),
    [err, setErr] = useState(""),
    [load, setLoad] = useState(true);
  const initialLoad = useRef(true);
  const fetchData = useCallback(() => {
    const useCache = initialLoad.current;
    initialLoad.current = false;
    setLoad(true);
    setErr("");
    Promise.all([readDashboardFeed({ force: !useCache }), api<HealthData>("/health")])
      .then(([d, h]) => {
        setData(d);
        setHealth(h);
        setErr("");
      })
      .catch((e) => setErr(e.message))
      .finally(() => setLoad(false));
  }, []);
  useEffect(() => {
    fetchData();
  }, [fetchData]);
  return { data, health, err, load, fetchData };
}
