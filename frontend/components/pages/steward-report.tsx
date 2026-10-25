import type { ComponentProps } from "react";
import type { Row } from "@/lib/api";
import { ResourceEditor } from "../ui";

type StewardReportProps = {
  sessions: Row[];
  drivers: Row[];
  report: ComponentProps<typeof ResourceEditor>["save"];
  busy: boolean;
};

export function StewardReport({
  sessions,
  drivers,
  report,
  busy,
}: StewardReportProps) {
  return (
    <ResourceEditor
      fields={[
        {
          name: "session_id",
          required: true,
          options: sessions.map((s) => ({
            value: String(s.id),
            label: `${String(s.event_name || "Event")} · ${String(s.session_type || "Session")} · ${String(s.state || "")} · ${String(s.scheduled_at || "").slice(0, 10)} · ${String(s.id).slice(0, 8)}`,
          })),
        },
        {
          name: "driver_id",
          required: true,
          options: drivers.map((d) => ({
            value: String(d.id),
            label: `${String(d.number || "#—")} · ${String(d.full_name || "Driver")}`,
          })),
        },
        { name: "lap", type: "number", required: true },
        { name: "description", required: true },
      ]}
      save={report}
      busy={busy}
      primary
    />
  );
}
