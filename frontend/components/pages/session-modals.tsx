"use client";

import type { ComponentProps } from "react";
import type { Row } from "@/lib/api";
import { NbModal } from "@/components/nb/modal";
import { ResourceEditor } from "../ui";

type SessionResultModalProps = {
  drivers: Row[];
  busy: boolean;
  saveResult: ComponentProps<typeof ResourceEditor>["save"];
  setResultModal: (open: boolean) => void;
};

export function SessionResultModal({
  drivers,
  busy,
  saveResult,
  setResultModal,
}: SessionResultModalProps) {
  return (
    <NbModal
      open={true}
      title="Add or update session result"
      onClose={() => setResultModal(false)}
    >
      <ResourceEditor
        fields={[
          {
            name: "driver_id",
            required: true,
            options: drivers.map((d) => ({
              value: String(d.id),
              label: `${String(d.number || "#—")} · ${String(d.full_name || "Driver")}`,
            })),
          },
          { name: "position", type: "number", required: true },
          { name: "lap_time_ms", type: "number" },
          { name: "pole", options: ["false", "true"] },
          { name: "fastest_lap", options: ["false", "true"] },
          { name: "classified", options: ["true", "false"] },
        ]}
        save={saveResult}
        busy={busy}
        primary
      />
    </NbModal>
  );
}

type SessionEditorModalProps = {
  editModal: boolean;
  current: Row | undefined;
  fields: ComponentProps<typeof ResourceEditor>["fields"];
  save: ComponentProps<typeof ResourceEditor>["save"];
  busy: boolean;
  setModal: (open: boolean) => void;
};

export function SessionEditorModal({
  editModal,
  current,
  fields,
  save,
  busy,
  setModal,
}: SessionEditorModalProps) {
  return (
    <NbModal
      open={true}
      title={editModal ? "Edit session" : "Schedule session"}
      onClose={() => setModal(false)}
    >
      <div className="form-hint">
        Event IDs are taken from the event records loaded above.
      </div>
      <ResourceEditor
        fields={fields}
        initial={editModal ? current : undefined}
        save={save}
        busy={busy}
        primary
      />
    </NbModal>
  );
}
