import { NbCard } from "@/components/nb/card";
import { NbTable, type NbTableColumn } from "@/components/nb/table";
import { TyreBadge } from "@/components/nb/tyre-badge";
import type { ViewState } from "@/lib/data-state";
import { pretty, type Row } from "@/lib/api";

const tyreCompounds = ["SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"] as const;
type TyreCompound = (typeof tyreCompounds)[number];

function isTyreCompound(value: unknown): value is TyreCompound {
  return typeof value === "string" && tyreCompounds.includes(value as TyreCompound);
}

function sectorCell(row: Row, index: number) {
  const cells: unknown = (row as Row & { sector_cells?: unknown }).sector_cells;
  if (!Array.isArray(cells) || cells.length !== 3) return "—";
  const cell = cells[index];
  if (cell === null || typeof cell !== "object") return "—";
  const { ms, kind } = cell as { ms?: unknown; kind?: unknown };
  const labels: Record<string, string> = {
    overall: "OB",
    personal: "PB",
    slower: "SLOW",
    unknown: "—",
  };
  const tones: Record<string, string> = {
    overall: "var(--color-violet)",
    personal: "var(--color-mint)",
    slower: "var(--color-yellow)",
    unknown: "var(--color-paper)",
  };
  if (typeof kind !== "string" || !(kind in labels)) return "—";
  return (
    <span style={{ backgroundColor: tones[kind], color: "var(--color-ink)", display: "inline-flex", flexDirection: "column", minHeight: 44, justifyContent: "center", padding: 8 }}>
      <span>{labels[kind]}</span>
      <span>{typeof ms === "number" && Number.isFinite(ms) ? pretty(ms) : "—"}</span>
    </span>
  );
}

const columns: readonly NbTableColumn<Row>[] = [
  { key: "position", title: "position", numeric: true, render: (row) => <span style={{ alignItems: "center", backgroundColor: "var(--color-ink)", color: "var(--color-paper)", display: "inline-flex", fontFamily: "var(--font-mono)", height: 44, justifyContent: "center", minWidth: 44 }}>{pretty(row.position)}</span> },
  { key: "number", title: "number", numeric: true, render: (row) => pretty(row.number) },
  { key: "driver_name", title: "driver name", render: (row) => <span style={{ alignItems: "center", display: "inline-flex", gap: 8 }}><span>{pretty(row.driver_name)}</span>{(row as Row & { fastest_lap?: unknown }).fastest_lap === true && <span style={{ backgroundColor: "var(--color-violet)", color: "var(--color-ink)", padding: 4 }}>FL</span>}</span> },
  { key: "licence_number", title: "licence number", numeric: true, render: (row) => pretty(row.licence_number) },
  { key: "team_name", title: "team name", render: (row) => {
    const team = row as Row & { team_color?: unknown; team_colour?: unknown };
    const suppliedColor = typeof team.team_color === "string" && team.team_color.trim()
      ? team.team_color
      : typeof team.team_colour === "string" && team.team_colour.trim()
        ? team.team_colour
        : undefined;
    const color = suppliedColor ?? "var(--color-ink)";
    return <span style={{ borderLeft: `4px solid ${color}`, display: "inline-block", minHeight: 44, padding: 8 }}>{pretty(row.team_name)}</span>;
  } },
  { key: "gap", title: "gap", numeric: true, render: (row) => pretty(row.gap) },
  { key: "lap", title: "lap", numeric: true, render: (row) => pretty(row.lap) },
  { key: "sector", title: "sector", numeric: true, render: (row) => pretty(row.sector) },
  { key: "sector_times_ms", title: "sector times ms", numeric: true, render: (row) => pretty(row.sector_times_ms) },
  { key: "last_lap_ms", title: "last lap ms", numeric: true, render: (row) => pretty(row.last_lap_ms) },
  { key: "best_lap_ms", title: "best lap ms", numeric: true, render: (row) => pretty(row.best_lap_ms) },
  { key: "tire_compound", title: "tire compound", render: (row) => <span style={{ alignItems: "center", display: "inline-flex", gap: 8 }}>{isTyreCompound(row.tire_compound) && <TyreBadge compound={row.tire_compound} />}<span>{pretty(row.tire_compound)}</span><span>{pretty(row.tire_age_laps)} laps</span></span> },
  { key: "tire_age_laps", title: "tire age laps", numeric: true, render: (row) => pretty(row.tire_age_laps) },
  { key: "tire_wear_pct", title: "tire wear pct", numeric: true, render: (row) => pretty(row.tire_wear_pct) },
  { key: "pit_state", title: "pit state", render: (row) => pretty(row.pit_state) },
  { key: "pit_box_number", title: "pit box number", numeric: true, render: (row) => pretty(row.pit_box_number) },
  { key: "interval", title: "interval", render: (row) => pretty((row as Row & { interval?: unknown }).interval) },
  { key: "sector_s1", title: "S1", render: (row) => sectorCell(row, 0) },
  { key: "sector_s2", title: "S2", render: (row) => sectorCell(row, 1) },
  { key: "sector_s3", title: "S3", render: (row) => sectorCell(row, 2) },
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
