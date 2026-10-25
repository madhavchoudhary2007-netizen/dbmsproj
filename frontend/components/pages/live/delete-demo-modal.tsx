import type { Row } from "@/lib/api";
import { Button, Modal } from "@/components/ui";

export function DeleteDemoModal({
  deleteRace,
  demoBusy,
  setDeleteRace,
  removeDemoRace,
}: {
  deleteRace: Row | null;
  demoBusy: boolean;
  setDeleteRace: (race: Row | null) => void;
  removeDemoRace: () => Promise<void>;
}) {
  return (
    <>
      {deleteRace && (
        <Modal title="Delete generated race?" close={() => !demoBusy && setDeleteRace(null)}>
          <div className="decision-form">
            <p>Delete <strong>{String(deleteRace.event_name || "this generated race")}</strong> and its generated drivers and telemetry? This action cannot be undone.</p>
            <div className="form-actions">
              <Button kind="secondary" disabled={demoBusy} onClick={() => setDeleteRace(null)}>Keep race</Button>
              <Button kind="danger" disabled={demoBusy} onClick={() => void removeDemoRace()}>{demoBusy ? "Deleting…" : "Delete race"}</Button>
            </div>
          </div>
        </Modal>
      )}
    </>
  );
}
