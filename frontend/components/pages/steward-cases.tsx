"use client";

import { pretty } from "@/lib/api";
import { NbBadge } from "@/components/nb/badge";
import { NbState } from "@/components/nb/state";
import type { ViewState } from "@/lib/data-state";

type Row = Record<string, unknown>;
type Props = {
  rows: Row[];
  loading: boolean;
  error: unknown;
  retry: () => void;
  onSelect: (row: Row) => void;
};

const fields = [
  ["Driver", "driver_name"],
  ["Session", "session_label"],
  ["Lap", "lap"],
  ["Reported at", "reported_at"],
  ["Description", "description"],
] as const;

export function StewardCases({ rows, loading, error, retry, onSelect }: Props) {
  const message = error instanceof Error ? error.message : String(error ?? "Unable to load incident reports.");
  const state: ViewState<Row[]> = loading && !rows.length
    ? { status: "loading" }
    : error && !rows.length
      ? { status: "error", error: { message, retryable: true }, retry }
      : rows.length && (loading || error)
        ? { status: "partial", data: rows, filter: { label: "incident refresh", clear: retry }, totalCount: rows.length }
        : rows.length
          ? { status: "populated", data: rows }
          : { status: "empty", reason: "no-data" };
  const cases = (
    <div role="table" aria-label="Incident case files" className="grid gap-4">
      <div role="rowgroup" className="grid gap-4">
        {rows.map((row) => (
          <div
            key={pretty(row.id)} role="row" tabIndex={0}
            aria-label={`Case ${pretty(row.id)}: ${pretty(row.description)}`}
            onClick={() => onSelect(row)}
            onKeyDown={(event) => {
              if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                onSelect(row);
              }
            }}
            className="min-h-12 min-w-0 cursor-pointer border-4 border-ink bg-paper p-4 shadow-nb-4 focus-visible:outline-4 focus-visible:outline-[var(--nb-yellow)] focus-visible:outline-offset-4"
          >
            <div role="cell" className="mb-4 inline-block min-w-0 break-all border-4 border-ink bg-cream px-3 py-2 font-bold">CASE #{pretty(row.id)}</div>
            <div role="presentation" className="grid gap-3 sm:grid-cols-2">
              {fields.map(([label, key]) => (
                <div role="cell" key={key} className={key === "description" ? "min-w-0 sm:col-span-2" : "min-w-0"}>
                  <span className="block text-sm font-bold uppercase">{label}</span>
                  <span className="block min-w-0 break-words">{pretty(row[key])}</span>
                </div>
              ))}
              <div role="cell">
                <span className="mb-1 block text-sm font-bold uppercase">Status</span>
                <NbBadge status={pretty(row.state)}>{pretty(row.state)}</NbBadge>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <NbState
      state={state}
      empty="No records returned by the API."
      loadingLabel="Loading incident case files"
      skeletonRows={2}
      sourceMessage={error ? message : loading ? "Refreshing incident case files." : undefined}
      partialSummary={error ? "Showing saved case files after a refresh error." : "Showing saved case files while refreshing."}
      partialActionLabel="Try again"
      partialActionAriaLabel="Retry incident case file loading"
    >
      {() => cases}
    </NbState>
  );
}
