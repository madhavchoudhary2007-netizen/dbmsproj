import { Pause, Play, Square } from "lucide-react";
import { Row } from "@/lib/api";
import { NbButton } from "@/components/nb/button";

type SessionControlsProps = {
  current: Row;
  canManage: boolean;
  canControl: boolean;
  setEditModal: (value: boolean) => void;
  setModal: (value: boolean) => void;
  perform: (action: string) => Promise<unknown>;
  setResultModal: (value: boolean) => void;
  getResults: () => Promise<unknown>;
};

export function SessionControls({
  current,
  canManage,
  canControl,
  setEditModal,
  setModal,
  perform,
  setResultModal,
  getResults,
}: SessionControlsProps) {
  return (
    <div className="space-y-3">
      {canControl && (
        <div role="group" aria-label="Session lifecycle" className="flex flex-wrap items-stretch gap-2">
          <span className="inline-flex min-h-12 items-center border-4 border-ink bg-yellow px-3 font-bold uppercase text-ink">
            {String(current?.state ?? "")}
          </span>
          <NbButton className="[&_.nb-face]:!min-h-12" disabled={current?.state !== "SCHEDULED"} onClick={() => void perform("start")}>
            <Play size={14} /> Start
          </NbButton>
          <NbButton className="[&_.nb-face]:!min-h-12" variant="secondary" disabled={current?.state !== "ACTIVE"} onClick={() => void perform("pause")}>
            <Pause size={14} /> Pause
          </NbButton>
          <NbButton className="[&_.nb-face]:!min-h-12" variant="secondary" disabled={current?.state !== "PAUSED"} onClick={() => void perform("resume")}>
            <Play size={14} /> Resume
          </NbButton>
          <NbButton className="[&_.nb-face]:!min-h-12" variant="danger" disabled={current?.state !== "ACTIVE" && current?.state !== "PAUSED"} onClick={() => void perform("finish")}>
            <Square size={14} /> Finish
          </NbButton>
        </div>
      )}
      <div className="action-row flex flex-wrap gap-2">
        {canManage && (
          <NbButton
            variant="secondary"
            onClick={() => {
              setEditModal(true);
              setModal(true);
            }}
          >
            Edit session
          </NbButton>
        )}
        {canControl && (
          <>
            <NbButton variant="secondary" disabled={!current || current.state === "SCHEDULED"} onClick={() => void perform("reset")}>
              Reset
            </NbButton>
            <NbButton variant="secondary" disabled={!current || !["ACTIVE", "PAUSED", "COMPLETED"].includes(String(current.state))} onClick={() => setResultModal(true)}>
              Record result
            </NbButton>
          </>
        )}
        <NbButton variant="secondary" onClick={() => void getResults()}>
          Load results
        </NbButton>
      </div>
    </div>
  );
}
