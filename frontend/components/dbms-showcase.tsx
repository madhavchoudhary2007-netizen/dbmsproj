"use client";

import { useCallback, useEffect, useState } from "react";
import { NbButton } from "@/components/nb/button";
import { NbCard } from "@/components/nb/card";
import { NbBadge } from "@/components/nb/badge";
import { NbTabs } from "@/components/nb/tabs";
import {
  fetchIsolationDemo, triggerDeadlockDemo, fetchViews, triggerRefreshStandingsMV,
  fetchAnalyticsGaps, fetchExplainPlan, fetchAuditLog, fetchSecurity,
  type IsolationDemoResponse, type DeadlockDemoResponse, type ViewsResponse,
  type RefreshStandingsMVResponse, type AnalyticsGapsResponse, type ExplainPlanResponse,
  type AuditLogResponse, type DBMSSecurityResponse,
} from "@/lib/dbms-showcase";

type TabKey = "isolation" | "deadlock" | "views" | "analytics" | "plans" | "audit";
const TABS = [
  { id: "isolation", label: "Isolation" }, { id: "deadlock", label: "Deadlock" },
  { id: "views", label: "Views & MV" }, { id: "analytics", label: "Analytics Gaps" },
  { id: "plans", label: "Query Plans" }, { id: "audit", label: "Audit & Security" },
] as const;

function StateMsg({ type, text }: { type: "loading" | "error" | "empty" | "partial"; text: string }) {
  const bg = type === "loading" ? "bg-cream" : type === "error" ? "bg-red" : type === "partial" ? "bg-yellow" : "bg-paper";
  return <div role={type === "error" ? "alert" : "status"} className={`border-4 border-ink ${bg} p-4 font-mono text-xs font-bold text-ink`}>{text}</div>;
}

