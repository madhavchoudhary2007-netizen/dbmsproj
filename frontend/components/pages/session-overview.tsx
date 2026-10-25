import type { Row } from "@/lib/api";
import { pretty } from "@/lib/api";
import { NbBadge } from "@/components/nb/badge";
import { NbButton } from "@/components/nb/button";
import { NbCard } from "@/components/nb/card";
import { NbTable } from "@/components/nb/table";
import type { ViewState } from "@/lib/data-state";

type SessionOverviewProps = {
  canManage: boolean;
  primary: boolean;
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
  canManage, primary, setEditModal, setModal, rows, events, err, loading, load,
  setSelected, setResults, setResultsLoaded, setActionMsg,
}: SessionOverviewProps) {
  const sessions = rows.map((r) => ({
    ...r,
    event_name: r.event_name || events.find((e) => e.id === r.event_id)?.name,
  }));
  const retry = () => void load();
  const state: ViewState<readonly Row[]> = loading && sessions.length === 0
    ? { status: "loading" }
    : err && sessions.length
      ? { status: "partial", data: sessions, totalCount: sessions.length, filter: { label: "sessions", clear: retry } }
      : err
        ? { status: "error", error: { message: err, retryable: true }, retry }
        : sessions.length
          ? { status: "populated", data: sessions }
          : { status: "empty", reason: "no-data" };

  return (
    <>
      <NbCard tone="cream" className="col-span-full flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="eyebrow text-[length:var(--fs-label)]">RACE CONTROL / SESSION CONTROL</p>
          <h1 className="text-[length:var(--fs-h1)] font-bold">Sessions</h1>
          <p>Schedule sessions, control the live state, and review classified results.</p>
        </div>
        {canManage ? (
          <NbButton variant={primary ? "primary" : "secondary"} data-primary={primary || undefined} onClick={() => { setEditModal(false); setModal(true); }}>Schedule session</NbButton>
        ) : (
          <NbButton variant="primary" data-primary={primary || undefined} onClick={retry} aria-label="Refresh">Refresh</NbButton>
        )}
      </NbCard>
      <NbCard tone="paper" className="min-w-0">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <span className="record-count text-[length:var(--fs-label)]">{rows.length} SESSIONS</span>
          <NbButton variant="secondary" onClick={retry} aria-label="Refresh">Refresh</NbButton>
        </div>
        <NbTable
          caption="Sessions"
          state={state}
          empty="No records returned by the API."
          sourceMessage={err || undefined}
          partialSummary={`Showing ${sessions.length} of ${sessions.length} sessions. The latest refresh failed.`}
          partialActionLabel="Retry sessions"
          partialActionAriaLabel="Retry sessions"
          columns={["event_name", "session_type", "state", "scheduled_at", "total_laps"].map((key) => ({
            key,
            title: key.replaceAll("_", " "),
            render: (row: Row) => key === "state"
              ? <NbBadge status={String(row[key] ?? "—")}>{pretty(row[key])}</NbBadge>
              : pretty(row[key]),
          }))}
          rowKey={(row) => String(row.id ?? "")}
          onSelect={(row) => {
            setSelected(String(row.id || ""));
            setResults([]);
            setResultsLoaded(false);
            setActionMsg("");
          }}
        />
      </NbCard>
    </>
  );
}
