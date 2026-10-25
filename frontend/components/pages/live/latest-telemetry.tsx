import type { Row } from "@/lib/api";
import { DataTable } from "../../ui";

export function LatestTelemetry({
  shown,
  status,
}: {
  shown: Row[];
  status: string;
}) {
  return (
    <div className="panel">
      <div className="panel-heading">
        <div>
          <div className="eyebrow">LATEST TELEMETRY</div>
          <h2>{shown.length} samples in view</h2>
        </div>
        <span className="live-badge">
          <i /> {status}
        </span>
      </div>
      <DataTable
        rows={shown.slice(-30).reverse()}
        columns={[
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
        ]}
      />
    </div>
  );
}
