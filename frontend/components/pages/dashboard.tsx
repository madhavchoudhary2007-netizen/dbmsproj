"use client";

import { pretty } from "@/lib/api";
import { useDashboard } from "@/lib/use-dashboard";
import { PageHeader, ReloadButton, StateMessage } from "@/components/ui";

export function Dashboard() {
  const { data, health, err, load, fetchData } = useDashboard();
  return (
    <>
      <PageHeader
        eyebrow="CONTROL ROOM / OVERVIEW"
        title="Race operations"
        description="Competition status and service health from the ApexGrid API."
        action={<ReloadButton onClick={fetchData} data-primary="true" />}
      />
      <StateMessage error={err} loading={load} retry={fetchData} />
      {data && (
        <>
          <div className="stat-grid">
            {[
              ["active_sessions", data.active_sessions],
              ["scheduled_events", data.scheduled_events],
              ["open_incidents", data.open_incidents],
              ["drivers", data.drivers],
            ].map(([k, v]) => (
              <div className="stat-card" key={String(k)}>
                <span>{String(k).replaceAll("_", " ")}</span>
                <b>{pretty(v)}</b>
                <small>API reported</small>
              </div>
            ))}
          </div>
          <div className="dashboard-grid">
            <div className="panel">
              <div className="panel-heading">
                <div>
                  <div className="eyebrow">CURRENT CONTEXT</div>
                  <h2>Race weekend</h2>
                </div>
                <span className="live-badge">
                  <i /> LIVE DATA
                </span>
              </div>
              {data.active_session ? (
                Object.entries(data.active_session).map(([k, v]) => (
                  <div className="detail-row" key={k}>
                    <span>{k.replaceAll("_", " ")}</span>
                    <b>{pretty(v)}</b>
                  </div>
                ))
              ) : (
                <p className="muted">
                  No active or paused session is currently returned by the API.
                </p>
              )}
            </div>
            <div className="panel">
              <div className="panel-heading">
                <div>
                  <div className="eyebrow">SERVICE HEALTH</div>
                  <h2>Platform status</h2>
                </div>
              </div>
              {Object.entries(health?.services || {}).map(([k, v]) => (
                <div className="detail-row" key={k}>
                  <span>{k}</span>
                  <b className={v === "up" ? "green" : ""}>{pretty(v)}</b>
                </div>
              ))}
              {health && (
                <div className="detail-row">
                  <span>overall</span>
                  <b>{pretty(health.status)}</b>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </>
  );
}
