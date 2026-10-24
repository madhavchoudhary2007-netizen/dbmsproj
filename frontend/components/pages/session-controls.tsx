import { Pause, Play, Square } from "lucide-react";
import { Row } from "@/lib/api";
import { Button } from "../ui";

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
    <div className="action-row">
      {canManage && (
        <Button
          kind="secondary"
          onClick={() => {
            setEditModal(true);
            setModal(true);
          }}
        >
          Edit session
        </Button>
      )}
      {canControl && (
        <>
          <Button disabled={current?.state !== "SCHEDULED"} onClick={() => void perform("start")}>
            <Play size={14} /> Start
          </Button>
          <Button kind="secondary" disabled={current?.state !== "ACTIVE"} onClick={() => void perform("pause")}>
            <Pause size={14} /> Pause
          </Button>
          <Button kind="secondary" disabled={current?.state !== "PAUSED"} onClick={() => void perform("resume")}>
            <Play size={14} /> Resume
          </Button>
          <Button kind="danger" disabled={current?.state !== "ACTIVE" && current?.state !== "PAUSED"} onClick={() => void perform("finish")}>
            <Square size={14} /> Finish
          </Button>
          <Button kind="secondary" disabled={!current || current.state === "SCHEDULED"} onClick={() => void perform("reset")}>
            Reset
          </Button>
          <Button kind="secondary" disabled={!current || !["ACTIVE", "PAUSED", "COMPLETED"].includes(String(current.state))} onClick={() => setResultModal(true)}>
            Record result
          </Button>
        </>
      )}
      <Button kind="secondary" onClick={() => void getResults()}>
        Load results
      </Button>
    </div>
  );
}
