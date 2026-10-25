"use client";
import { useAnalytics } from "@/lib/use-analytics";
import { Row } from "@/lib/api";
import { Button, DataTable, PageHeader, StateMessage } from "../ui";

export function Analytics() {
  const {
    rows, page, setPage, champ, setChamp, season, setSeason, circuit,
    setCircuit, driver, setDriver, team, setTeam, opts, error, hasQueried,
    busy, search, analyticsPages, analyticsColumns, displayAnalyticsRows,
  } = useAnalytics();
  return (
    <>
      <PageHeader
        eyebrow="CHAMPIONSHIP / PERFORMANCE"
        title="Driver analytics"
        description="Filter driver metrics using the analytics API. Results and comparisons reflect returned data."
      />
      <div className="filter-panel">
        {(
          [
            ["Championship", champ, setChamp, opts.championships],
            ["Circuit", circuit, setCircuit, opts.circuits],
            ["Driver", driver, setDriver, opts.drivers],
            ["Team", team, setTeam, opts.teams],
          ] as [string, string, (val: string) => void, Row[]][]
        ).map(([title, value, setter, items]) => (
          <label key={title}>
            {title}
            <select value={value} onChange={(e) => setter(e.target.value)}>
              <option value="">All</option>
              {items.map((r: Row) => (
                <option key={String(r.id)} value={String(r.id)}>
                  {title === "Driver" ? `${String(r.full_name || r.id)} · #${String(r.number || "—")} · ${String(r.licence_number || "")}` : String(r.name || r.full_name || r.id)}
                </option>
              ))}
            </select>
          </label>
        ))}
        <label>
          Season
          <input
            value={season}
            onChange={(e) => setSeason(e.target.value)}
            placeholder="Season"
          />
        </label>
        <Button data-primary="true" onClick={() => void search()} disabled={busy}>
          {busy ? "Loading…" : "Apply filters"}
        </Button>
      </div>
      {error && <div className="notice error-notice">{error}</div>}
      <div className="panel">
        <div className="panel-heading">
          <div>
            <div className="eyebrow">API RESULTS</div>
            <h2>{hasQueried ? `${rows.length} driver records` : "Driver records"}</h2>
          </div>
        </div>
        {busy ? (
          <StateMessage loading />
        ) : !hasQueried ? (
          <p className="muted">Apply filters to load driver analytics.</p>
        ) : (
          <DataTable
            rows={displayAnalyticsRows}
            columns={analyticsColumns}
          />
        )}
        {analyticsPages > 1 && <div className="dbms-pagination"><Button kind="secondary" disabled={page === 0} onClick={() => setPage((value) => value - 1)}>Previous</Button><span className="muted">Page {page + 1} of {analyticsPages}</span><Button kind="secondary" disabled={page >= analyticsPages - 1} onClick={() => setPage((value) => value + 1)}>Next</Button></div>}
      </div>
    </>
  );
}
