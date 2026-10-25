import type { Row } from "@/lib/api";
import { NbButton } from "@/components/nb/button";
import { NbModal } from "@/components/nb/modal";

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
        <NbModal title="Delete generated race?" open={Boolean(deleteRace)} onClose={() => !demoBusy && setDeleteRace(null)}>
          <div className="decision-form">
            <p>Delete <strong>{String(deleteRace.event_name || "this generated race")}</strong> and its generated drivers and telemetry? This action cannot be undone.</p>
            <div className="form-actions">
              <NbButton variant="secondary" disabled={demoBusy} onClick={() => setDeleteRace(null)}>Keep race</NbButton>
              <NbButton variant="danger" disabled={demoBusy} data-primary="true" onClick={() => void removeDemoRace()}>{demoBusy ? "Deleting…" : "Delete race"}</NbButton>
            </div>
          </div>
        </NbModal>
      )}
    </>
  );
}