export function DbmsShowcase() {
  const [tab, setTab] = useState<TabKey>("isolation");
  const [isoLevel, setIsoLevel] = useState<"read_committed" | "repeatable_read" | "serializable">("read_committed");
  const [isoData, setIsoData] = useState<IsolationDemoResponse | null>(null), [isoLoading, setIsoLoading] = useState(false), [isoError, setIsoError] = useState<string | null>(null);
  const [deadlockData, setDeadlockData] = useState<DeadlockDemoResponse | null>(null), [deadlockLoading, setDeadlockLoading] = useState(false), [deadlockError, setDeadlockError] = useState<string | null>(null);
  const [viewsData, setViewsData] = useState<ViewsResponse | null>(null), [viewsLoading, setViewsLoading] = useState(false), [viewsError, setViewsError] = useState<string | null>(null);
  const [refreshMv, setRefreshMv] = useState<RefreshStandingsMVResponse | null>(null), [refreshLoading, setRefreshLoading] = useState(false);
  const [sessionId, setSessionId] = useState("00000000-0000-0000-0000-000000000001"), [gapsData, setGapsData] = useState<AnalyticsGapsResponse | null>(null), [gapsLoading, setGapsLoading] = useState(false), [gapsError, setGapsError] = useState<string | null>(null);
  const [planQuery, setPlanQuery] = useState("standings_rollup"), [analyze, setAnalyze] = useState(true), [planData, setPlanData] = useState<ExplainPlanResponse | null>(null), [planLoading, setPlanLoading] = useState(false), [planError, setPlanError] = useState<string | null>(null);
  const [auditTable, setAuditTable] = useState(""), [auditData, setAuditData] = useState<AuditLogResponse | null>(null), [securityData, setSecurityData] = useState<DBMSSecurityResponse | null>(null), [auditLoading, setAuditLoading] = useState(false), [auditError, setAuditError] = useState<string | null>(null);

  const runIsolation = useCallback(async (lvl?: "read_committed" | "repeatable_read" | "serializable") => {
    setIsoLoading(true); setIsoError(null);
    try { setIsoData(await fetchIsolationDemo(lvl ?? isoLevel)); } catch (e) { setIsoError(e instanceof Error ? e.message : String(e)); } finally { setIsoLoading(false); }
  }, [isoLevel]);

  const runDeadlock = async () => {
    setDeadlockLoading(true); setDeadlockError(null);
    try { setDeadlockData(await triggerDeadlockDemo()); } catch (e) { setDeadlockError(e instanceof Error ? e.message : String(e)); } finally { setDeadlockLoading(false); }
  };

  const loadViews = useCallback(async () => {
    setViewsLoading(true); setViewsError(null);
    try { setViewsData(await fetchViews()); } catch (e) { setViewsError(e instanceof Error ? e.message : String(e)); } finally { setViewsLoading(false); }
  }, []);

  const handleRefreshMv = async () => {
    setRefreshLoading(true);
    try { setRefreshMv(await triggerRefreshStandingsMV()); } catch (e) { setViewsError(e instanceof Error ? e.message : String(e)); } finally { setRefreshLoading(false); }
  };

  const runGaps = useCallback(async (sid?: string) => {
    setGapsLoading(true); setGapsError(null);
    try { setGapsData(await fetchAnalyticsGaps(sid ?? sessionId)); } catch (e) { setGapsError(e instanceof Error ? e.message : String(e)); } finally { setGapsLoading(false); }
  }, [sessionId]);

  const runExplain = useCallback(async (q?: string, a?: boolean) => {
    setPlanLoading(true); setPlanError(null);
    try { setPlanData(await fetchExplainPlan(q ?? planQuery, a ?? analyze)); } catch (e) { setPlanError(e instanceof Error ? e.message : String(e)); } finally { setPlanLoading(false); }
  }, [planQuery, analyze]);

  const loadAuditAndSecurity = useCallback(async (tbl?: string) => {
    setAuditLoading(true); setAuditError(null);
    try {
      const [aRes, sRes] = await Promise.all([fetchAuditLog(tbl ?? (auditTable || undefined)), fetchSecurity()]);
      setAuditData(aRes); setSecurityData(sRes);
    } catch (e) { setAuditError(e instanceof Error ? e.message : String(e)); } finally { setAuditLoading(false); }
  }, [auditTable]);

  useEffect(() => {
    if (tab === "isolation") void runIsolation();
    else if (tab === "views") void loadViews();
    else if (tab === "analytics") void runGaps();
    else if (tab === "plans") void runExplain();
    else if (tab === "audit") void loadAuditAndSecurity();
  }, [tab, runIsolation, loadViews, runGaps, runExplain, loadAuditAndSecurity]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <span className="font-mono text-xs font-bold uppercase tracking-wider text-ink/70">DATABASE ENGINEERING / DBMS SHOWCASE</span>
        <h1 className="font-sans text-2xl font-black uppercase text-ink md:text-3xl">PostgreSQL & Database Capabilities</h1>
      </div>
      <NbTabs label="DBMS Showcase Capabilities" items={TABS} value={tab} onChange={(val) => setTab(val as TabKey)} />
      <NbCard tone="paper" shadow={8} className="p-6">
        {tab === "isolation" && (
          <div className="space-y-6">
            <div className="flex flex-wrap items-center gap-4">
              <label className="font-mono text-xs font-bold uppercase text-ink">
                Isolation Level
                <select value={isoLevel} onChange={(e) => setIsoLevel(e.target.value as "read_committed" | "repeatable_read" | "serializable")} className="ml-2 min-h-[44px] min-w-[44px] border-4 border-ink bg-paper p-2 font-mono text-xs font-bold">
                  <option value="read_committed">read_committed</option><option value="repeatable_read">repeatable_read</option><option value="serializable">serializable</option>
                </select>
              </label>
              <NbButton data-primary variant="primary" busy={isoLoading} onClick={() => void runIsolation()}>Run Isolation Demo</NbButton>
              {isoData?.anomaly_detected ? <NbBadge status="REJECTED">Non-repeatable Read Detected</NbBadge> : isoData ? <NbBadge status="FINISHED">Anomaly Prevented</NbBadge> : null}
            </div>
            {isoLoading && <StateMsg type="loading" text="Running transaction isolation simulation..." />}
            {isoError && <StateMsg type="error" text={isoError} />}
            {!isoLoading && !isoError && !isoData && <StateMsg type="empty" text="Choose an isolation level and click Run Isolation Demo." />}
            {isoData && (
              <div className="grid gap-4 md:grid-cols-2">
                <div className="border-4 border-ink bg-cream p-4">
                  <span className="font-mono text-xs font-bold uppercase text-ink">Observed Reads</span>
                  {isoData.observed_reads.length === 0 ? <StateMsg type="partial" text="No intermediate reads recorded." /> : <pre className="mt-2 max-h-64 overflow-x-auto border-2 border-ink bg-paper p-3 font-mono text-xs">{JSON.stringify(isoData.observed_reads, null, 2)}</pre>}
                </div>
                <div className="border-4 border-ink bg-cream p-4">
                  <span className="font-mono text-xs font-bold uppercase text-ink">Timeline Steps</span>
                  {isoData.timeline.length === 0 ? <StateMsg type="partial" text="Timeline empty." /> : <ol className="mt-2 max-h-64 space-y-1 overflow-y-auto font-mono text-xs">{isoData.timeline.map((step, idx) => <li key={idx} className="border-b-2 border-ink/20 pb-1">{idx + 1}. {JSON.stringify(step)}</li>)}</ol>}
                </div>
              </div>
            )}
          </div>
        )}
        {tab === "deadlock" && (
          <div className="space-y-6">
            <div className="flex flex-wrap items-center gap-4">
              <NbButton data-primary variant="danger" busy={deadlockLoading} onClick={() => void runDeadlock()}>Simulate Deadlock</NbButton>
              {deadlockData && <span className="border-4 border-ink bg-yellow px-3 py-2 font-mono text-sm font-bold">SQLSTATE {deadlockData.sqlstate}</span>}
              {deadlockData && <span className="font-mono text-xs font-bold uppercase">Aborted Tx: #{String(deadlockData.aborted_transaction)}</span>}
            </div>
            {deadlockLoading && <StateMsg type="loading" text="Simulating concurrent cyclic transaction locks..." />}
            {deadlockError && <StateMsg type="error" text={deadlockError} />}
            {!deadlockLoading && !deadlockError && !deadlockData && <StateMsg type="empty" text="Click Simulate Deadlock to trigger a 40P01 concurrent lock cycle." />}
            {deadlockData && (
              <div className="border-4 border-ink bg-cream p-4 space-y-3">
                <span className="font-mono text-xs font-bold uppercase text-ink">Deadlock Diagnostics</span>
                <p className="font-mono text-sm font-bold text-red">{deadlockData.error_message ?? "40P01: deadlock detected"}</p>
                <pre className="max-h-64 overflow-x-auto border-2 border-ink bg-paper p-3 font-mono text-xs">{JSON.stringify(deadlockData.details, null, 2)}</pre>
              </div>
            )}
          </div>
        )}
        {tab === "views" && (
          <div className="space-y-6">
            <div className="flex flex-wrap items-center gap-4">
              <NbButton busy={refreshLoading} onClick={() => void handleRefreshMv()}>Refresh Standings MV</NbButton>
              {refreshMv && <NbBadge status={refreshMv.refreshed ? "FINISHED" : "REJECTED"}>{refreshMv.refreshed ? `Refreshed in ${refreshMv.duration_ms ?? 0}ms` : "Refresh Failed"}</NbBadge>}
            </div>
            {viewsLoading && <StateMsg type="loading" text="Fetching database view definitions..." />}
            {viewsError && <StateMsg type="error" text={viewsError} />}
            {!viewsLoading && !viewsError && viewsData?.views.length === 0 && <StateMsg type="empty" text="No views found in catalog." />}
            {viewsData && viewsData.views.length > 0 && (
              <div className="space-y-4">
                {viewsData.views.map((v) => (
                  <div key={v.name} className="border-4 border-ink bg-cream p-4 space-y-2">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="font-mono text-sm font-bold">{v.name}</span>
                      <NbBadge status={v.view_type === "materialized_view" ? "PAUSED" : "APPROVED"}>{v.view_type}</NbBadge>
                    </div>
                    <pre className="max-h-48 overflow-x-auto whitespace-pre-wrap border-2 border-ink bg-paper p-3 font-mono text-xs">{v.definition}</pre>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
        {tab === "analytics" && (
          <div className="space-y-6">
            <div className="flex flex-wrap items-center gap-4">
              <label className="font-mono text-xs font-bold uppercase text-ink">
                Session ID
                <input value={sessionId} onChange={(e) => setSessionId(e.target.value)} className="ml-2 min-h-[44px] min-w-[44px] border-4 border-ink bg-paper px-3 font-mono text-xs" />
              </label>
              <NbButton busy={gapsLoading} onClick={() => void runGaps(sessionId)}>Calculate Gaps</NbButton>
            </div>
            {gapsLoading && <StateMsg type="loading" text="Running window analytics query..." />}
            {gapsError && <StateMsg type="error" text={gapsError} />}
            {gapsData && (
              <div className="space-y-4">
                <div className="border-4 border-ink bg-cream p-4 space-y-2">
                  <span className="font-mono text-xs font-bold uppercase text-ink">SQL Window Specification</span>
                  <pre className="max-h-36 overflow-x-auto whitespace-pre-wrap border-2 border-ink bg-paper p-3 font-mono text-xs">{gapsData.sql}</pre>
                </div>
                {gapsData.gaps.length === 0 ? <StateMsg type="partial" text="No gap telemetry records found for this session." /> : (
                  <div className="overflow-x-auto border-4 border-ink bg-paper">
                    <table className="w-full text-left font-mono text-xs">
                      <thead className="border-b-4 border-ink bg-cream">
                        <tr>{["Driver", "Lap", "Pos", "Gap to Leader", "Interval", "Rolling Avg"].map((h) => <th key={h} className="border-r-2 border-ink p-2 last:border-r-0">{h}</th>)}</tr>
                      </thead>
                      <tbody>
                        {gapsData.gaps.map((g, idx) => (
                          <tr key={idx} className="border-b-2 border-ink/20">
                            <td className="border-r-2 border-ink/20 p-2 font-bold">{g.driver_name ?? g.driver_id ?? "—"}</td>
                            <td className="border-r-2 border-ink/20 p-2">{g.lap}</td>
                            <td className="border-r-2 border-ink/20 p-2">{g.position}</td>
                            <td className="border-r-2 border-ink/20 p-2">{g.gap_to_leader_ms != null ? `${g.gap_to_leader_ms} ms` : "—"}</td>
                            <td className="border-r-2 border-ink/20 p-2">{g.interval_ms != null ? `${g.interval_ms} ms` : "—"}</td>
                            <td className="p-2">{g.rolling_avg_ms != null ? `${g.rolling_avg_ms} ms` : "—"}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
        {tab === "plans" && (
          <div className="space-y-6">
            <div className="flex flex-wrap items-center gap-4">
              <label className="font-mono text-xs font-bold uppercase text-ink">
                Query
                <select value={planQuery} onChange={(e) => setPlanQuery(e.target.value)} className="ml-2 min-h-[44px] min-w-[44px] border-4 border-ink bg-paper p-2 font-mono text-xs font-bold">
                  <option value="standings_rollup">standings_rollup</option><option value="leaderboard">leaderboard</option><option value="licence">licence</option>
                </select>
              </label>
              <label className="inline-flex min-h-[44px] min-w-[44px] items-center gap-2 font-mono text-xs font-bold uppercase cursor-pointer">
                <input type="checkbox" checked={analyze} onChange={(e) => setAnalyze(e.target.checked)} className="h-4 w-4 border-2 border-ink accent-yellow" />
                ANALYZE
              </label>
              <NbButton busy={planLoading} onClick={() => void runExplain()}>Explain Query</NbButton>
            </div>
            {planLoading && <StateMsg type="loading" text="Generating EXPLAIN plan tree..." />}
            {planError && <StateMsg type="error" text={planError} />}
            {planData && (
              <div className="space-y-4">
                {planData.raw_sql && <pre className="max-h-32 overflow-x-auto whitespace-pre-wrap border-2 border-ink bg-cream p-3 font-mono text-xs">{planData.raw_sql}</pre>}
                <pre className="max-h-96 overflow-x-auto border-4 border-ink bg-paper p-4 font-mono text-xs">{JSON.stringify(planData.plan, null, 2)}</pre>
              </div>
            )}
          </div>
        )}
        {tab === "audit" && (
          <div className="space-y-6">
            <div className="flex flex-wrap items-center gap-4">
              <label className="font-mono text-xs font-bold uppercase text-ink">
                Filter Table
                <select value={auditTable} onChange={(e) => { setAuditTable(e.target.value); void loadAuditAndSecurity(e.target.value); }} className="ml-2 min-h-[44px] min-w-[44px] border-4 border-ink bg-paper p-2 font-mono text-xs font-bold">
                  <option value="">(All Tables)</option><option value="penalties">penalties</option><option value="sessions">sessions</option><option value="championships">championships</option>
                </select>
              </label>
              <NbButton busy={auditLoading} onClick={() => void loadAuditAndSecurity()}>Refresh Audit & Security</NbButton>
            </div>
            {auditLoading && <StateMsg type="loading" text="Loading audit trails and catalog permissions..." />}
            {auditError && <StateMsg type="error" text={auditError} />}
            {auditData && (
              <div className="border-4 border-ink bg-cream p-4 space-y-2">
                <span className="font-mono text-xs font-bold uppercase text-ink">Audit Logs ({auditData.audit_logs.length})</span>
                {auditData.audit_logs.length === 0 ? <StateMsg type="empty" text="No audit records found." /> : (
                  <div className="overflow-x-auto border-2 border-ink bg-paper">
                    <table className="w-full text-left font-mono text-xs">
                      <thead className="border-b-2 border-ink bg-cream">
                        <tr>{["Table", "Operation", "Actor", "Timestamp"].map((h) => <th key={h} className="border-r-2 border-ink p-2 last:border-r-0">{h}</th>)}</tr>
                      </thead>
                      <tbody>
                        {auditData.audit_logs.map((row) => (
                          <tr key={row.id} className="border-b-2 border-ink/20">
                            <td className="border-r-2 border-ink/20 p-2 font-bold">{row.table_name}</td>
                            <td className="border-r-2 border-ink/20 p-2"><span className="border border-ink bg-yellow px-1 font-bold">{row.op}</span></td>
                            <td className="border-r-2 border-ink/20 p-2">{row.actor ?? "system"}</td>
                            <td className="p-2">{row.at}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
            {securityData && (
              <div className="grid gap-4 md:grid-cols-2">
                <div className="border-4 border-ink bg-cream p-4 space-y-2">
                  <span className="font-mono text-xs font-bold uppercase text-ink">Role Grants ({securityData.grants.length})</span>
                  {securityData.grants.length === 0 ? <StateMsg type="empty" text="No role grants." /> : <ul className="max-h-48 space-y-1 overflow-y-auto font-mono text-xs">{securityData.grants.map((g, idx) => <li key={idx} className="border-b-2 border-ink/20 pb-1 font-bold">{g.grantee}: {g.privilege_type} ON {g.table_name}</li>)}</ul>}
                </div>
                <div className="border-4 border-ink bg-cream p-4 space-y-2">
                  <span className="font-mono text-xs font-bold uppercase text-ink">RLS Policies ({securityData.policies.length})</span>
                  {securityData.policies.length === 0 ? <StateMsg type="empty" text="No RLS policies." /> : <ul className="max-h-48 space-y-1 overflow-y-auto font-mono text-xs">{securityData.policies.map((p, idx) => <li key={idx} className="border-b-2 border-ink/20 pb-1">{p.policyname} ON {p.tablename} ({p.cmd ?? "ALL"})</li>)}</ul>}
                </div>
              </div>
            )}
          </div>
        )}
      </NbCard>
    </div>
  );
}
