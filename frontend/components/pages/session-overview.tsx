import { Row } from "@/lib/api";
import {
  AddButton,
  DataTable,
  PageHeader,
  ReloadButton,
  StateMessage,
} from "../ui";

type SessionOverviewProps = {
  canManage: boolean;
  setEditModal: (value: boolean) => void;
  setModal: (value: boolean) => void;
  rows: Row[];
  events: Row[];
  err: string;
  loading: boolean;
  load: () => Promise<void>;
  setSelected: (value: string) => void;
  setResults: (rows: Row[]) => void;
  setResultsLoaded: (value: boolean) => void;
  setActionMsg: (value: string) => void;
};

export function SessionOverview({
  canManage,
  setEditModal,
  setModal,
  rows,
  events,
  err,
  loading,
  load,
  setSelected,
  setResults,
  setResultsLoaded,
  setActionMsg,
}: SessionOverviewProps) {
  return (
    <>
      <PageHeader
        eyebrow="RACE CONTROL / SESSION CONTROL"
        title="Sessions"
        description="Schedule sessions, control the live state, and review classified results."
        action={
          canManage ? (
            <AddButton
              onClick={() => {
                setEditModal(false);
                setModal(true);
              }}
              children="Schedule session"
            />
          ) : null
        }
      />
      <div className="toolbar">
        <span className="record-count">{rows.length} SESSIONS</span>
        <ReloadButton onClick={() => void load()} />
      </div>
      <StateMessage error={err} loading={loading} retry={() => void load()} />
      {!loading && !err && (
        <DataTable
          rows={rows.map((r) => ({
            ...r,
            event_name:
              r.event_name || events.find((e) => e.id === r.event_id)?.name,
          }))}
          columns={[
            "event_name",
            "session_type",
            "state",
            "scheduled_at",
            "total_laps",
          ]}
          onSelect={(r) => {
            setSelected(String(r.id || ""));
            setResults([]);
            setResultsLoaded(false);
            setActionMsg("");
          }}
        />
      )}
    </>
  );
}
