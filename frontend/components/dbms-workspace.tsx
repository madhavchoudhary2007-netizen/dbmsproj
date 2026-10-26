"use client";

import { useEffect, useMemo, useState } from "react";
import { api, asArray, Row } from "@/lib/api";
import dynamic from "next/dynamic";
import { Button, DataTable, Modal } from "./ui";
const RaceDatabase = dynamic(() => import("./race-database").then((mod) => mod.RaceDatabase), { loading: () => <div className="p-4 text-muted">Loading race database...</div> });
const EerDiagram = dynamic(() => import("./race-database").then((mod) => mod.EerDiagram), { loading: () => <div className="p-4 text-muted">Loading EER diagram...</div> });
const DbmsShowcase = dynamic(() => import("./dbms-showcase").then((mod) => mod.DbmsShowcase), { loading: () => <div className="p-4 text-muted">Loading showcase...</div> });

type View = "overview" | "showcase" | "race" | "tables" | "eer" | "schema" | "indexes" | "plans" | "locks" | "telemetry" | "mongo-collections" | "mongo-indexes" | "polyglot" | "operations";
const views: [View, string][] = [
  ["overview", "Overview"], ["showcase", "Showcase"], ["race", "Race records"], ["tables", "SQL tables"],
  ["eer", "EER model"], ["schema", "Schema"], ["indexes", "Indexes"],
  ["plans", "Query plans"], ["locks", "Locks"], ["telemetry", "Documents"],
  ["mongo-collections", "Collections"], ["mongo-indexes", "Indexes"],
  ["polyglot", "Cross-store"], ["operations", "Operations"],
];
const viewGroups: { label: string; views: View[] }[] = [
  { label: "Workspace", views: ["overview", "showcase"] },
  { label: "PostgreSQL", views: ["race", "tables", "eer", "schema", "indexes", "plans", "locks", "operations"] },
  { label: "MongoDB", views: ["mongo-collections", "mongo-indexes", "telemetry"] },
  { label: "Cross-store", views: ["polyglot"] },
];
const readPaths: Partial<Record<View, string>> = {
  schema: "/dbms/schema", indexes: "/dbms/indexes", locks: "/dbms/locks",
  telemetry: "/dbms/mongo/collections/telemetry?limit=50&offset=0",
  "mongo-collections": "/dbms/mongo/collections", "mongo-indexes": "/dbms/mongo/collections", polyglot: "/dbms/polyglot",
};

function viewFromHash(): View {
  const candidate = window.location.hash.slice(1) as View;
  return views.some(([id]) => id === candidate) ? candidate : "overview";
}

function formatMongoDocument(document: Row): Row {
  return {
    ...document,
    sector_ms: Array.isArray(document.sector_ms) ? document.sector_ms.join(" / ") : document.sector_ms ?? "—",
    tire_temp_c: Array.isArray(document.tire_temp_c) ? document.tire_temp_c.join(" / ") : document.tire_temp_c ?? "—",
  };
}

interface ExplainPlanNode {
  "Node Type"?: string;
  "Relation Name"?: string;
  "Index Name"?: string;
  "Startup Cost"?: number;
  "Total Cost"?: number;
  "Plan Rows"?: number;
  Plans?: ExplainPlanNode[];
  [key: string]: unknown;
}

interface TableDataResponse {
  total: number;
  rows?: Row[];
  columns?: string[];
  [key: string]: unknown;
}

function planRows(plan: ExplainPlanNode | null | undefined, depth = 0): Row[] {
  if (!plan) return [];
  return [{node: `${"  ".repeat(depth)}${plan["Node Type"] || "Unknown"}`,
    relation: plan["Relation Name"] || "—", index: plan["Index Name"] || "—",
    startup_cost: plan["Startup Cost"], total_cost: plan["Total Cost"],
    plan_rows: plan["Plan Rows"]},
    ...(plan.Plans || []).flatMap((child: ExplainPlanNode) => planRows(child, depth + 1))];
}

