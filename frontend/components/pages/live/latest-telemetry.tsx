import { pretty, type Row } from "@/lib/api";
import type { ViewState } from "@/lib/data-state";
import { NbCard } from "@/components/nb/card";
import { NbTable, type NbTableColumn } from "@/components/nb/table";

const keys = [
  "ts",
  "driver_id",
  "lap",
  "sector",
  "position",
  "speed_kph",
  "throttle_pct",
  "brake_pct",
  "tire_compound",
  "pit_state",
  "pit_box_number",
  "pit_reservation_id",
] as const;

const numericKeys = new Set<string>([
  "lap",
  "sector",
  "position",
  "speed_kph",
  "throttle_pct",
  "brake_pct",
  "pit_box_number",
]);

const columns: NbTableColumn<Row>[] = keys.map((key) => ({
  key,
  title: key.replaceAll("_", " "),
  numeric: numericKeys.has(key),
  className: "whitespace-normal break-words font-mono tabular-nums",
  render: (row) => pretty(row[key]),
}));

export function LatestTelemetry({
  shown,
  status,
  loading,
  error,
  retry,
}: {
  shown: Row[];
  status: string;
  loading: boolean;
  error: string;
  retry: () => void;
}) {
  const rows = shown.slice(-30).reverse();
  const snapshotState: ViewState<readonly Row[]> = loading && rows.length === 0
    ? { status: "loading" }
    : error && rows.length === 0
      ? { status: "error", error: { message: error, retryable: true }, retry }
      : error
        ? {
            status: "partial",
            data: rows,
            filter: { label: "Retry snapshot", clear: retry },
            totalCount: shown.length,
          }
        : rows.length > 0
          ? { status: "populated", data: rows }
          : { status: "empty", reason: "no-data" };

  return (
    <NbCard tone="paper" className="min-w-0">
      <div className="mb-4 flex min-w-0 flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="eyebrow !text-[length:var(--fs-label)]">LATEST TELEMETRY</div>
          <h2 className="!text-[length:var(--fs-h3)]">{shown.length} samples in view</h2>
        </div>
        <span className="live-badge !bg-paper !text-ink">
          <i /> <span className="!bg-paper !text-[length:var(--fs-label)] !text-ink">{status}</span>
        </span>
      </div>
      <NbTable
        state={snapshotState}
        columns={columns}
        rowKey={(_, index) => index}
        caption="Latest telemetry samples"
        empty="No records returned by the API."
        pageSize={8}
        className="font-mono"
        sourceMessage={error || undefined}
        partialSummary={`Showing ${rows.length} retained samples of ${shown.length}.`}
        partialActionLabel="Retry snapshot"
        partialActionAriaLabel="Retry snapshot for latest telemetry"
      />
    </NbCard>
  );
}
