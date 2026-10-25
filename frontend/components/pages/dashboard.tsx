"use client";

import { pretty } from "@/lib/api";
import { useDashboard } from "@/lib/use-dashboard";
import Link from "next/link";
import { ReloadButton, StateMessage } from "@/components/ui";
import { NbCard } from "@/components/nb/card";
import { NbStat } from "@/components/nb/stat";

export function Dashboard() {
  const { data, health, err, load, fetchData } = useDashboard();
  return (
    <>
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
      <StateMessage error={err} loading={load} retry={fetchData} />
      {data && (
        <>
          <div className="mb-4 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {([
              ["active_sessions", data.active_sessions, "red", -2],
              ["scheduled_events", data.scheduled_events, "yellow", 2],
              ["open_incidents", data.open_incidents, "violet", -2],
              ["drivers", data.drivers, "mint", 2],
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
