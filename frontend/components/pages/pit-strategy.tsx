import type { Row } from "@/lib/api";
import type { ViewState } from "@/lib/data-state";
import { NbBadge } from "@/components/nb/badge";
import { NbCard } from "@/components/nb/card";
import { NbState } from "@/components/nb/state";
import { TyreBadge } from "@/components/nb/tyre-badge";

type Props = {
  strategy: Row[];
  strategyLoading: boolean;
  strategyError: string;
  loading: boolean;
  sessionState: unknown;
  selectedSession: string;
  retry: () => void;
  value: (value: unknown, suffix?: string) => string;
  statusText: (status: unknown) => string;
};

const compounds = ["SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"] as const;
type Compound = (typeof compounds)[number];
const isCompound = (value: unknown): value is Compound => compounds.includes(value as Compound);

export function PitStrategy(props: Props) {
  const { strategy, strategyLoading, strategyError, loading, sessionState, selectedSession, retry, value, statusText } = props;
  const retained = strategy.length > 0;
  let state: ViewState<Row[]>;
  if ((strategyError || strategyLoading || loading) && retained) {
    state = { status: "partial", data: strategy, totalCount: strategy.length, filter: { label: "automatic strategy refresh", clear: retry } };
  } else if (strategyError) {
    state = { status: "error", error: { message: strategyError, retryable: true }, retry };
  } else if (loading || strategyLoading) {
    state = { status: "loading" };
  } else if (!selectedSession || !strategy.length) {
    state = { status: "empty", reason: "no-data" };
  } else {
    state = { status: "populated", data: strategy };
  }
  return <NbCard tone="cream" shadow={4} className="grid gap-4" role="region" aria-label="Driver pit decisions">
    <div className="grid gap-2">
      <p className="font-mono text-sm font-bold uppercase">AUTOMATIC STRATEGY{strategyLoading ? " · UPDATING" : ""}</p>
      <div className="flex flex-wrap items-center justify-between gap-4"><h2 className="text-2xl font-bold">Driver pit decisions</h2><span>{String(sessionState || "No session selected")}</span></div>
      <p>The strategy engine tracks tire age and schedules stops at the configured stint target. Pit reservations are created automatically.</p>
      {strategyError && <strong>Strategy unavailable</strong>}
    </div>
    <NbState state={state} empty={selectedSession ? "No driver strategy is available for this session." : "Select a session to view its automatic pit strategy."} loadingLabel="Loading automatic strategy" skeletonRows={2} sourceMessage={strategyError ? `Strategy unavailable: ${strategyError}` : strategyLoading || loading ? "Automatic strategy is updating." : undefined} partialSummary={strategyError ? "Showing retained strategy while the refresh failed." : "Showing retained strategy while it updates."} partialActionLabel={strategyError ? "Try again" : "Refresh strategy"} partialActionAriaLabel="Refresh automatic pit strategy" className="grid gap-4">
      {(rows) => <div className="grid gap-4 md:grid-cols-2">{rows.map((d, i) => {
        const assigned = d.assigned_box as Row | null;
        const stops = Array.isArray(d.stops) ? d.stops as Row[] : [];
        const pendingStop = stops.find((stop) => stop.status === "PENDING" || stop.status === "RESERVED");
        const destination = pendingStop?.tire_compound ?? pendingStop?.compound;
        return <NbCard tone="paper" shadow={4} className="grid content-start gap-4" key={String(d.driver_id || i)}>
          <div className="flex flex-wrap items-start justify-between gap-4"><div><p className="font-mono text-sm font-bold uppercase">{String(d.team_name || "Team")}{d.driver_number ? ` · #${d.driver_number}` : ""}</p><h3 className="text-xl font-bold">{String(d.driver_name || "Driver")}</h3></div><NbBadge status={String(d.status || "")}>{statusText(d.status)}</NbBadge></div>
          <div className="grid gap-2">
            <div className="flex items-center justify-between gap-4"><span>Current lap</span><b>{value(d.current_lap)}</b></div>
            <div className="flex flex-wrap items-center justify-between gap-4"><span>Tire</span><span className="flex items-center gap-2">{isCompound(d.tire_compound) && <TyreBadge compound={d.tire_compound} />}<b>{value(d.tire_compound)} · {value(d.tire_age_laps)} {Number(d.tire_age_laps) === 1 ? "lap" : "laps"}</b>{isCompound(destination) && <span className="flex items-center gap-2" aria-label={`Pending stop: ${destination}`}><span aria-hidden="true">→</span><TyreBadge compound={destination} /></span>}</span></div>
            <div className="flex items-center justify-between gap-4"><span>Tire wear</span><b>{value(d.tire_wear_pct, "%")}</b></div>
            {sessionState !== "COMPLETED" && <><div className="flex items-center justify-between gap-4"><span>Recommended stop</span><b>{d.recommended_stop_lap == null ? "—" : `Lap ${d.recommended_stop_lap}`}</b></div><div className="flex items-center justify-between gap-4"><span>Pit window</span><b>{d.pit_window_start_lap == null && d.pit_window_end_lap == null ? "—" : `Lap ${value(d.pit_window_start_lap)}–${value(d.pit_window_end_lap)}`}</b></div><div className="flex items-center justify-between gap-4"><span>Decision in</span><b>{d.laps_until_decision == null ? "—" : `${d.laps_until_decision} ${Number(d.laps_until_decision) === 1 ? "lap" : "laps"}`}</b></div></>}
          </div>
          <p>{String(d.reason || "Automatic strategy is monitoring this stint.")}</p>
          {assigned && <div className="border-4 border-ink bg-yellow p-3">Box {value(assigned.box_number)} reserved · {String(assigned.status || "").toLowerCase()}</div>}
        </NbCard>;
      })}</div>}
    </NbState>
  </NbCard>;
}
