"use client";

import { Check } from "lucide-react";
import { NbButton } from "../nb/button";
import { NbCard } from "../nb/card";
import { NbField } from "../nb/field";
import { NbModal } from "../nb/modal";
import { StewardReport } from "./steward-report";
import { StewardSanctions } from "./steward-sanctions";
import { StewardCases } from "./steward-cases";
import { StewardRecords } from "./steward-records";
import { useStewardDesk } from "@/lib/use-steward-desk";

export function StewardDesk() {
  const {
    rows,
    drivers,
    sessions,
    error,
    loading,
    active,
    setActive,
    busy,
    notes,
    setNotes,
    points,
    setPoints,
    seconds,
    setSeconds,
    grid,
    setGrid,
    message,
    canSteward,
    records,
    load,
    report,
    decide,
  } = useStewardDesk();
  return (
    <>
      <NbCard tone="cream" className="mb-8">
        <header className="flex min-w-0 flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <p className="mb-2 text-sm font-bold uppercase">RACE CONTROL / STEWARDING</p>
            <h1 className="text-[length:var(--fs-h1)] font-bold">Steward desk</h1>
            <p className="mt-4 max-w-[68ch]">Review reported incidents and record decisions. Approved penalties update driver points and eligibility in PostgreSQL.</p>
          </div>
          <div className="flex min-h-16 w-full max-w-64 min-w-0 shrink items-center justify-center border-4 border-ink bg-red p-4 text-center text-sm font-bold uppercase text-ink sm:w-64">
            {rows.length} CASE FILES
          </div>
          {!(active && canSteward) && (canSteward ? (
            <NbButton variant="primary" data-primary="true" onClick={() => setActive({ __new: true })}>Report incident</NbButton>
          ) : (
            <NbButton variant="primary" data-primary="true" onClick={() => void load()}>Refresh</NbButton>
          ))}
        </header>
      </NbCard>
      <StewardCases
        rows={rows.map((r) => ({
            ...r,
            driver_name:
              r.driver_name ||
              drivers.find((d) => d.id === r.driver_id)?.full_name,
            session_label:
              r.session_name ||
              sessions.find((s) => s.id === r.session_id)?.session_type,
          }))}
        loading={loading}
        error={error}
        retry={() => void load()}
        onSelect={(r) => {
            setActive(r);
            setNotes("");
            setPoints(0);
            setSeconds(0);
            setGrid(0);
        }}
      />
      <StewardRecords records={records} />
      {message && <NbCard tone="cream" className="mb-4" role="status">{message}</NbCard>}
      {active && canSteward && (
        <NbModal
          open
          title={active.__new ? "Report incident" : "Incident review"}
          onClose={() => setActive(undefined)}
        >
          {active.__new ? (
            <StewardReport
              sessions={sessions}
              drivers={drivers}
              report={report}
              busy={busy}
            />
          ) : (
            <div className="decision-form">
              <p className="mb-4 min-w-0 break-words">
                <b>
                  {String(active.description || "Incident details unavailable")}
                </b>
              </p>
              <p className="muted">
                Lap {String(active.lap)} · {String(active.state)}
              </p>
              {active.state !== "OPEN" && (
                <NbCard tone="cream" className="mb-4" role="status">
                  This incident already has a decision recorded.
                </NbCard>
              )}
              <NbField id="steward-decision-notes" label="Decision notes">
                <textarea
                  className="min-h-32 w-full border-4 border-ink bg-paper p-3 text-ink"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                />
              </NbField>
              <StewardSanctions
                points={points}
                seconds={seconds}
                grid={grid}
                setPoints={setPoints}
                setSeconds={setSeconds}
                setGrid={setGrid}
              />
              <div className="form-actions">
                <NbButton
                  disabled={busy || active.state !== "OPEN"}
                  onClick={() => void decide(false)}
                  variant="danger"
                >
                  Reject report
                </NbButton>
                <NbButton
                  disabled={busy || active.state !== "OPEN"}
                  onClick={() => void decide(true)}
                  variant="primary"
                  data-primary={active.state === "OPEN" ? "true" : undefined}
                >
                  <Check size={15} /> Approve penalty
                </NbButton>
                {active.state !== "OPEN" && <NbButton variant="primary" data-primary="true" onClick={() => setActive(undefined)}>Close review</NbButton>}
              </div>
            </div>
          )}
        </NbModal>
      )}
    </>
  );
}
