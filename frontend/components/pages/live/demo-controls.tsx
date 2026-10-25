import type { MutableRefObject } from "react";
import { Plus, Trash2 } from "lucide-react";
import { NbBadge } from "@/components/nb/badge";
import { NbButton } from "@/components/nb/button";
import { NbCard } from "@/components/nb/card";
import { NbState } from "@/components/nb/state";
import type { Row } from "../../../lib/api";

interface DemoControlsProps {
  canManageDemos: boolean;
  demoBusy: boolean;
  createPrimary?: boolean;
  createDemoRace: () => Promise<void>;
  demoMessage: string;
  demoRaces: Row[];
  visibleDemoRaces: Row[];
  autoFollow: MutableRefObject<boolean>;
  setSession: (session: string) => void;
  setDriver: (driver: string) => void;
  setDeleteRace: (race: Row | null) => void;
  setShowCompletedDemos: (show: boolean) => void;
  showCompletedDemos: boolean;
  listLoading: boolean;
  listError: string;
  retryLists: () => void;
}

export function DemoControls({
  canManageDemos,
  demoBusy,
  createPrimary = true,
  createDemoRace,
  demoMessage,
  demoRaces,
  visibleDemoRaces,
  autoFollow,
  setSession,
  setDriver,
  setDeleteRace,
  setShowCompletedDemos,
  showCompletedDemos,
  listLoading,
  listError,
  retryLists,
}: DemoControlsProps) {
  const listState = listLoading
    ? { status: "loading" as const }
    : listError && demoRaces.length === 0
      ? { status: "error" as const, error: { message: listError, retryable: true }, retry: retryLists }
      : listError
        ? {
            status: "partial" as const,
            data: visibleDemoRaces,
            totalCount: demoRaces.length,
            filter: { label: "generated races", clear: retryLists },
          }
        : demoRaces.length === 0
          ? { status: "empty" as const, reason: "no-data" as const }
          : visibleDemoRaces.length < demoRaces.length
            ? {
                status: "partial" as const,
                data: visibleDemoRaces,
                totalCount: demoRaces.length,
                filter: { label: "recent generated races", clear: () => setShowCompletedDemos(true) },
              }
            : { status: "populated" as const, data: visibleDemoRaces };
  const showRaceCards = (races: Row[]) => (
    <>
      <div className="demo-race-list">
        {races.map((race: Row) => (
          <NbCard shadow={4} className="demo-race-row" key={String(race.session_id)}>
            <button className="demo-race-select" onClick={() => { autoFollow.current = false; setSession(String(race.session_id)); setDriver(""); }} aria-label={`Show ${race.event_name} ${String(race.session_id).slice(0, 8)} live timing`}>
              <span className="demo-race-name">{String(race.event_name || "Generated race")}</span>
              <span className="demo-race-meta">{String(race.circuit_name || "Circuit pending")} · {String(race.car_count)} cars · {String(race.total_laps)} laps · {String(race.created_at || "").slice(0, 10)} · {String(race.session_id).slice(0, 8)}</span>
            </button>
            <span className={`demo-state ${race.state === "ACTIVE" ? "is-active" : ""}`}><NbBadge status={String(race.state)} /></span>
            {canManageDemos && <NbButton variant="ghost" className="icon-button danger-icon" aria-label={`Delete ${race.event_name} ${String(race.session_id).slice(0, 8)}`} disabled={demoBusy} onClick={() => setDeleteRace(race)}><Trash2 size={15} /></NbButton>}
          </NbCard>
        ))}
      </div>
      {showCompletedDemos && demoRaces.length > 6 && <NbButton variant="secondary" onClick={() => setShowCompletedDemos(false)}>Show recent races</NbButton>}
    </>
  );
  return (
    <>
      {canManageDemos && (
        <NbCard tone="yellow" className="demo-race-hero my-3 flex flex-wrap items-center justify-between gap-4 !border-ink !bg-yellow !text-ink" aria-labelledby="demo-race-title">
          <div>
            <div className="eyebrow">LIVE DEMO / READY TO RUN</div>
            <h2 id="demo-race-title" className="!text-ink !font-bold !text-[length:var(--fs-h2)] leading-[1.2]">Put a full grid on track</h2>
            <p className="!text-ink !text-[length:var(--fs-body)] leading-[1.5]">Start a generated race with 8–16 fictional drivers and live timing. Sessions support up to 72 laps.</p>
          </div>
          <NbButton variant="primary" size="lg" disabled={demoBusy} data-primary={createPrimary ? "true" : undefined} onClick={() => void createDemoRace()}>
            <Plus size={15} /> {demoBusy ? "Starting race…" : "Create live race"}
          </NbButton>
        </NbCard>
      )}
      {demoMessage && <div className="notice" role="status">{demoMessage}</div>}
      <section className="demo-races-panel" aria-labelledby="demo-races-title">
          <NbCard shadow={4} className="demo-races-container">
          <div className="panel-heading">
            <div><div className="eyebrow">GENERATED SESSIONS</div><h2 id="demo-races-title">Live race demos</h2></div>
            <span className="muted">{demoRaces.length} race{demoRaces.length === 1 ? "" : "s"}</span>
          </div>
          <NbState<Row[]>
            state={listState}
            empty="No generated races are available."
            className="demo-race-list-state"
            loadingLabel="Loading generated races"
            skeletonRows={3}
            sourceMessage={listError || undefined}
            partialSummary={`Showing ${visibleDemoRaces.length} of ${demoRaces.length} generated races`}
            partialActionLabel={listError ? "Retry" : `Show all ${demoRaces.length} generated races`}
            partialActionAriaLabel={listError ? "Retry generated races" : `Show all ${demoRaces.length} generated races`}
          >
            {(races) => <>
              {listError && visibleDemoRaces.length < demoRaces.length && <NbButton variant="secondary" onClick={() => setShowCompletedDemos(true)}>Show all {demoRaces.length} generated races</NbButton>}
              {showRaceCards(races)}
            </>}
          </NbState>
          </NbCard>
      </section>
    </>
  );
}