export function DbmsWorkspace() {
  const [view, setView] = useState<View>("overview");
  const [overview, setOverview] = useState<Record<string, unknown> | null>(null);
  const [overviewError, setOverviewError] = useState("");
  const [readData, setReadData] = useState<Record<string, unknown> | null>(null);
  const [readError, setReadError] = useState("");
  const [updatedAt, setUpdatedAt] = useState("");
  const [revision, setRevision] = useState(0);
  const [query, setQuery] = useState<"leaderboard" | "licence">("leaderboard");
  const [raceSelection, setRaceSelection] = useState("");
  const [tables, setTables] = useState<Row[]>([]);
  const [table, setTable] = useState("");
  const [tableOffset, setTableOffset] = useState(0);
  const [tableData, setTableData] = useState<TableDataResponse | null>(null);
  const [mongoOffset, setMongoOffset] = useState(0);
  const [mongoDraftFilters, setMongoDraftFilters] = useState({session_id: "", driver_id: "", lap: "", sector: ""});
  const [mongoFilters, setMongoFilters] = useState({session_id: "", driver_id: "", lap: "", sector: ""});
  const [selectedMongoDocument, setSelectedMongoDocument] = useState<Row | null>(null);
  const [championships, setChampionships] = useState<Row[]>([]);
  const [championship, setChampionship] = useState("");
  const [operation, setOperation] = useState("");
  const [operationError, setOperationError] = useState("");
  const [operationResults, setOperationResults] = useState<Record<string, Record<string, unknown>>>({});

  const selectView = (nextView: View) => {
    setView(nextView);
    setReadError("");
    if (typeof window !== "undefined") window.history.pushState(null, "", `${window.location.pathname}${window.location.search}#${nextView}`);
  };

  useEffect(() => {
    const syncView = () => setView(viewFromHash());
    syncView();
    window.addEventListener("popstate", syncView);
    window.addEventListener("hashchange", syncView);
    return () => {
      window.removeEventListener("popstate", syncView);
      window.removeEventListener("hashchange", syncView);
    };
  }, []);

  useEffect(() => {
    let disposed = false;
    let timer: ReturnType<typeof setTimeout>;
    const load = async () => {
      try {
        const value = await api<Record<string, unknown>>("/dbms/overview");
        if (!disposed) { setOverview(value); setOverviewError(""); }
      } catch (error) {
        if (!disposed) setOverviewError(error instanceof Error ? error.message : "Database status unavailable");
      } finally {
        if (!disposed) timer = setTimeout(load, 5000);
      }
    };
    void load();
    return () => { disposed = true; clearTimeout(timer); };
  }, [revision]);

  const mongoParams = new URLSearchParams({limit: "50", offset: String(mongoOffset)});
  Object.entries(mongoFilters).forEach(([key, value]) => { if (value) mongoParams.set(key, value); });
  const readPath = view === "plans" ? `/dbms/explain?query=${query}` : view === "telemetry"
    ? `/dbms/mongo/collections/telemetry?${mongoParams.toString()}`
    : readPaths[view];
  useEffect(() => {
    if (!readPath) return;
    let disposed = false;
    let timer: ReturnType<typeof setTimeout>;
    setReadData(null); setReadError("");
    const load = async () => {
      try {
        const value = await api<Record<string, unknown>>(readPath);
        if (!disposed) { setReadData(value); setUpdatedAt(new Date().toISOString()); setReadError(""); }
      } catch (error) {
        if (!disposed) setReadError(error instanceof Error ? error.message : "Could not load database view");
      } finally {
        if (!disposed) timer = setTimeout(load, view === "locks" ? 3000 : 10000);
      }
    };
    void load();
    return () => { disposed = true; clearTimeout(timer); };
  }, [readPath, revision, view]);

  useEffect(() => {
    if (view !== "tables") return;
    let disposed = false;
    let timer: ReturnType<typeof setTimeout>;
    const load = async () => {
      try {
        const value = await api<{ tables?: Row[] }>("/dbms/tables");
        if (!disposed) {
          const rows = asArray(value?.tables);
          setTables(rows);
          setTable((previous) => {
            if (rows.some((row) => row.table_name === previous)) return previous;
            setTableOffset(0);
            return String(rows[0]?.table_name || "");
          });
          setReadError("");
        }
      } catch (error) {
        if (!disposed) setReadError(error instanceof Error ? error.message : "Could not load tables");
      } finally {
        if (!disposed) timer = setTimeout(load, 10000);
      }
    };
    void load();
    return () => { disposed = true; clearTimeout(timer); };
  }, [view, revision]);

  useEffect(() => {
    if (view !== "tables" || !table) return;
    let disposed = false;
    let timer: ReturnType<typeof setTimeout>;
    setTableData(null);
    const load = async () => {
      try {
        const value = await api<TableDataResponse>(`/dbms/tables/${encodeURIComponent(table)}?limit=50&offset=${tableOffset}`);
        if (!disposed) {
          setTableData(value);
          if (value.total <= tableOffset && tableOffset > 0)
            setTableOffset(Math.max(0, Math.floor((value.total - 1) / 50) * 50));
          setReadError("");
        }
      } catch (error) {
        if (!disposed) setReadError(error instanceof Error ? error.message : "Could not load table rows");
      } finally {
        if (!disposed) timer = setTimeout(load, 5000);
      }
    };
    void load();
    return () => { disposed = true; clearTimeout(timer); };
  }, [view, table, tableOffset, revision]);

  useEffect(() => {
    if (view !== "operations") return;
    let disposed = false;
    setOperationError("");
    api("/championships?limit=200&offset=0").then((rows) => {
      if (disposed) return;
      const available = asArray(rows);
      setChampionships(available);
      setChampionship((selected) => available.some((row) => String(row.id) === selected)
        ? selected : "");
    }).catch((error) => {
      if (!disposed) setOperationError(error instanceof Error ? error.message : "Could not load championships");
    });
    return () => { disposed = true; };
  }, [view, revision]);

  const runOperation = async (key: string, path: string) => {
    setOperation(key); setOperationError("");
    try {
      const result = await api<Record<string, unknown>>(path, {method: "POST"});
      setOperationResults((previous) => ({...previous, [key]: result}));
      setRevision((previous) => previous + 1);
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Operation failed");
    } finally {
      setOperation("");
    }
  };
  const inspectRows = useMemo(() => (tableData?.rows || []).map((row: Row) => Object.fromEntries(
    Object.entries(row).map(([key, value]) => [key, value && typeof value === "object" ? JSON.stringify(value) : value])
  )), [tableData]);
  const statusCards = [
    ["Active sessions", overview?.active_sessions], ["Completed sessions", overview?.completed_sessions],
    ["Open incidents", overview?.open_incidents], ["Reserved pit stops", overview?.reserved_pit_stops],
    ["Completed pit stops", overview?.completed_pit_stops], ["Official results", overview?.official_results],
    ["Mongo samples", overview?.telemetry_samples],
  ];
  const operations = [
    ["constraint", "Constraint check", "Tries an invalid driver number in a savepoint.", "/dbms/constraint-demo"],
    ["transaction", "Transaction rollback", "Writes a temporary row, then rolls back its savepoint.", "/dbms/transaction-demo"],
    ["lock", "Pit box lock", "Runs two conflicting reservations and measures the database wait.", "/dbms/lock-demo"],
  ];

  return <div className="dbms-workspace">
    <section className="panel dbms-status-panel">
      <div className="panel-heading"><div><div className="eyebrow">CONNECTED DATABASES</div><h2>Live system state</h2></div><span className="muted">{overview?.updated_at ? `Updated ${new Date(String(overview.updated_at)).toLocaleTimeString()}` : "Connecting…"}</span></div>
      {overviewError && <div className="notice error-notice">{overviewError}</div>}
      <div className="dbms-status-grid">{statusCards.map(([label, value]) => <div className="dbms-stat" key={String(label)}><small>{String(label)}</small><strong>{value == null ? "—" : String(Number(value).toLocaleString())}</strong></div>)}</div>
      <div className="dbms-connection"><span>PostgreSQL · {overview?.postgres ? String(overview.postgres) : "checking"}</span><span>MongoDB · {overview?.mongodb ? String(overview.mongodb) : "checking"}</span></div>
    </section>
    <nav className="dbms-workspace-nav" aria-label="Database views">
      {viewGroups.map((group) => <div className="dbms-view-group" key={group.label}>
        <span className="eyebrow">{group.label}</span>
        <div className="dbms-view-buttons">{group.views.map((id) => {
          const label = views.find(([viewId]) => viewId === id)?.[1] || id;
          return <button key={id} type="button" className={view === id ? "is-active" : ""} aria-current={view === id ? "page" : undefined} onClick={() => selectView(id)}>{label}</button>;
        })}</div>
      </div>)}
    </nav>
    <div className="dbms-workspace-toolbar"><div><span className="eyebrow">CURRENT VIEW</span><h2>{views.find(([id]) => id === view)?.[1]}</h2></div><div className="dbms-workspace-tools"><span className="muted">{updatedAt && !["overview","showcase","race","eer","operations"].includes(view) ? `Updated ${new Date(updatedAt).toLocaleTimeString()} · auto refresh` : view === "race" ? "Live races refresh automatically" : view === "operations" ? "Actions run on demand" : "Live status refreshes every 5 seconds"}</span><Button kind="secondary" onClick={() => setRevision((value) => value + 1)}>Refresh</Button></div></div>
    {readError && <div className="notice error-notice">{readError}</div>}
    {view === "overview" && <section className="panel"><div className="eyebrow">WORKSPACE</div><h2>Database views and operations</h2><p className="muted">Choose a view above to inspect actual PostgreSQL or MongoDB records. Live status updates every five seconds; race records, table rows and read-only diagnostics refresh while their view is open. Write demonstrations run only when selected.</p><div className="dbms-overview-links"><button type="button" onClick={() => selectView("showcase")}>Open DBMS showcase →</button><button type="button" onClick={() => selectView("race")}>Open live race records →</button><button type="button" onClick={() => selectView("tables")}>Browse SQL tables →</button><button type="button" onClick={() => selectView("operations")}>Run DBMS operations →</button></div></section>}
    {view === "showcase" && <DbmsShowcase />}
    {view === "race" && <RaceDatabase selectedRace={raceSelection} onSelectRace={setRaceSelection} refreshToken={revision} />}
    {view === "eer" && <EerDiagram />}
    {view === "tables" && <section className="panel"><div className="eyebrow">POSTGRESQL / PUBLIC BASE TABLES</div><h2>Relational table browser</h2><p className="muted">Select a table for live row counts and paged records. Password hashes are hidden.</p><div className="dbms-table-picker" role="group" aria-label="Choose a PostgreSQL table">{tables.map((row) => { const name = String(row.table_name); return <button type="button" key={name} aria-pressed={table === name} className={table === name ? "is-active" : ""} onClick={() => {setTable(name); setTableOffset(0);}}>{name}<small>{String(row.row_count)} rows</small></button>; })}</div><div className="inline-form"><label>Table<select aria-label="Database table" value={table} onChange={(event) => {setTable(event.target.value); setTableOffset(0);}}>{tables.map((row) => <option key={String(row.table_name)} value={String(row.table_name)}>{String(row.table_name)} · {String(row.row_count)} rows</option>)}</select></label><span className="muted">{tableData ? `${tableData.total} rows · showing ${tableOffset + 1}–${Math.min(tableOffset + 50, tableData.total)}` : "Loading rows…"}</span></div><DataTable rows={inspectRows} columns={tableData?.columns || []}/><div className="dbms-pagination"><Button kind="secondary" disabled={tableOffset === 0} onClick={() => setTableOffset((value) => Math.max(0, value - 50))}>Previous</Button><Button kind="secondary" disabled={!tableData || tableOffset + 50 >= tableData.total} onClick={() => setTableOffset((value) => value + 50)}>Next</Button></div></section>}
    {view === "schema" && <section className="panel"><div className="eyebrow">POSTGRESQL / INFORMATION SCHEMA</div><h2>Column definitions</h2><DataTable rows={asArray(readData)} columns={["table_name","column_name","data_type","is_nullable"]}/></section>}
    {view === "indexes" && <section className="panel"><div className="eyebrow">POSTGRESQL / INDEXES</div><h2>Index definitions</h2><DataTable rows={asArray(readData)} columns={["tablename","indexname","indexdef"]}/></section>}
    {view === "plans" && <section className="panel"><div className="eyebrow">POSTGRESQL / EXPLAIN</div><h2>Query plans</h2><div className="inline-form"><label>Query<select aria-label="Query plan" value={query} onChange={(event) => setQuery(event.target.value as "leaderboard" | "licence")}><option value="leaderboard">Leaderboard</option><option value="licence">Licence lookup</option></select></label></div><DataTable rows={planRows((readData?.plan as { Plan?: ExplainPlanNode }[] | undefined)?.[0]?.Plan)} columns={["node","relation","index","startup_cost","total_cost","plan_rows"]}/><details className="dbms-details"><summary>Raw EXPLAIN response</summary><pre>{JSON.stringify(readData, null, 2)}</pre></details></section>}
    {view === "locks" && <section className="panel"><div className="eyebrow">POSTGRESQL / LIVE LOCKS</div><h2>Current database locks</h2><DataTable rows={asArray(readData)} columns={["locktype","mode","granted","relation","pid"]}/></section>}
    {view === "mongo-collections" && <section className="panel"><div className="eyebrow">MONGODB / DATABASE {String(readData?.database || "")}</div><h2>Collections</h2><p className="muted">Live document counts and index totals for each application collection.</p><DataTable rows={asArray(readData?.collections).map((collection) => ({...collection, index_count: asArray(collection.indexes).length}))} columns={["name","document_count","index_count"]}/></section>}
    {view === "mongo-indexes" && <section className="panel"><div className="eyebrow">MONGODB / TELEMETRY COLLECTION</div><h2>Collection indexes</h2><p className="muted">Index definitions reported by MongoDB for the telemetry collection.</p><DataTable rows={asArray(readData?.collections).flatMap((collection) => asArray(collection.indexes).map((index) => ({collection: collection.name, name: index.name, key: JSON.stringify(index.key), unique: index.unique ?? false, sparse: index.sparse ?? false})))} columns={["collection","name","key","unique","sparse"]}/></section>}
    {view === "telemetry" && <section className="panel"><div className="eyebrow">MONGODB / TELEMETRY COLLECTION</div><h2>Telemetry documents</h2><p className="muted">Browse actual documents, filter by race session, driver, lap or sector, and page through results. Lap time is recorded when a lap completes. Select a row to inspect its complete JSON document.</p><form className="dbms-mongo-filters" onSubmit={(event) => {event.preventDefault(); setMongoOffset(0); setMongoFilters({...mongoDraftFilters}); setSelectedMongoDocument(null);}}><label>Session ID<input value={mongoDraftFilters.session_id} onChange={(event) => setMongoDraftFilters({...mongoDraftFilters, session_id: event.target.value})} /></label><label>Driver ID<input value={mongoDraftFilters.driver_id} onChange={(event) => setMongoDraftFilters({...mongoDraftFilters, driver_id: event.target.value})} /></label><label>Lap<input type="number" min="1" value={mongoDraftFilters.lap} onChange={(event) => setMongoDraftFilters({...mongoDraftFilters, lap: event.target.value})} /></label><label>Sector<input type="number" min="1" max="3" value={mongoDraftFilters.sector} onChange={(event) => setMongoDraftFilters({...mongoDraftFilters, sector: event.target.value})} /></label><Button type="submit" kind="secondary">Apply filters</Button><Button type="button" kind="secondary" onClick={() => {const empty = {session_id: "", driver_id: "", lap: "", sector: ""}; setMongoDraftFilters(empty); setMongoFilters(empty); setMongoOffset(0); setSelectedMongoDocument(null);}}>Clear</Button></form><p className="muted">{readData ? `${Number(readData.total || 0).toLocaleString()} documents · showing ${readData.total ? mongoOffset + 1 : 0}–${Math.min(mongoOffset + 50, Number(readData.total || 0))}` : "Loading documents…"}</p><DataTable rows={asArray(readData?.documents).map(formatMongoDocument)} columns={["id","ts","session_id","driver_id","lap","sector","sector_ms","lap_time_ms","elapsed_ms","position","speed_kph","throttle_pct","brake_pct","tire_compound","tire_age_laps","tire_wear_pct","tire_temp_c","pit_state","pit_box_number","source"]} onSelect={(document) => setSelectedMongoDocument(asArray(readData?.documents).find((raw) => raw.id === document.id) || document)}/><div className="dbms-pagination"><Button kind="secondary" disabled={mongoOffset === 0} onClick={() => {setSelectedMongoDocument(null); setMongoOffset((value) => Math.max(0, value - 50));}}>Previous</Button><Button kind="secondary" disabled={!readData || mongoOffset + 50 >= Number(readData.total || 0)} onClick={() => {setSelectedMongoDocument(null); setMongoOffset((value) => value + 50);}}>Next</Button></div>{selectedMongoDocument && <Modal title={`Telemetry document · lap ${String(selectedMongoDocument.lap ?? "—")} · sector ${String(selectedMongoDocument.sector ?? "—")}`} close={() => setSelectedMongoDocument(null)}><p className="muted">MongoDB document ID: {String(selectedMongoDocument.id || "—")}</p><pre className="dbms-mongo-json">{JSON.stringify(selectedMongoDocument, null, 2)}</pre></Modal>}</section>}
    {view === "polyglot" && <section className="panel"><div className="eyebrow">POSTGRESQL + MONGODB</div><h2>Cross-store results</h2><p className="muted">Official SQL race results joined by shared session and driver IDs to recent MongoDB sample counts.</p><DataTable rows={asArray(readData?.rows).map((row) => { const tel = typeof row.telemetry === "object" && row.telemetry !== null ? (row.telemetry as Record<string, unknown>) : undefined; return { ...row, telemetry_samples: (tel?.samples as number | undefined) ?? 0, latest_sample: (tel?.latest as string | undefined) ?? "—" }; })} columns={["session_id","state","full_name","driver_id","telemetry_samples","latest_sample"]}/></section>}
    {view === "operations" && <section className="panel"><div className="eyebrow">DATABASE ACTIONS</div><h2>Transaction and rule demonstrations</h2><p className="muted">Each action returns its actual database outcome. Choose an action to run it; read-only views update automatically.</p>{operationError && <div className="notice error-notice" role="alert">{operationError}</div>}<div className="dbms-operation-grid">{operations.map(([key,title,description,path]) => <article className="dbms-operation-card" key={key}><h3>{title}</h3><p>{description}</p><Button disabled={!!operation} onClick={() => void runOperation(key,path)}>{operation === key ? "Running…" : `Run ${title.toLowerCase()}`}</Button>{operationResults[key] && <><p className="dbms-operation-outcome">{key === "constraint" ? operationResults[key].rejected ? "Constraint rejected invalid row" : "Constraint accepted row" : key === "transaction" ? operationResults[key].savepoint_rolled_back ? "Rollback verified" : "Rollback check failed" : operationResults[key].lock_wait_observed && operationResults[key].overlapping_reservation === "rejected" ? `Lock wait ${operationResults[key].lock_wait_ms} ms; overlap rejected` : "Lock check failed"}</p><details className="dbms-details"><summary>API response</summary><pre>{JSON.stringify(operationResults[key],null,2)}</pre></details></>}</article>)}</div><div className="dbms-recalculate"><h3>Recalculate standings</h3><div className="inline-form"><label>Championship<select aria-label="Championship for recalculation" value={championship} onChange={(event) => { setChampionship(event.target.value); setOperationResults((previous) => { const {recalculate: _result, ...rest} = previous; return rest; }); }}><option value="">Select championship</option>{championships.map((row) => <option key={String(row.id)} value={String(row.id)}>{String(row.name || row.id)}</option>)}</select></label><Button disabled={!championship || !!operation} onClick={() => void runOperation("recalculate", `/dbms/recalculate?championship_id=${encodeURIComponent(championship)}`)}>{operation === "recalculate" ? "Running…" : "Recalculate"}</Button></div>{operationResults.recalculate && <><p className="dbms-operation-outcome">Standings recalculated for championship {String(operationResults.recalculate.championship_id || championship)}.</p><details className="dbms-details"><summary>API response</summary><pre>{JSON.stringify(operationResults.recalculate,null,2)}</pre></details></>}</div></section>}
  </div>;
}
