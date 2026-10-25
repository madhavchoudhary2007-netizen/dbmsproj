import { NbCard } from "@/components/nb/card";
import { NbTable, type NbTableColumn } from "@/components/nb/table";
import type { ViewState } from "@/lib/data-state";
import { pretty, type Row } from "@/lib/api";

const columns: readonly NbTableColumn<Row>[] = [
  { key: "position", title: "position", numeric: true, render: (row) => pretty(row.position) },
  { key: "number", title: "number", numeric: true, render: (row) => pretty(row.number) },
  { key: "driver_name", title: "driver name", render: (row) => pretty(row.driver_name) },
  { key: "licence_number", title: "licence number", numeric: true, render: (row) => pretty(row.licence_number) },
  { key: "team_name", title: "team name", render: (row) => pretty(row.team_name) },
  { key: "gap", title: "gap", numeric: true, render: (row) => pretty(row.gap) },
  { key: "lap", title: "lap", numeric: true, render: (row) => pretty(row.lap) },
  { key: "sector", title: "sector", numeric: true, render: (row) => pretty(row.sector) },
  { key: "sector_times_ms", title: "sector times ms", numeric: true, render: (row) => pretty(row.sector_times_ms) },
  { key: "last_lap_ms", title: "last lap ms", numeric: true, render: (row) => pretty(row.last_lap_ms) },
  { key: "best_lap_ms", title: "best lap ms", numeric: true, render: (row) => pretty(row.best_lap_ms) },
  { key: "tire_compound", title: "tire compound", render: (row) => pretty(row.tire_compound) },
  { key: "tire_age_laps", title: "tire age laps", numeric: true, render: (row) => pretty(row.tire_age_laps) },
  { key: "tire_wear_pct", title: "tire wear pct", numeric: true, render: (row) => pretty(row.tire_wear_pct) },
  { key: "pit_state", title: "pit state", render: (row) => pretty(row.pit_state) },
  { key: "pit_box_number", title: "pit box number", numeric: true, render: (row) => pretty(row.pit_box_number) },
];

export function TimingTower({
  orderRows,
  status,
  selectedDriver,
  onSelectDriver,
}: {
  orderRows: Row[];
  status: string;
  selectedDriver: string;
  onSelectDriver: (id: string) => void;
}) {
  const rows = orderRows.map((car) => ({
    ...car,
    position: car.position ?? "—",
    sector: car.sector ?? "—",
    last_lap_ms: car.last_lap_ms ?? "—",
    best_lap_ms: car.best_lap_ms ?? "—",
    tire_compound: car.tire_compound ?? "—",
    tire_age_laps: car.tire_age_laps ?? "—",
    tire_wear_pct: car.tire_wear_pct ?? "—",
    pit_state: car.pit_state ?? "—",
  }));
  const state: ViewState<readonly Row[]> = rows.length
    ? { status: "populated", data: rows }
    : { status: "empty", reason: "no-data" };

  return (
    <NbCard tone="paper" className="panel running-order-panel !bg-paper !p-4">
      <div className="panel-heading flex min-w-0 flex-wrap items-center justify-between gap-4">
        <div className="min-w-0">
          <div className="eyebrow !text-[length:var(--fs-label)] !leading-normal">LIVE TIMING / RUNNING ORDER</div>
          <h2 className="!text-[length:var(--fs-h3)] !leading-tight">{orderRows.length} cars on timing</h2>
        </div>
        <span className="live-badge inline-flex max-w-full flex-wrap !bg-paper !text-ink !text-[length:var(--fs-label)] !leading-normal">
          <i /> {status}
        </span>
      </div>
      <NbTable
        state={state}
        columns={columns}
        rowKey={(row) => String(row.driver_id)}
        caption="LIVE TIMING / RUNNING ORDER"
        empty="Waiting for timing and telemetry packets from this session."
        onSelect={(row) => onSelectDriver(String(row.driver_id))}
        isSelected={(row) => String(row.driver_id) === selectedDriver}
      />
    </NbCard>
  );
}
