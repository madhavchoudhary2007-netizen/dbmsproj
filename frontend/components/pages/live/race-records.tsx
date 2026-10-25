import type { Dispatch, SetStateAction } from "react";
import { Row, pretty } from "@/lib/api";
import type { ViewState } from "@/lib/data-state";
import { NbBadge } from "@/components/nb/badge";
import { NbButton } from "@/components/nb/button";
import { NbCard } from "@/components/nb/card";
import { NbState } from "@/components/nb/state";
import { NbTable } from "@/components/nb/table";

type RaceRecordsProps = {
  selectedLaps: Row[];
  recordsError: string;
  loading: boolean;
  retry: () => void;
  showAllLaps: boolean;
  setShowAllLaps: Dispatch<SetStateAction<boolean>>;
  visibleLaps: Row[];
  namedDrivers: Map<string, Row>;
  liveIncidents: Row[];
  livePitStops: Row[];
};

type TimelineField = { key: string; label: string; status?: boolean };

function recordsState(rows: Row[], loading: boolean, error: string, retry: () => void): ViewState<Row[]> {
  if (loading && !rows.length) return { status: "loading" };
  if (error && !rows.length) return { status: "error", error: { message: error, retryable: true }, retry };
  if (error) return { status: "partial", data: rows, totalCount: rows.length, filter: { label: "records refresh", clear: retry } };
  return rows.length ? { status: "populated", data: rows } : { status: "empty", reason: "no-data" };
}

function ControlTimeline({ fields, state, error }: { fields: TimelineField[]; state: ViewState<Row[]>; error: string }) {
  return <NbState state={state} empty="No records returned by the API." sourceMessage={state.status === "partial" ? `Records could not be refreshed: ${error}` : undefined} partialActionLabel="Retry records" skeletonRows={3}>
    {(items) => <ol className="space-y-3 border-l-4 border-ink pl-4">
      {items.map((row, index) => <li key={`${String(row.id ?? row.lap ?? index)}-${index}`} className="relative border-4 border-ink bg-paper p-3 shadow-nb-4">
        <span aria-hidden="true" className="absolute -left-6 top-3 size-3 border-4 border-ink bg-yellow" />
        <dl className="grid min-w-0 grid-cols-1 gap-x-4 gap-y-2 sm:grid-cols-2">
          {fields.map(({ key, label, status: isStatus }) => <div key={key} className="min-w-0">
            <dt className="text-[length:var(--fs-label)] font-bold uppercase tracking-wide">{label}</dt>
            <dd className="break-words font-mono tabular-nums">{isStatus ? <NbBadge status={pretty(row[key])}>{pretty(row[key])}</NbBadge> : pretty(row[key])}</dd>
          </div>)}
        </dl>
      </li>)}
    </ol>}
  </NbState>;
}

