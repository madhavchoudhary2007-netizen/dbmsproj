"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api, asArray, Row } from "@/lib/api";
import { Button, DataTable } from "./ui";

type RaceState = "ACTIVE" | "PAUSED" | "SCHEDULED";
const pollingStates: RaceState[] = ["ACTIVE", "PAUSED", "SCHEDULED"];
const isPollingState = (state: unknown) => pollingStates.includes(String(state) as RaceState);

export function RaceDatabase({selectedRace = "", onSelectRace, refreshToken = 0}: {selectedRace?: string; onSelectRace?: (id: string) => void; refreshToken?: number} = {}) {
  const [races, setRaces] = useState<Row[]>([]);
  const [raceListLoading, setRaceListLoading] = useState(true);
  const [raceError, setRaceError] = useState("");
  const [selected, setSelected] = useState(selectedRace);
  const selectedRef = useRef(selectedRace);
  const selectedRaceRef = useRef(selectedRace);
  const onSelectRaceRef = useRef(onSelectRace);
  const [snapshot, setSnapshot] = useState<Record<string, unknown> | null>(null);
  const [snapshotError, setSnapshotError] = useState("");
  const [archiveLaps, setArchiveLaps] = useState<Row[]>([]);
  const [lapLoading, setLapLoading] = useState(false);
  const [lapError, setLapError] = useState("");
  const [lapRevision, setLapRevision] = useState(0);
  const [lapPage, setLapPage] = useState(0);
  const [left, setLeft] = useState(""), [right, setRight] = useState("");
  const [view, setView] = useState("timing"), [revision, setRevision] = useState(0);
  useEffect(() => {
    selectedRaceRef.current = selectedRace;
    onSelectRaceRef.current = onSelectRace;
  }, [selectedRace, onSelectRace]);
  useEffect(() => {
    if (selectedRef.current !== selectedRace) {
      selectedRef.current = selectedRace;
      setSelected(selectedRace);
    }
  }, [selectedRace]);
  useEffect(() => {
    let disposed = false;
    let timer: ReturnType<typeof setTimeout>;
    const load = async () => {
      try {
        const rows = await api<Row[]>("/dbms/races");
        if (disposed) return;
        const nextRows = asArray(rows);
        setRaces(nextRows);
        setRaceError("");
        setRaceListLoading(false);
        const preferred = selectedRaceRef.current || selectedRef.current;
        const next = nextRows.some((race) => String(race.id) === preferred)
          ? preferred
          : String(nextRows[0]?.id || "");
        selectedRef.current = next;
        setSelected(next);
        if (next !== selectedRaceRef.current) onSelectRaceRef.current?.(next);
      } catch (error) {
        if (!disposed) {
          setRaceError(error instanceof Error ? error.message : "Could not load races");
          setRaceListLoading(false);
        }
      } finally {
        if (!disposed) timer = setTimeout(load, 5000);
      }
    };
    void load();
    return () => { disposed = true; clearTimeout(timer); };
  }, [refreshToken]);
  const selectedState = races.find((race) => String(race.id) === selected)?.state;
  const selectedStateRef = useRef(selectedState);
  useEffect(() => {
    selectedStateRef.current = snapshot?.session?.state ?? selectedState;
  }, [selectedState, snapshot?.session?.state]);
  useEffect(() => {
    let disposed = false, timer: ReturnType<typeof setTimeout>;
    const load = async () => {
      try {
        const value = await api<{ session?: { state?: string } } & Record<string, unknown>>(`/dbms/races/${selected}?include_laps=false`);
        if (disposed) return;
        setSnapshot(value);
        setSnapshotError("");
        if (isPollingState(value?.session?.state)) timer = setTimeout(load, 1000);
      } catch (error) {
        if (!disposed) {
          setSnapshotError(error instanceof Error ? error.message : "Could not load race");
          timer = setTimeout(load, 3000);
        }
      }
    };
    if (selected) void load();
    return () => { disposed = true; clearTimeout(timer); };
  }, [selected, revision, refreshToken]);
  useEffect(() => {
    setSnapshot(null);
    setSnapshotError("");
    setArchiveLaps([]);
    setLapLoading(false);
    setLapError("");
    setLapPage(0);
    setLeft("");
    setRight("");
  }, [selected]);
  useEffect(() => {
    if (!selected || view !== "laps") return;
    let disposed = false;
    let timer: ReturnType<typeof setTimeout>;
    let hasLoaded = false;
    const load = async () => {
      if (!hasLoaded) setLapLoading(true);
      try {
        const value = await api<{ laps?: Row[] } & Record<string, unknown>>(`/dbms/races/${selected}/laps`);
        if (disposed) return;
        setArchiveLaps(asArray(value?.laps ?? value));
        setLapError("");
        setLapLoading(false);
        hasLoaded = true;
        if (isPollingState(selectedStateRef.current)) timer = setTimeout(load, 5000);
      } catch (error) {
        if (!disposed) {
          setLapError(error instanceof Error ? error.message : "Could not load lap archive");
          setLapLoading(false);
          hasLoaded = true;
          timer = setTimeout(load, 5000);
        }
      }
    };
    void load();
    return () => { disposed = true; clearTimeout(timer); };
  }, [selected, view, revision, lapRevision, refreshToken]);
  const drivers: Row[] = snapshot?.drivers || [];
  const a = left || String(drivers[0]?.id || "");
  const b = right || String(drivers[1]?.id || drivers[0]?.id || "");
  const name = (id: string) => String(drivers.find((d) => String(d.id) === id)?.driver_name || id || "Unknown driver");
  const comparisons = useMemo(() => {
    interface ComparisonRow {
      lap: number;
      a?: number | null;
      b?: number | null;
      sector_a?: unknown;
      sector_b?: unknown;
      delta_seconds?: number | null;
    }
    const map = new Map<number, ComparisonRow>();
    for (const lap of archiveLaps) {
      const driverId = String(lap.driver_id ?? "");
      if (![a, b].includes(driverId)) continue;
      const lapNum = Number(lap.lap ?? 0);
      const row: ComparisonRow = map.get(lapNum) || { lap: lapNum };
      const seconds = Number(lap.lap_time_ms) / 1000;
      if (a === b) {
        row.a = seconds; row.b = seconds;
        row.sector_a = lap.sector_ms; row.sector_b = lap.sector_ms;
      } else if (driverId === a) {
        row.a = seconds;
        row.sector_a = lap.sector_ms;
      } else {
        row.b = seconds;
        row.sector_b = lap.sector_ms;
      }
      map.set(lapNum, row);
    }
    return [...map.values()].sort((x, y) => x.lap - y.lap).map((row) => ({ ...row,
      delta_seconds: row.a != null && row.b != null ? Number((row.a - row.b).toFixed(3)) : null }));
  }, [archiveLaps, a, b]);
  const sessionState = String(snapshot?.session?.state || selectedState || "");
  const live = sessionState === "ACTIVE";
  const hasLiveTiming = isPollingState(sessionState);
  const statusLabel = live ? "ACTIVE · updating every second" : sessionState === "PAUSED" ? "PAUSED · polling for updates" : sessionState === "SCHEDULED" ? "SCHEDULED · polling for updates" : `${sessionState || "Race"} · saved records`;
  const timing = (snapshot?.latest || []).map((r: Row) => ({ ...r, driver_name: name(String(r.driver_id)), lap_seconds: r.last_lap_ms ? Number(Number(r.last_lap_ms) / 1000).toFixed(3) : r.lap_time_ms ? Number(Number(r.lap_time_ms) / 1000).toFixed(3) : "—", sector_times_ms: Array.isArray(r.sector_ms) ? r.sector_ms.join(" / ") : "—" }));
  const results = (snapshot?.results || []).map((r: Row) => ({ ...r, best_lap_seconds: r.lap_time_ms ? Number(Number(r.lap_time_ms) / 1000).toFixed(3) : "—" }));
  const provisional = results.some((result: Row) => result.provisional === true);
  const penalties = (snapshot?.penalties || []).map((penalty: Row) => ({
    ...penalty,
    driver_name: penalty.driver_name || drivers.find((driver) => String(driver.id) === String(penalty.driver_id))?.driver_name || "Unknown driver",
  }));
  const lapPageSize = 100;
  const lapPages = Math.max(1, Math.ceil(archiveLaps.length / lapPageSize));
  const visibleLapPage = Math.min(lapPage, lapPages - 1);
  const visibleArchiveLaps = archiveLaps.slice(visibleLapPage * lapPageSize, (visibleLapPage + 1) * lapPageSize);
  return <section className="panel race-database">
    <div className="panel-heading"><div><div className="eyebrow">RACE DATABASE EXPLORER</div><h2>Live records & race archive</h2><p className="muted">Follow MongoDB telemetry as it arrives, or inspect a completed race’s PostgreSQL classification and saved laps.</p></div></div>
    <div className="inline-form"><select aria-label="Database race" value={selected} onChange={(e) => { const next = e.target.value; selectedRef.current = next; setSelected(next); onSelectRaceRef.current?.(next); }}><option value="">Select race</option>{races.map((r) => <option key={String(r.id)} value={String(r.id)}>{String(r.event_name)} · {String(r.state)} · {String(r.total_laps)} laps · {String(r.started_at || r.scheduled_at || "").slice(0, 10)} · {String(r.id).slice(0, 8)}</option>)}</select><Button kind="secondary" onClick={() => setRevision((x) => x + 1)}>Refresh records</Button></div>
    {raceError && <div className="notice error-notice">Race list: {raceError}</div>}
    {snapshotError && <div className="notice error-notice">Race records: {snapshotError}</div>}
    {snapshot ? <>
      <div className="race-db-summary"><span className={live ? "live-dot" : ""}>{statusLabel}</span><span>MongoDB: {Number(snapshot.telemetry_count || 0).toLocaleString()} samples</span><span>{snapshot.completed_driver_laps ?? archiveLaps.length} completed driver laps</span><span>PostgreSQL: {results.length} results</span><span>Updated {new Date(snapshot.updated_at).toLocaleTimeString()}</span></div>
      {snapshot.lap_source === "historical_demo" && <p className="muted">Historical demo: these saved laps were generated from the seeded fictional race classification.</p>}
      <div className="dbms-buttons">{[["timing", live ? "Live timing records" : "Timing records"], ["laps", "Lap-by-lap comparison"], ["relational", "Incidents & pit records"]].map(([id,label]) => <Button key={id} kind={view===id ? "primary" : "secondary"} onClick={() => setView(id)}>{label}</Button>)}</div>
      {view === "timing" && <><h3>{hasLiveTiming ? "Latest telemetry per driver" : provisional ? "Provisional classification" : "Final classification"}</h3>{!hasLiveTiming && provisional && <div className="notice">Historical time and grid penalties are recorded but not applied to official order or points. Review penalties before treating this classification as final.</div>}<DataTable rows={hasLiveTiming ? timing : results} columns={hasLiveTiming ? ["position","driver_name","lap","sector","sector_times_ms","lap_seconds","elapsed_ms","speed_kph","tire_compound","pit_state","pit_box_number"] : ["position","driver_name","number","licence_number","best_lap_seconds","classified","pole","fastest_lap"]}/>{!hasLiveTiming && <><h3>Last recorded telemetry</h3><DataTable rows={timing} columns={["position","driver_name","lap","sector","sector_times_ms","elapsed_ms","lap_seconds","pit_state","pit_box_number"]}/></>}</>}
      {view === "laps" && <><div className="inline-form">{[[a,setLeft,"Compare driver A"],[b,setRight,"Compare driver B"]].map(([value,setter,label],i) => <label key={i}>{String(label)}<select aria-label={String(label)} value={String(value)} onChange={(e) => (setter as (v:string)=>void)(e.target.value)}>{drivers.map((d) => <option key={String(d.id)} value={String(d.id)}>{String(d.driver_name)} · #{String(d.number)}</option>)}</select></label>)}</div>{lapLoading && <p className="muted">Loading saved lap archive…</p>}{lapError && <div className="notice error-notice" role="alert">Lap archive: {lapError} <Button kind="secondary" onClick={() => setLapRevision((value) => value + 1)}>Retry lap archive</Button></div>}<p className="muted">Lap times in seconds. Delta = {name(a)} minus {name(b)}; a negative delta means the first driver was faster. Only completed laps are compared.</p>{comparisons.length ? <><div style={{height:300}}><ResponsiveContainer><LineChart data={comparisons}><CartesianGrid strokeDasharray="3 3" stroke="#293443"/><XAxis dataKey="lap"/><YAxis domain={["auto","auto"]} unit="s"/><Tooltip/><Line dataKey="a" name={name(a)} stroke="#e7ff6b" dot={false} connectNulls={false}/><Line dataKey="b" name={name(b)} stroke="#66c8ff" dot={false} connectNulls={false}/></LineChart></ResponsiveContainer></div><DataTable rows={comparisons.map((r) => ({lap:r.lap,driver_a_seconds:r.a?.toFixed(3),driver_b_seconds:r.b?.toFixed(3),delta_seconds:r.delta_seconds,sectors_a_ms:r.sector_a?.join(" / "),sectors_b_ms:r.sector_b?.join(" / ")}))} columns={["lap","driver_a_seconds","driver_b_seconds","delta_seconds","sectors_a_ms","sectors_b_ms"]}/></> : <div className="state">{lapLoading ? "Loading lap comparisons…" : "No completed lap measurements are stored for this race yet."}</div>}<h3>Every driver lap</h3><p className="muted">{archiveLaps.length} saved driver laps · showing {archiveLaps.length ? visibleLapPage * lapPageSize + 1 : 0}–{Math.min((visibleLapPage + 1) * lapPageSize, archiveLaps.length)}</p><DataTable rows={visibleArchiveLaps.map((lap) => ({driver_name:name(String(lap.driver_id)),lap:lap.lap,sector_1_ms:Array.isArray(lap.sector_ms)?lap.sector_ms[0]:null,sector_2_ms:Array.isArray(lap.sector_ms)?lap.sector_ms[1]:null,sector_3_ms:Array.isArray(lap.sector_ms)?lap.sector_ms[2]:null,lap_time_ms:lap.lap_time_ms,position:lap.position}))} columns={["driver_name","lap","sector_1_ms","sector_2_ms","sector_3_ms","lap_time_ms","position"]}/>{lapPages > 1 && <div className="dbms-pagination"><Button kind="secondary" disabled={visibleLapPage === 0} onClick={() => setLapPage((page) => Math.max(0, page - 1))}>Previous</Button><span className="muted">Page {visibleLapPage + 1} of {lapPages}</span><Button kind="secondary" disabled={visibleLapPage >= lapPages - 1} onClick={() => setLapPage((page) => page + 1)}>Next</Button></div>}</>}
      {view === "relational" && <><h3>Incident reports</h3><DataTable rows={snapshot.incidents} columns={["driver_name","lap","state","description"]}/><h3>Penalties</h3><DataTable rows={penalties} columns={["id","driver_name","points","time_seconds","grid_places"]}/><h3>Named pit stops</h3><DataTable rows={snapshot.pit_reservations} columns={["driver_name","team_name","box_number","allocation_source","starts_at","ends_at","status"]}/></>}
    </> : <div className="state">{selected ? "Loading race records…" : raceListLoading ? "Loading races…" : "No races available."}</div>}
  </section>;
}

const positions: Record<string, [number,number]> = {
  demo_races:[20,740],demo_race_entries:[285,740],
  championships:[20,20],race_events:[285,20],circuits:[550,20],pit_boxes:[815,20],
  race_sessions:[285,200],session_results:[550,200],pit_reservations:[815,200],
  users:[20,380],drivers:[285,380],incident_reports:[550,380],penalties:[815,380],
  teams:[20,560],team_memberships:[285,560],driver_standings:[550,560],penalty_points:[815,560],
};
export function EerDiagram() {
  const [schema, setSchema] = useState<{ columns?: Row[]; relationships?: Row[] } | null>(null), [selected, setSelected] = useState("race_sessions"), [error, setError] = useState("");
  useEffect(() => {
    let disposed = false;
    const load = () => api<{ columns?: Row[]; relationships?: Row[] }>("/dbms/eer").then((value) => { if (!disposed) { setSchema(value); setError(""); } })
      .catch((e) => { if (!disposed) setError(e.message); });
    void load();
    const timer = setInterval(load, 15000);
    return () => { disposed = true; clearInterval(timer); };
  }, []);
  const columns: Row[] = schema?.columns || [], edges: Row[] = schema?.relationships || [];
  const allTables = [...new Set(columns.map((r) => String(r.table_name)))];
  return <section className="panel"><div className="eyebrow">DATABASE MODEL</div><h2>Enhanced entity relationship diagram</h2><p className="muted">Shared by live and completed races. Click an entity to inspect its actual columns and foreign keys. Arrows run from the referencing entity to its parent; one parent can have many child records, except the unique driver → user link.</p>{error && <div className="notice error-notice">{error}</div>}
    <div className="eer-scroll"><svg viewBox="0 0 1080 1040" role="img" aria-label="ApexGrid entity relationship diagram" style={{minWidth:850,width:"100%"}}><defs><marker id="eer-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8" fill="#7b8ca3"/></marker></defs>{edges.filter((e) => positions[String(e.child)] && positions[String(e.parent)]).map((e,i) => { const c=positions[String(e.child)],p=positions[String(e.parent)];return <path key={i} d={`M${c[0]+110},${c[1]+45} L${p[0]+110},${p[1]+45}`} stroke={e.child===selected || e.parent===selected ? "#e7ff6b" : "#43536b"} opacity={e.child===selected || e.parent===selected ? 1 : .45} strokeWidth="2" markerEnd="url(#eer-arrow)"/>; })}{Object.entries(positions).map(([table,[x,y]]) => <g key={table} role="button" tabIndex={0} aria-label={`Inspect ${table}`} onClick={() => setSelected(table)} onKeyDown={(e) => {if(e.key==="Enter" || e.key===" ") setSelected(table);}} style={{cursor:"pointer"}}><rect x={x} y={y} width="225" height="95" rx="8" fill={selected===table ? "#26301e" : "#151e2a"} stroke={selected===table ? "#e7ff6b" : "#526078"}/><text x={x+12} y={y+26} fill="#f5f7fa" fontSize="14" fontWeight="600">{table}</text><text x={x+12} y={y+50} fill="#a7b3c4" fontSize="12">PK {columns.filter((c)=>c.table_name===table && c.primary_key).map((c)=>c.column_name).join(", ")}</text><text x={x+12} y={y+74} fill="#a7b3c4" fontSize="12">{edges.filter((e)=>e.child===table).length} foreign key links</text></g>)}<g><rect x="20" y="920" width="490" height="85" rx="8" fill="#182a2c" stroke="#66c8ff"/><text x="32" y="945" fill="#66c8ff" fontSize="15">MongoDB · telemetry (many samples per driver/session)</text><text x="32" y="970" fill="#a7b3c4" fontSize="13">session_id → race_sessions · driver_id → drivers</text><text x="32" y="992" fill="#a7b3c4" fontSize="12">External UUID references · laps, sectors, pace, tires</text></g><g><rect x="550" y="920" width="490" height="85" rx="8" fill="#222519" stroke="#e7ff6b"/><text x="562" y="945" fill="#e7ff6b" fontSize="15">users → disjoint role specialization</text><text x="562" y="970" fill="#a7b3c4" fontSize="13">ADMIN · STEWARD · PRINCIPAL · DRIVER</text><text x="562" y="992" fill="#a7b3c4" fontSize="12">One role per user · DRIVER profile via unique user_id</text></g></svg></div>
    <div className="callout">User specialization: ADMIN · STEWARD · PRINCIPAL · DRIVER are disjoint roles stored in users.role. Drivers extend a user through drivers.user_id; principals link through teams.principal_user_id. MongoDB telemetry references a session and driver by UUID outside PostgreSQL foreign-key enforcement.</div>
    <div className="inline-form"><label>Inspect entity<select aria-label="EER entity" value={selected} onChange={(e)=>setSelected(e.target.value)}>{allTables.map((table)=><option key={table}>{table}</option>)}</select></label></div><DataTable rows={columns.filter((c)=>c.table_name===selected)} columns={["column_name","data_type","primary_key"]}/><h3>Foreign key relationships</h3><DataTable rows={edges.filter((e)=>e.child===selected || e.parent===selected)} columns={["child","foreign_key","parent","parent_key","optional","children_per_parent"]}/>
  </section>;
}
