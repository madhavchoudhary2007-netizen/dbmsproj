import { Row } from "@/lib/api";
import { DataTable, StateMessage } from "../../ui";

export function TimingTower({
  orderRows,
  status,
}: {
  orderRows: Row[];
  status: string;
}) {
  return (
    <div className="panel running-order-panel">
      <div className="panel-heading">
        <div>
          <div className="eyebrow">LIVE TIMING / RUNNING ORDER</div>
          <h2>{orderRows.length} cars on timing</h2>
        </div>
        <span className="live-badge">
          <i /> {status}
        </span>
      </div>
      {orderRows.length ? (
        <DataTable
          rows={orderRows.map((car) => ({
            ...car,
            position: car.position ?? "—",
            sector: car.sector ?? "—",
            last_lap_ms: car.last_lap_ms ?? "—",
            best_lap_ms: car.best_lap_ms ?? "—",
            tire_compound: car.tire_compound ?? "—",
            tire_age_laps: car.tire_age_laps ?? "—",
            tire_wear_pct: car.tire_wear_pct ?? "—",
            pit_state: car.pit_state ?? "—",
          }))}
          columns={[
            "position",
            "number",
            "driver_name",
            "licence_number",
            "team_name",
            "gap",
            "lap",
            "sector",
            "sector_times_ms",
            "last_lap_ms",
            "best_lap_ms",
            "tire_compound",
            "tire_age_laps",
            "tire_wear_pct",
            "pit_state",
            "pit_box_number",
          ]}
        />
      ) : (
        <StateMessage empty="Waiting for timing and telemetry packets from this session." />
      )}
    </div>
  );
}
