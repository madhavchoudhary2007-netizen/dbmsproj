import { api } from "@/lib/api";

export interface IsolationDemoResponse {
  level: string;
  observed_reads: Array<Record<string, unknown>>;
  anomaly_detected: boolean;
  anomaly_type: string | null;
  timeline: Array<Record<string, unknown>>;
}

export interface DeadlockDemoResponse {
  aborted_transaction: string | number;
  sqlstate: string;
  error_message: string | null;
  details: Record<string, unknown>;
}

export interface ViewDefinition {
  name: string;
  view_type: "view" | "materialized_view";
  definition: string;
}

export interface ViewsResponse {
  views: ViewDefinition[];
}

export interface RefreshStandingsMVResponse {
  refreshed: boolean;
  view_name: string;
  message: string | null;
  duration_ms: number | null;
}

export interface LapGapRecord {
  driver_id: string | null;
  driver_name: string | null;
  lap: number;
  position: number;
  gap_to_leader_ms: number | null;
  interval_ms: number | null;
  rolling_avg_ms: number | null;
}

export interface AnalyticsGapsResponse {
  session_id: string;
  gaps: LapGapRecord[];
  sql: string;
}

export interface ExplainPlanResponse {
  query_name: string | null;
  plan: Record<string, unknown> | Array<Record<string, unknown>>;
  analyze: boolean;
  buffers: boolean | null;
  raw_sql: string | null;
}

export interface AuditLogRow {
  id: number;
  table_name: string;
  op: string;
  row_pk: Record<string, unknown> | null;
  old: Record<string, unknown> | null;
  new: Record<string, unknown> | null;
  actor: string | null;
  at: string;
}

export interface AuditLogResponse {
  audit_logs: AuditLogRow[];
  total: number | null;
}

export interface RoleGrant {
  grantee: string;
  table_name: string;
  privilege_type: string;
}

export interface SecurityPolicy {
  policyname: string;
  tablename: string;
  roles: string[] | string | null;
  cmd: string | null;
}

export interface DBMSSecurityResponse {
  roles: string[];
  grants: RoleGrant[];
  policies: SecurityPolicy[];
}

export async function fetchIsolationDemo(
  level: "read_committed" | "repeatable_read" | "serializable" = "read_committed",
): Promise<IsolationDemoResponse> {
  const params = new URLSearchParams({ level });
  return api<IsolationDemoResponse>(`/dbms/isolation-demo?${params.toString()}`);
}

export async function triggerDeadlockDemo(): Promise<DeadlockDemoResponse> {
  return api<DeadlockDemoResponse>("/dbms/deadlock-demo", {
    method: "POST",
  });
}

export async function fetchViews(): Promise<ViewsResponse> {
  return api<ViewsResponse>("/dbms/views");
}

export async function triggerRefreshStandingsMV(): Promise<RefreshStandingsMVResponse> {
  return api<RefreshStandingsMVResponse>("/dbms/refresh-standings-mv", {
    method: "POST",
  });
}

export async function fetchAnalyticsGaps(
  sessionId: string,
): Promise<AnalyticsGapsResponse> {
  const params = new URLSearchParams({ session_id: sessionId });
  return api<AnalyticsGapsResponse>(`/analytics/gaps?${params.toString()}`);
}

export async function fetchExplainPlan(
  queryName?: string,
  analyze: boolean = true,
): Promise<ExplainPlanResponse> {
  const params = new URLSearchParams();
  if (analyze !== undefined) {
    params.set("analyze", String(analyze));
  }
  if (queryName) {
    params.set("query_name", queryName);
  }
  const qs = params.toString() ? `?${params.toString()}` : "";
  return api<ExplainPlanResponse>(`/dbms/explain${qs}`);
}

export async function fetchAuditLog(
  table?: string,
  limit?: number,
): Promise<AuditLogResponse> {
  const params = new URLSearchParams();
  if (table) {
    params.set("table", table);
  }
  if (limit !== undefined) {
    params.set("limit", String(limit));
  }
  const qs = params.toString() ? `?${params.toString()}` : "";
  return api<AuditLogResponse>(`/dbms/audit${qs}`);
}

export async function fetchSecurity(): Promise<DBMSSecurityResponse> {
  return api<DBMSSecurityResponse>("/dbms/security");
}