export function RaceRecords({ selectedLaps, recordsError, loading, retry, showAllLaps, setShowAllLaps, visibleLaps, namedDrivers, liveIncidents, livePitStops }: RaceRecordsProps) {
  const lapRows = visibleLaps.map((lap) => ({
    driver_name: namedDrivers.get(String(lap.driver_id))?.full_name || lap.driver_id,
    lap: lap.lap,
    sector_1_ms: Array.isArray(lap.sector_ms) ? lap.sector_ms[0] : null,
    sector_2_ms: Array.isArray(lap.sector_ms) ? lap.sector_ms[1] : null,
    sector_3_ms: Array.isArray(lap.sector_ms) ? lap.sector_ms[2] : null,
    lap_time_ms: lap.lap_time_ms,
    position: lap.position,
  }));
  const lapState: ViewState<typeof lapRows> = loading && !selectedLaps.length
    ? { status: "loading" }
    : recordsError && !selectedLaps.length
      ? { status: "error", error: { message: recordsError, retryable: true }, retry }
      : recordsError
        ? { status: "partial", data: lapRows, totalCount: selectedLaps.length, filter: { label: "records refresh", clear: retry } }
        : selectedLaps.length > 100 && !showAllLaps
          ? { status: "partial", data: lapRows, totalCount: selectedLaps.length, filter: { label: "latest 100 laps", clear: () => setShowAllLaps(true) } }
          : lapRows.length ? { status: "populated", data: lapRows } : { status: "empty", reason: "no-data" };
  const incidentsState = recordsState(liveIncidents, loading, recordsError, retry);
  const pitStopsState = recordsState(livePitStops, loading, recordsError, retry);
  const lapColumns = [
    { key: "driver_name", title: "driver name", render: (row: (typeof lapRows)[number]) => pretty(row.driver_name) }, { key: "lap", title: "lap", numeric: true, render: (row: (typeof lapRows)[number]) => pretty(row.lap) },
    { key: "sector_1_ms", title: "sector 1 ms", numeric: true, render: (row: (typeof lapRows)[number]) => pretty(row.sector_1_ms) }, { key: "sector_2_ms", title: "sector 2 ms", numeric: true, render: (row: (typeof lapRows)[number]) => pretty(row.sector_2_ms) },
    { key: "sector_3_ms", title: "sector 3 ms", numeric: true, render: (row: (typeof lapRows)[number]) => pretty(row.sector_3_ms) }, { key: "lap_time_ms", title: "lap time ms", numeric: true, render: (row: (typeof lapRows)[number]) => pretty(row.lap_time_ms) },
    { key: "position", title: "position", numeric: true, render: (row: (typeof lapRows)[number]) => pretty(row.position) },
  ];
  return <>
    <NbCard tone="paper" className="min-w-0">
      <div className="mb-4 flex min-w-0 flex-wrap items-end justify-between gap-4">
        <div><p className="text-[length:var(--fs-label)] font-bold uppercase tracking-widest">RECORDED LAPS</p><h2 className="text-[length:var(--fs-h2)] font-bold">Driver lap and sector history</h2></div>
        <span className="text-[length:var(--fs-label)]">{selectedLaps.length} completed driver laps</span>
      </div>
      {recordsError && <div className="mb-4 border-4 border-ink bg-red p-3" role="status">Lap and race-control records could not be refreshed: {recordsError}. Retrying automatically in 5 seconds.</div>}
      {recordsError && selectedLaps.length > 100 && !showAllLaps && <div className="mb-4"><NbButton variant="secondary" onClick={() => setShowAllLaps(true)}>Show all laps</NbButton></div>}
      {selectedLaps.length > 100 && showAllLaps && <div className="mb-4 flex flex-wrap items-center justify-between gap-3"><span className="text-[length:var(--fs-label)]">Showing all laps</span><NbButton variant="secondary" onClick={() => setShowAllLaps(false)}>Show latest 100</NbButton></div>}
      <NbTable state={lapState} columns={lapColumns} rowKey={(_, index) => index} caption="Recorded laps with driver, lap, sector times, lap time, and position" empty="No records returned by the API." pageSize={5} sourceMessage={recordsError || undefined} partialSummary={lapState.status === "partial" && selectedLaps.length > 100 && !showAllLaps ? `Showing latest 100 laps · Showing 100 of ${selectedLaps.length} completed driver laps` : undefined} partialActionLabel={recordsError ? "Retry records" : "Show all laps"} />
    </NbCard>
    <NbCard tone="paper" className="min-w-0">
      <p className="text-[length:var(--fs-label)] font-bold uppercase tracking-widest">RACE CONTROL RECORDS</p><h2 className="mb-4 text-[length:var(--fs-h2)] font-bold">Incidents and pit stops</h2>
      <h3 className="mb-3 text-[length:var(--fs-h3)] font-bold">Incidents</h3>
      <ControlTimeline state={incidentsState} error={recordsError} fields={[{ key: "driver_name", label: "Driver" }, { key: "lap", label: "Lap" }, { key: "description", label: "Description" }, { key: "state", label: "State", status: true }]} />
      <h3 className="mb-3 mt-6 text-[length:var(--fs-h3)] font-bold">Pit stops</h3>
      <ControlTimeline state={pitStopsState} error={recordsError} fields={[{ key: "driver_name", label: "Driver" }, { key: "team_name", label: "Team" }, { key: "box_number", label: "Box number" }, { key: "starts_at", label: "Starts at" }, { key: "ends_at", label: "Ends at" }, { key: "status", label: "Status", status: true }]} />
    </NbCard>
  </>;
}
