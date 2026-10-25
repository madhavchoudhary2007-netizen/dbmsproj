"use client";

import { pretty } from "@/lib/api";
import { useDashboard } from "@/lib/use-dashboard";
import Link from "next/link";
import { ReloadButton } from "@/components/ui";
import { NbCard } from "@/components/nb/card";
import { NbStat } from "@/components/nb/stat";
import { NbButton } from "@/components/nb/button";
import { NbState } from "@/components/nb/state";

export function Dashboard() {
  const { data, health, err, healthError, state, fetchData } = useDashboard();
  return (
    <>
      <div className="dashboard-overview-grid">
        <div className="dashboard-overview-main">
          <NbCard tone="cream" shadow={8} className="dashboard-hero">
            <div className="dashboard-hero-copy">
              <div className="eyebrow">CONTROL ROOM / OVERVIEW</div>
              <div className="dashboard-hero-title-wrap">
                <h1 className="dashboard-hero-title">Race operations</h1>
                <span className="dashboard-hero-title-stroke" aria-hidden="true">
                  RACE OPERATIONS
                </span>
              </div>
              <p>Competition status and service health from the ApexGrid API.</p>
            </div>
            <div className="dashboard-hero-actions">
              <ReloadButton onClick={fetchData} />
              <Link className="nb-plinth dashboard-live-link" href="/live" data-primary="true">
                <span className="nb-face">Open live timing</span>
              </Link>
            </div>
          </NbCard>
          {data && (
            <NbCard tone="paper" shadow={8} className="dashboard-context-card">
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
            </NbCard>
          )}
        </div>
        {data && (
          <NbCard tone="violet" shadow={8} className="dashboard-health-card">
            <div className="panel-heading">
              <div>
                <div className="eyebrow">SERVICE HEALTH</div>
                <h2>Platform status</h2>
              </div>
            </div>
            {Object.entries(health?.services || {}).map(([k, v]) => (
              <div className="detail-row" key={k}>
                <span>{k}</span>
                <b className={["up", "healthy"].includes(String(v).toLowerCase()) ? "green" : "red"}>{pretty(v)}</b>
              </div>
            ))}
            {health && (
              <div className="detail-row">
                <span>overall</span>
                <b className={["ok", "healthy", "up"].includes(String(health.status).toLowerCase()) ? "green" : "red"}>
                  {pretty(health.status)}
                </b>
              </div>
            )}
          </NbCard>
        )}
      </div>
      <NbState
        state={state}
        className={state.status === "partial" && (err || healthError) ? "dashboard-summary error" : "dashboard-summary"}
        empty="No dashboard data is currently available."
        nextAction={<NbButton variant="secondary" onClick={fetchData}>Reload dashboard data</NbButton>}
        shownCount={4}
        partialSummary="Showing 4 dashboard metrics"
        sourceMessage={state.status === "partial" ? state.filter.label : healthError || err || undefined}
        partialActionLabel="Try again"
        partialActionAriaLabel="Try again"
      >
        {(dashboard) => (
          <div className="mb-4 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {([
              ["active_sessions", dashboard.active_sessions, "red", -2],
              ["scheduled_events", dashboard.scheduled_events, "yellow", 2],
              ["open_incidents", dashboard.open_incidents, "violet", -2],
              ["drivers", dashboard.drivers, "mint", 2],
            ] as const).map(([k, v, tone, tilt]) => (
              <NbStat
                key={String(k)}
                label={String(k).replaceAll("_", " ")}
                value={pretty(v)}
                delta="API reported"
                className="stat-card [&_dd]:text-5xl"
                tone={tone}
                stickerTilt={tilt}
              />
            ))}
            <NbCard tone="paper" shadow={8} className="col-span-full min-w-0">
              <div className="eyebrow">NEXT UP</div>
              {dashboard.next_event ? (
                <div className="min-w-0 [overflow-wrap:anywhere]">
                  <h2>{pretty(dashboard.next_event.name)}</h2>
                  <p>{pretty(dashboard.next_event.circuit_name)}</p>
                  <p>{pretty(dashboard.next_event.scheduled_at)}</p>
                </div>
              ) : <p>No upcoming event.</p>}
              <Link className="nb-plinth mt-4 inline-flex min-h-11 min-w-11 items-center justify-center border-4 border-ink bg-paper px-4 py-2 font-bold" href="/sessions">
                View sessions
              </Link>
            </NbCard>
          </div>
        )}
      </NbState>
    </>
  );
}
