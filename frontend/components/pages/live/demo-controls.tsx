import type { MutableRefObject } from "react";
import { Plus, Trash2 } from "lucide-react";
import { Button } from "../../ui";
import type { Row } from "../../../lib/api";

interface DemoControlsProps {
  canManageDemos: boolean;
  demoBusy: boolean;
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
}

export function DemoControls({
  canManageDemos,
  demoBusy,
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
}: DemoControlsProps) {
  return (
    <>
      {canManageDemos && (
        <section className="demo-race-hero panel" aria-labelledby="demo-race-title">
          <div>
            <div className="eyebrow">LIVE DEMO / READY TO RUN</div>
            <h2 id="demo-race-title">Put a full grid on track</h2>
            <p>Start a generated race with 8–16 fictional drivers and live timing. Sessions support up to 72 laps.</p>
          </div>
          <Button disabled={demoBusy} data-primary="true" onClick={() => void createDemoRace()}>
            <Plus size={15} /> {demoBusy ? "Starting race…" : "Create live race"}
          </Button>
        </section>
      )}
      {demoMessage && <div className="notice" role="status">{demoMessage}</div>}
      {demoRaces.length > 0 && (
        <section className="panel demo-races-panel" aria-labelledby="demo-races-title">
          <div className="panel-heading">
            <div><div className="eyebrow">GENERATED SESSIONS</div><h2 id="demo-races-title">Live race demos</h2></div>
            <span className="muted">{demoRaces.length} race{demoRaces.length === 1 ? "" : "s"}</span>
          </div>
          <div className="demo-race-list">
            {visibleDemoRaces.map((race: Row) => (
              <div className="demo-race-row" key={String(race.session_id)}>
                <button className="demo-race-select" onClick={() => { autoFollow.current = false; setSession(String(race.session_id)); setDriver(""); }} aria-label={`Show ${race.event_name} ${String(race.session_id).slice(0, 8)} live timing`}>
                  <span className="demo-race-name">{String(race.event_name || "Generated race")}</span>
                  <span className="demo-race-meta">{String(race.circuit_name || "Circuit pending")} · {String(race.car_count)} cars · {String(race.total_laps)} laps · {String(race.created_at || "").slice(0, 10)} · {String(race.session_id).slice(0, 8)}</span>
                </button>
                <span className={`demo-state ${race.state === "ACTIVE" ? "is-active" : ""}`}>{String(race.state)}</span>
                {canManageDemos && <button className="icon-button danger-icon" aria-label={`Delete ${race.event_name} ${String(race.session_id).slice(0, 8)}`} disabled={demoBusy} onClick={() => setDeleteRace(race)}><Trash2 size={15} /></button>}
              </div>
            ))}
          </div>
          {demoRaces.length > visibleDemoRaces.length && <Button kind="secondary" onClick={() => setShowCompletedDemos(true)}>Show all {demoRaces.length} generated races</Button>}
          {showCompletedDemos && demoRaces.length > 6 && <Button kind="secondary" onClick={() => setShowCompletedDemos(false)}>Show recent races</Button>}
        </section>
      )}
    </>
  );
}
