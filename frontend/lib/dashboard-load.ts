import { api } from "./api";
import { DashboardData, readDashboardFeed } from "./dashboard-feed";

export interface HealthData {
  services?: Record<string, unknown>;
  status?: unknown;
  [key: string]: unknown;
}

export async function loadDashboardSources(
  force: boolean,
  signal?: AbortSignal,
): Promise<{
  dashboard: PromiseSettledResult<DashboardData>;
  health: PromiseSettledResult<HealthData>;
}> {
  const [dashboard, health] = await Promise.allSettled([
    readDashboardFeed({ force, signal }),
    api<HealthData>("/health", { signal }),
  ]);
  return { dashboard, health };
}

export type DashboardClassification =
  | { status: "loading" }
  | { status: "empty"; reason: "no-data" }
  | { status: "populated"; data: DashboardData }
  | { status: "error"; error: { message: string; retryable: boolean } }
  | { status: "partial"; data: DashboardData; filter: { label: string }; totalCount: number };

export function deriveDashboardState(
  data: DashboardData | null,
  loading: boolean,
  error: string,
  healthError: string,
): DashboardClassification {
  if (loading) return { status: "loading" };
  if (!data && error)
    return { status: "error", error: { message: error, retryable: true } };
  if (!data) return { status: "empty", reason: "no-data" };

  const metrics = [data.active_sessions, data.scheduled_events, data.open_incidents, data.drivers];
  if (metrics.every((value) => value === undefined || value === null))
    return { status: "empty", reason: "no-data" };

  const causes = [
    error ? `Dashboard data unavailable: ${error}` : "",
    healthError ? `Service health unavailable: ${healthError}` : "",
  ].filter(Boolean);
  if (causes.length)
    return { status: "partial", data, filter: { label: causes.join("; ") }, totalCount: 4 };
  return { status: "populated", data };
}
