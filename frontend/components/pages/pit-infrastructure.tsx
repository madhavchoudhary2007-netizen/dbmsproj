import type { Row } from "@/lib/api";
import type { ViewState } from "@/lib/data-state";
import { NbBadge } from "@/components/nb/badge";
import { NbState } from "@/components/nb/state";

type Props = {
  boxes: Row[];
  res: Row[];
  strategy: Row[];
  loading: boolean;
  error: string;
  retry: () => void;
  onSelect: (row: Row) => void;
};

function stateFor(rows: Row[], loading: boolean, error: string, retry: () => void): ViewState<Row[]> {
  if (rows.length && (loading || error)) return { status: "partial", data: rows, filter: { label: "retained records", clear: retry }, totalCount: rows.length };
  if (loading) return { status: "loading" };
  if (error) return { status: "error", error: { message: error, retryable: true }, retry };
  return rows.length ? { status: "populated", data: rows } : { status: "empty", reason: "no-data" };
}

const value = (row: Row, key: string) => String(row[key] ?? "—");

export function PitInfrastructure({ boxes, res, strategy, loading, error, retry, onSelect }: Props) {
  const boxesState = stateFor(boxes, loading, error, retry);
  const queueState = stateFor(res, loading, error, retry);
  return <div className="grid gap-8 lg:grid-cols-2">
    <section aria-label="Selected event infrastructure" className="min-w-0">
      <div className="mb-4"><p className="font-mono text-sm font-bold uppercase">PIT BOXES</p><h2 className="text-2xl font-bold">Selected event infrastructure</h2></div>
      <NbState state={boxesState} empty="No records returned by the API." loadingLabel="Loading pit boxes" skeletonRows={3} partialSummary="Showing retained pit boxes while the latest request is incomplete" partialActionLabel="Try again" partialActionAriaLabel="Retry pit box request" sourceMessage={error || undefined}>
        {(rows) => <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">{rows.map((box) => {
          const active = strategy.some((stop) => stop.status === "IN_PIT" && String((stop.assigned_box as Row | undefined)?.box_number) === value(box, "number"));
          const status = active ? "ACTIVE" : value(box, "status");
          return <article key={String(box.id ?? box.number)} className={`min-w-0 border-4 border-ink p-4 shadow-nb-4 ${active ? "bg-red" : status === "RESERVED" ? "bg-yellow" : "bg-paper"}`}>
            <div aria-hidden="true" className="mb-3 h-2 w-full bg-ink" />
            <p className="break-words font-mono text-4xl font-bold tabular-nums">{value(box, "number")}</p>
            <p className="mb-3 min-h-11 min-w-0 break-words font-bold">{value(box, "team_name")}</p>
            <NbBadge status={status}><span className="inline-flex items-center gap-2"><span aria-hidden="true" className={`size-3 rounded-full bg-ink transition-opacity duration-200 motion-reduce:transition-none ${active ? "opacity-100" : "opacity-0"}`} />{active ? "IN PIT" : status}</span></NbBadge>
            <p className="mt-3 min-w-0 break-words text-sm"><span className="font-bold">Window:</span> {value(box, "starts_at")} → {value(box, "ends_at")}</p>
          </article>;
        })}</div>}
      </NbState>
    </section>
    <section aria-label="Pit stop queue" className="min-w-0">
      <div className="mb-4"><p className="font-mono text-sm font-bold uppercase">AUTOMATIC ALLOCATIONS</p><h2 className="text-2xl font-bold">Pit stop queue</h2></div>
      <NbState state={queueState} empty="No records returned by the API." loadingLabel="Loading pit stop queue" skeletonRows={3} partialSummary="Showing retained pit stops while the latest request is incomplete" partialActionLabel="Try again" partialActionAriaLabel="Retry pit stop queue request" sourceMessage={error || undefined}>
        {(rows) => <div aria-label="Pit stop allocation timeline" className="flex max-w-full gap-4 overflow-x-auto p-2" tabIndex={0}>
          {rows.map((row) => <button key={String(row.id)} type="button" onClick={() => onSelect(row)} aria-label={`Open reservation for ${value(row, "driver_name")}, ${value(row, "team_name")}`} className="w-64 shrink-0 border-4 border-ink bg-cream p-4 text-left text-ink shadow-nb-4 focus-visible:outline focus-visible:outline-4 focus-visible:outline-ink">
            {[["Driver", "driver_name"], ["Team", "team_name"], ["Box", "box_number"], ["Allocation", "allocation_source"], ["Starts", "starts_at"], ["Ends", "ends_at"], ["Status", "status"]].map(([label, key]) => <p key={key} className="mb-2 break-words"><span className="font-bold">{label}:</span> {value(row, key)}</p>)}
          </button>)}
        </div>}
      </NbState>
    </section>
  </div>;
}
