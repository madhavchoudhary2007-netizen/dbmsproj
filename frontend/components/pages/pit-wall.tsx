"use client";
import { Row } from "@/lib/api";
import { usePitWall } from "@/lib/use-pit-wall";
import { DataTable, ReloadButton, StateMessage } from "@/components/ui";
import { PitStrategy } from "@/components/pages/pit-strategy";
import { NbButton } from "@/components/nb/button";
import { NbCard } from "@/components/nb/card";
import { NbField } from "@/components/nb/field";
import { NbSelect } from "@/components/nb/input";
import { NbModal } from "@/components/nb/modal";

export function PitWall() {
  const {
    boxes, res, strategy, history, strategyLoading, strategyError,
    selectedReservation, setSelectedReservation, events, sessions, event, setEvent,
    selectedSession, setSelectedSession, error, loading, saving, message, load,
    canManageReservation, updateReservation, sessionState, historyDrivers,
    clearPitWallSelection, value, statusText,
  } = usePitWall();
  return <>
    <NbCard tone="cream" className="mb-8 grid gap-4 shadow-nb-8 md:grid-cols-[minmax(0,1fr)_auto] md:items-center">
      <div className="grid gap-2">
        <p className="font-mono text-sm font-bold uppercase">RACE CONTROL / PIT WALL</p>
        <h1 className="text-3xl font-bold">Pit Wall</h1>
        <p className="max-w-3xl">Pit decisions are generated automatically from tire age and race state. No manual pit stop request is needed.</p>
      </div>
      <div className="grid min-w-0 gap-4 sm:grid-cols-2 md:col-span-2">
        <NbField id="pit-wall-event" label="Event">
          <NbSelect value={event} onChange={(e) => { clearPitWallSelection(); setSelectedSession(""); setEvent(e.target.value); void load(e.target.value, ""); }}>
            <option value="">Select event</option>{events.map((e) => <option key={String(e.id)} value={String(e.id)}>{String(e.name || e.id)} · {String(e.start_date || "").slice(0, 10)} · {String(e.id).slice(0, 8)}</option>)}
          </NbSelect>
        </NbField>
        <NbField id="pit-wall-session" label="Session">
          <NbSelect value={selectedSession} onChange={(e) => { clearPitWallSelection(); setSelectedSession(e.target.value); void load(event, e.target.value); }}>
            <option value="">Select session</option>{sessions.filter((s) => !event || s.event_id === event).map((s) => <option key={String(s.id)} value={String(s.id)}>{String(s.session_type || s.id)} · {String(s.state)} · {String(s.scheduled_at || "").slice(0, 10)} · {String(s.id).slice(0, 8)}</option>)}
          </NbSelect>
        </NbField>
      </div>
      <div className="flex flex-wrap items-center gap-4 md:col-start-2 md:justify-self-end">
        <NbCard tone="red" shadow={4} className="font-mono font-bold uppercase">{boxes.length} BOXES · {res.length} PIT {res.length === 1 ? "STOP" : "STOPS"}</NbCard>
        <ReloadButton onClick={() => void load(event, selectedSession)} data-primary={selectedReservation ? undefined : "true"} />
      </div>
    </NbCard>
    <StateMessage error={error} loading={loading} retry={() => void load()} />{message && <div className="notice">{message}</div>}

    <PitStrategy strategy={strategy} strategyLoading={strategyLoading} strategyError={strategyError} loading={loading} sessionState={sessionState} selectedSession={selectedSession} retry={() => void load(event, selectedSession)} value={value} statusText={statusText} />
    {(sessionState === "COMPLETED" || Number(history.total_stops) > 0) && <div className="panel"><div className="panel-heading"><div><div className="eyebrow">RACE HISTORY</div><h2>Completed pit stops</h2></div><span className="muted">{value(history.total_stops, " total stops")}</span></div>{historyDrivers.length ? <DataTable rows={historyDrivers} columns={["driver_name", "team_name", "stop_count", "laps"]} /> : <div className="state" role="status">No completed pit stops were recorded for this race.</div>}</div>}
    {!loading && !error && <div className="dashboard-grid"><div className="panel"><div className="panel-heading"><div><div className="eyebrow">PIT BOXES</div><h2>Selected event infrastructure</h2></div></div><DataTable rows={boxes} columns={["number", "status", "team_name", "starts_at", "ends_at"]} /></div><div className="panel"><div className="panel-heading"><div><div className="eyebrow">AUTOMATIC ALLOCATIONS</div><h2>Pit stop queue</h2></div></div><DataTable rows={res} columns={["driver_name", "team_name", "box_number", "allocation_source", "starts_at", "ends_at", "status"]} onSelect={(row) => setSelectedReservation(row)} /></div></div>}
    {selectedReservation && <NbModal open title="Pit reservation" onClose={() => setSelectedReservation(null)}><div className="grid gap-4"><div className="grid gap-2"><p className="font-bold">{String(selectedReservation.team_name || "Team")} · box {String(selectedReservation.box_number || "—")}</p><p>{String(selectedReservation.starts_at || "")} → {String(selectedReservation.ends_at || "")}</p></div><div className="grid gap-2 border-4 border-ink bg-cream p-4"><p>Status: {String(selectedReservation.status || "—")}</p><p>Allocation: {String(selectedReservation.allocation_source || "—")}</p></div><div className="flex flex-wrap gap-4">{selectedReservation.allocation_source === "MANUAL" && selectedReservation.status === "RESERVED" && canManageReservation(selectedReservation) ? <><NbButton variant="danger" disabled={saving} onClick={() => void updateReservation("CANCELLED")}>Cancel reservation</NbButton><NbButton variant="primary" disabled={saving} data-primary="true" onClick={() => void updateReservation("COMPLETED")}>Mark completed</NbButton></> : <NbButton variant="primary" data-primary="true" onClick={() => setSelectedReservation(null)}>Close reservation</NbButton>}</div></div></NbModal>}
  </>;
}
