"use client";

import type { ComponentProps } from "react";
import type { Row } from "@/lib/api";
import { Modal, ResourceEditor } from "../ui";

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
    <Modal
      title="Add or update session result"
      close={() => setResultModal(false)}
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
      />
    </Modal>
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
    <Modal
      title={editModal ? "Edit session" : "Schedule session"}
      close={() => setModal(false)}
    >
      <div className="form-hint">
        Event IDs are taken from the event records loaded above.
      </div>
      <ResourceEditor
        fields={fields}
        initial={editModal ? current : undefined}
        save={save}
        busy={busy}
      />
    </Modal>
  );
}
