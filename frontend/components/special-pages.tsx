"use client";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Activity,
  Check,
  Plus,
  Trash2,
  Play,
  Pause,
  Square,
  RefreshCw,
  Radio,
  TriangleAlert,
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { api, asArray, listAll, Row, pretty, API_BASE } from "@/lib/api";
import {
  AddButton,
  Button,
  DataTable,
  Modal,
  PageHeader,
  ReloadButton,
  ResourceEditor,
  SearchBox,
  StateMessage,
} from "./ui";
import { useAuth } from "./auth";
import { DbmsWorkspace } from "./dbms-workspace";
import { useDashboard } from "@/lib/use-dashboard";

export function Dashboard() {
  const { data, health, err, load, fetchData } = useDashboard();
  return (
    <>
      <PageHeader
        eyebrow="CONTROL ROOM / OVERVIEW"
        title="Race operations"
        description="Competition status and service health from the ApexGrid API."
        action={<ReloadButton onClick={fetchData} data-primary="true" />}
      />
      <StateMessage error={err} loading={load} retry={fetchData} />
      {data && (
        <>
          <div className="stat-grid">
            {[
              ["active_sessions", data.active_sessions],
              ["scheduled_events", data.scheduled_events],
              ["open_incidents", data.open_incidents],
              ["drivers", data.drivers],
            ].map(([k, v]) => (
              <div className="stat-card" key={String(k)}>
                <span>{String(k).replaceAll("_", " ")}</span>
                <b>{pretty(v)}</b>
                <small>API reported</small>
              </div>
            ))}
          </div>
          <div className="dashboard-grid">
            <div className="panel">
              <div className="panel-heading">
                <div>
                  <div className="eyebrow">CURRENT CONTEXT</div>
                  <h2>Race weekend</h2>
                </div>
                <span className="live-badge">
                  <i /> LIVE DATA
                </span>
              </div>
              {data.active_session ? (
                Object.entries(data.active_session).map(([k, v]) => (
                  <div className="detail-row" key={k}>
                    <span>{k.replaceAll("_", " ")}</span>
                    <b>{pretty(v)}</b>
                  </div>
                ))
              ) : (
                <p className="muted">
                  No active or paused session is currently returned by the API.
                </p>
              )}
            </div>
            <div className="panel">
              <div className="panel-heading">
                <div>
                  <div className="eyebrow">SERVICE HEALTH</div>
                  <h2>Platform status</h2>
                </div>
              </div>
              {Object.entries(health?.services || {}).map(([k, v]) => (
                <div className="detail-row" key={k}>
                  <span>{k}</span>
                  <b className={v === "up" ? "green" : ""}>{pretty(v)}</b>
                </div>
              ))}
              {health && (
                <div className="detail-row">
                  <span>overall</span>
                  <b>{pretty(health.status)}</b>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </>
  );
}
export function SessionPage() {
  const [rows, setRows] = useState<Row[]>([]),
    [events, setEvents] = useState<Row[]>([]),
    [drivers, setDrivers] = useState<Row[]>([]),
    [resultModal, setResultModal] = useState(false),
    [editModal, setEditModal] = useState(false),
    [resultsLoaded, setResultsLoaded] = useState(false),
    [err, setErr] = useState(""),
    [loading, setLoading] = useState(true),
    [selected, setSelected] = useState(""),
    [actionMsg, setActionMsg] = useState(""),
    [modal, setModal] = useState(false),
    [busy, setBusy] = useState(false),
    [simCars, setSimCars] = useState(10),
    [simCarsInitialized, setSimCarsInitialized] = useState(false),
    [simRate, setSimRate] = useState(5),
    [simMessage, setSimMessage] = useState(""),
    [results, setResults] = useState<Row[]>([]);
  const { user } = useAuth();
  const canManage = user?.role === "ADMIN";
  const canControl = user?.role === "ADMIN" || user?.role === "STEWARD";
  const load = useCallback(async () => {
    setLoading(true);
    setErr("");
    try {
      const [s, e, d] = await Promise.all([
        listAll("/sessions"),
        listAll("/events"),
        listAll("/drivers"),
      ]);
      setRows(asArray(s));
      setEvents(asArray(e));
      setDrivers(asArray(d));
    } catch (x) {
      setErr(x instanceof Error ? x.message : "Unable to load");
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => {
    void load();
  }, [load]);
  useEffect(() => {
    if (simCarsInitialized || !drivers.length) return;
    const eligible = drivers.filter((d) => d.eligibility === "ACTIVE").length;
    setSimCars(Math.max(1, Math.min(10, eligible || 1)));
    setSimCarsInitialized(true);
  }, [drivers, simCarsInitialized]);
  const current = rows.find((r) => r.id === selected);
  const perform = async (action: string) => {
    if (!selected) return;
    setActionMsg("");
    try {
      await api(`/sessions/${selected}/action`, {
        method: "POST",
        body: JSON.stringify({ action }),
      });
      setActionMsg(`Session ${action} request completed.`);
      await load();
    } catch (e) {
      setActionMsg(e instanceof Error ? e.message : "Action failed");
    }
  };
  const saveResult = async (v: Row) => {
    if (!selected) return;
    setBusy(true);
    try {
      const saved = await api(`/sessions/${selected}/results`, {
        method: "POST",
        body: JSON.stringify([
          {
            ...v,
            pole: v.pole === "true" || v.pole === true,
            fastest_lap: v.fastest_lap === "true" || v.fastest_lap === true,
            classified: v.classified === "true" || v.classified === true,
          },
        ]),
      });
      setResults(asArray(saved));
      setResultsLoaded(true);
      setResultModal(false);
    } finally {
      setBusy(false);
    }
  };
  const simulate = async (action: string) => {
    if (!selected) return;
    setSimMessage("");
    try {
      const response = await api<{ state?: string; cars?: number; rate_hz?: number }>(`/sessions/${selected}/simulate`, {
        method: "POST",
        body: JSON.stringify({ action, cars: simCars, rate_hz: simRate }),
      });
      setSimMessage(
        `Simulator ${response.state}. ${response.cars} cars at ${response.rate_hz} Hz.`,
      );
      await load();
    } catch (e) {
      setSimMessage(
        e instanceof Error ? e.message : "Simulator request failed",
      );
    }
  };
  const getResults = async () => {
    if (!selected) return;
    try {
      setResults(asArray(await api(`/sessions/${selected}/results`)));
      setResultsLoaded(true);
    } catch (e) {
      setSimMessage(e instanceof Error ? e.message : "Results request failed");
    }
  };
  const fields = [
    {
      name: "event_id",
      required: true,
      options: events.map((e) => ({
        value: String(e.id),
        label: `${String(e.name || "Event")} · round ${String(e.round_number ?? "—")}`,
      })),
    },
    {
      name: "session_type",
      required: true,
      options: ["PRACTICE", "QUALIFYING", "RACE"],
    },
    { name: "scheduled_at", type: "datetime-local", required: true },
    { name: "total_laps", type: "number", min: 1, max: 72 },
    { name: "safety_car", options: ["false", "true"] },
  ];
  const save = async (v: Row) => {
    setBusy(true);
    try {
      const payload = Object.fromEntries(
        fields
          .map(({ name }) => [name, v[name]] as const)
          .filter(([, value]) => value !== undefined),
      );
      await api(editModal && selected ? `/sessions/${selected}` : "/sessions", {
        method: editModal ? "PATCH" : "POST",
        body: JSON.stringify(payload),
      });
      setModal(false);
      setEditModal(false);
      await load();
    } finally {
      setBusy(false);
    }
  };
  const deleteSession = async () => {
    if (!selected) return;
    setBusy(true);
    try {
      await api(`/sessions/${selected}`, { method: "DELETE" });
      setSelected("");
      setResults([]);
      await load();
    } catch (e) {
      setActionMsg(e instanceof Error ? e.message : "Unable to delete session");
    } finally {
      setBusy(false);
    }
  };
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
      {actionMsg && <div className="notice">{actionMsg}</div>}
      {current && (
        <div className="panel session-control">
          <div className="panel-heading">
            <div>
              <div className="eyebrow">SELECTED SESSION</div>
              <h2>
                {String(
                  current.event_name || current.session_type || "Session",
                )}
              </h2>
            </div>
            <span className="state-pill">{String(current.state)}</span>
          </div>
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
          {canControl && (
            <div className="sim-controls">
              <div>
                <div className="eyebrow">TELEMETRY SIMULATOR</div>
                <p className="muted">
                  Start telemetry simulation for the selected session.
                </p>
              </div>
              <label>
                Cars
                <input
                  type="number"
                  min="1"
                  max={Math.max(
                    1,
                    drivers.filter((d) => d.eligibility === "ACTIVE").length,
                  )}
                  value={simCars}
                  onChange={(e) => setSimCars(+e.target.value)}
                />
                <small className="muted">
                  {drivers.filter((d) => d.eligibility === "ACTIVE").length}{" "}
                  eligible drivers available
                </small>
              </label>
              <label>
                Rate Hz
                <input
                  type="number"
                  min="1"
                  value={simRate}
                  onChange={(e) => setSimRate(+e.target.value)}
                />
              </label>
              <div className="action-row">
                {["start", "pause", "resume", "stop", "reset"].map((a) => (
                  <Button
                    key={a}
                    disabled={(a === "start" && current?.state !== "ACTIVE") || (a === "reset" && current?.state !== "PAUSED")}
                    kind={a === "stop" ? "danger" : "secondary"}
                    onClick={() => void simulate(a)}
                  >
                    {a}
                  </Button>
                ))}
              </div>
            </div>
          )}
          {simMessage && <div className="notice">{simMessage}</div>}
          {resultsLoaded && results.length === 0 && (
            <StateMessage empty="No result rows are recorded for this session." />
          )}
          {results.length > 0 && (
            <div className="results-table">
              {results.some((result) => result.provisional === true) && (
                <div className="notice">
                  Historical time and grid penalties are recorded but not applied to official order or points. Review the penalties before treating results as final.
                </div>
              )}
              <div className="panel-heading">
                <div>
                  <div className="eyebrow">
                    {results.some((result) => result.provisional === true)
                      ? "PROVISIONAL RESULTS"
                      : "OFFICIAL RESULTS"}
                  </div>
                  <h2>{results.length} classified entries</h2>
                </div>
                {canControl && (
                  <Button onClick={() => setResultModal(true)}>
                    Update a result
                  </Button>
                )}
              </div>
              <DataTable
                rows={results}
                columns={Object.keys(results[0]).filter(
                  (k) => typeof results[0][k] !== "object",
                )}
              />
            </div>
          )}
          {canManage && (
            <div className="form-actions destructive-row">
              <Button
                kind="danger"
                disabled={busy}
                onClick={() => void deleteSession()}
              >
                Delete session
              </Button>
            </div>
          )}
          {resultModal && canControl && (
            <Modal
              title="Add or update session result"
              close={() => setResultModal(false)}
            >
              <ResourceEditor
                fields={[
                  {
                    name: "driver_id",
                    required: true,
                    options: drivers.map((d) => ({
                      value: String(d.id),
                      label: `${String(d.number || "#—")} · ${String(d.full_name || "Driver")}`,
                    })),
                  },
                  { name: "position", type: "number", required: true },
                  { name: "lap_time_ms", type: "number" },
                  { name: "pole", options: ["false", "true"] },
                  { name: "fastest_lap", options: ["false", "true"] },
                  { name: "classified", options: ["true", "false"] },
                ]}
                save={saveResult}
                busy={busy}
              />
            </Modal>
          )}
        </div>
      )}
      {modal && canManage && (
        <Modal
          title={editModal ? "Edit session" : "Schedule session"}
          close={() => setModal(false)}
        >
          <div className="form-hint">
            Event IDs are taken from the event records loaded above.
          </div>
          <ResourceEditor
            fields={fields}
            initial={editModal ? current : undefined}
            save={save}
            busy={busy}
          />
        </Modal>
      )}
    </>
  );
}
export function StewardDesk() {
  const [rows, setRows] = useState<Row[]>([]),
    [drivers, setDrivers] = useState<Row[]>([]),
    [sessions, setSessions] = useState<Row[]>([]),
    [error, setError] = useState(""),
    [loading, setLoading] = useState(true),
    [active, setActive] = useState<Row | undefined>(),
    [busy, setBusy] = useState(false),
    [notes, setNotes] = useState(""),
    [points, setPoints] = useState(0),
    [seconds, setSeconds] = useState(0),
    [grid, setGrid] = useState(0),
    [message, setMessage] = useState("");
  const { user } = useAuth();
  const canSteward = user?.role === "ADMIN" || user?.role === "STEWARD";
  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [i, d, s] = await Promise.all([
        listAll("/incidents"),
        listAll("/drivers"),
        listAll("/sessions"),
      ]);
      setRows(asArray(i));
      setDrivers(asArray(d));
      setSessions(asArray(s));
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to load incidents");
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => {
    void load();
  }, [load]);
  const report = async (v: Row) => {
    setBusy(true);
    try {
      await api("/incidents", { method: "POST", body: JSON.stringify(v) });
      setActive(undefined);
      await load();
    } finally {
      setBusy(false);
    }
  };
  const decide = async (approve: boolean) => {
    if (!active) return;
    setBusy(true);
    setMessage("");
    try {
      const result = await api<{ driver?: { season_points?: number | string; eligibility?: string } }>(`/incidents/${active.id}/decision`, {
        method: "POST",
        body: JSON.stringify({
          approve,
          notes,
          points,
          time_seconds: seconds,
          grid_places: grid,
        }),
      });
      setMessage(
        `Decision recorded. Current driver points: ${result.driver?.season_points ?? "reported by API"} · eligibility: ${result.driver?.eligibility ?? "updated by database trigger"}`,
      );
      setActive(undefined);
      setNotes("");
      setPoints(0);
      setSeconds(0);
      setGrid(0);
      await load();
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Decision failed");
    } finally {
      setBusy(false);
    }
  };
  return (
    <>
      <PageHeader
        eyebrow="RACE CONTROL / STEWARDING"
        title="Steward desk"
        description="Review reported incidents and record decisions. Approved penalties update driver points and eligibility in PostgreSQL."
        action={
          canSteward ? (
            <AddButton
              onClick={() => setActive({ __new: true })}
              children="Report incident"
            />
          ) : null
        }
      />
      <StateMessage error={error} loading={loading} retry={() => void load()} />
      {!error && !loading && (
        <DataTable
          rows={rows.map((r) => ({
            ...r,
            driver_name:
              r.driver_name ||
              drivers.find((d) => d.id === r.driver_id)?.full_name,
            session_label:
              r.session_name ||
              sessions.find((s) => s.id === r.session_id)?.session_type,
          }))}
          columns={[
            "reported_at",
            "session_label",
            "driver_name",
            "lap",
            "description",
            "state",
          ]}
          onSelect={(r) => {
            setActive(r);
            setNotes("");
            setPoints(0);
            setSeconds(0);
            setGrid(0);
          }}
        />
      )}
      {message && <div className="notice">{message}</div>}
      {active && canSteward && (
        <Modal
          title={active.__new ? "Report incident" : "Incident review"}
          close={() => setActive(undefined)}
        >
          {active.__new ? (
            <ResourceEditor
              fields={[
                {
                  name: "session_id",
                  required: true,
                  options: sessions.map((s) => ({
                    value: String(s.id),
                    label: `${String(s.event_name || "Event")} · ${String(s.session_type || "Session")} · ${String(s.state || "")} · ${String(s.scheduled_at || "").slice(0, 10)} · ${String(s.id).slice(0, 8)}`,
                  })),
                },
                {
                  name: "driver_id",
                  required: true,
                  options: drivers.map((d) => ({
                    value: String(d.id),
                    label: `${String(d.number || "#—")} · ${String(d.full_name || "Driver")}`,
                  })),
                },
                { name: "lap", type: "number", required: true },
                { name: "description", required: true },
              ]}
              save={report}
              busy={busy}
            />
          ) : (
            <div className="decision-form">
              <p>
                <b>
                  {String(active.description || "Incident details unavailable")}
                </b>
              </p>
              <p className="muted">
                Lap {String(active.lap)} · {String(active.state)}
              </p>
              {active.state !== "OPEN" && (
                <div className="notice">
                  This incident already has a decision recorded.
                </div>
              )}
              <label>
                Decision notes
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                />
              </label>
              <div className="form-grid three">
                <label>
                  Penalty points
                  <input
                    type="number"
                    min="0"
                    value={points}
                    onChange={(e) => setPoints(+e.target.value)}
                  />
                </label>
                <label>
                  Time penalty (seconds)
                  <input
                    type="number"
                    min="0"
                    value={seconds}
                    onChange={(e) => setSeconds(+e.target.value)}
                    disabled
                    aria-describedby="sanction-limit-explanation"
                  />
                </label>
                <label>
                  Grid places
                  <input
                    type="number"
                    min="0"
                    value={grid}
                    onChange={(e) => setGrid(+e.target.value)}
                    disabled
                    aria-describedby="sanction-limit-explanation"
                  />
                </label>
              </div>
              <p id="sanction-limit-explanation" className="muted">
                Official timing/grid enforcement is unavailable. Use penalty points and notes for now.
              </p>
              <div className="form-actions">
                <Button
                  disabled={busy || active.state !== "OPEN"}
                  onClick={() => void decide(false)}
                  kind="secondary"
                >
                  Reject report
                </Button>
                <Button
                  disabled={busy || active.state !== "OPEN"}
                  onClick={() => void decide(true)}
                  kind="danger"
                >
                  <Check size={15} /> Approve penalty
                </Button>
              </div>
            </div>
          )}
        </Modal>
      )}
    </>
  );
}
export function LiveTiming() {
  const [sessions, setSessions] = useState<Row[]>([]),
    [demoRaces, setDemoRaces] = useState<Row[]>([]),
    [session, setSession] = useState(""),
    [sessionDrivers, setSessionDrivers] = useState<Row[]>([]),
    [driver, setDriver] = useState(""),
    [packets, setPackets] = useState<Row[]>([]),
    [completedLaps, setCompletedLaps] = useState<Row[]>([]),
    [liveIncidents, setLiveIncidents] = useState<Row[]>([]),
    [livePitStops, setLivePitStops] = useState<Row[]>([]),
    [recordsError, setRecordsError] = useState(""),
    [snapshot, setSnapshot] = useState<Record<string, unknown> | null>(null),
    [timing, setTiming] = useState<{ cars?: Row[]; safety_car?: boolean; [key: string]: unknown }>({ cars: [], safety_car: false }),
    [status, setStatus] = useState("Choose an active session"),
    [error, setError] = useState(""),
    [demoBusy, setDemoBusy] = useState(false),
    [showCompletedDemos, setShowCompletedDemos] = useState(false),
    [showAllLaps, setShowAllLaps] = useState(false),
    [deleteRace, setDeleteRace] = useState<Row | null>(null),
    [demoMessage, setDemoMessage] = useState("");
  const { user } = useAuth();
  const canManageDemos = user?.role === "ADMIN" || user?.role === "STEWARD";
  const autoFollow = useRef(true);
  const listRequest = useRef(0);
  const errorSource = useRef<"lists" | "snapshot" | "demo" | "">("");
  const reportError = useCallback((source: "lists" | "snapshot" | "demo", message: string) => {
    errorSource.current = source;
    setError(message);
  }, []);
  const clearError = useCallback((source?: "lists" | "snapshot" | "demo") => {
    if (!source || errorSource.current === source) {
      errorSource.current = "";
      setError("");
    }
  }, []);
  const refreshLists = useCallback(async () => {
    const request = ++listRequest.current;
    const [s, r] = await Promise.all([
      listAll("/sessions"),
      listAll("/demo-races"),
    ]);
    const sessionRows = asArray(s);
    const raceRows = asArray(r);
    if (request === listRequest.current) {
      setSessions(sessionRows);
      setDemoRaces(raceRows);
      clearError("lists");
    }
    return { sessionRows, raceRows, current: request === listRequest.current };
  }, [clearError]);
  useEffect(() => {
    let disposed = false;
    refreshLists()
      .then(({ sessionRows, raceRows, current }) => {
        if (disposed || !current || !autoFollow.current) return;
        const activeDemo = raceRows.find((r: Row) => r.state === "ACTIVE");
        const active = activeDemo
          ? sessionRows.find((r: Row) => String(r.id) === String(activeDemo.session_id))
          : sessionRows.find((r: Row) => r.state === "ACTIVE");
        if (active) setSession(String(active.id));
      })
      .catch((e) => { if (!disposed) reportError("lists", e instanceof Error ? e.message : "Unable to load live sessions"); });
    return () => { disposed = true; };
  }, [refreshLists, reportError]);
  useEffect(() => {
    let disposed = false;
    let timer: ReturnType<typeof setTimeout>;
    const poll = async () => {
      try {
        const { sessionRows, raceRows, current } = await refreshLists();
        if (!disposed && current && autoFollow.current) {
          const active = raceRows.find((race: Row) => race.state === "ACTIVE");
          if (active) {
            const selected = sessionRows.find((row: Row) => String(row.id) === session);
            if (!selected || selected.state === "COMPLETED") {
              const nextSession = String(active.session_id);
              if (nextSession !== session) {
                setSession(nextSession);
                setDriver("");
              }
            }
          }
        }
      } catch {}
      if (!disposed) timer = setTimeout(() => { void poll(); }, 5000);
    };
    timer = setTimeout(() => { void poll(); }, 5000);
    return () => { disposed = true; listRequest.current += 1; clearTimeout(timer); };
  }, [refreshLists, session]);
  useEffect(() => {
    if (!session) { clearError("snapshot"); setCompletedLaps([]); setLiveIncidents([]); setLivePitStops([]); setRecordsError(""); return; }
    let alive = true;
    setCompletedLaps([]);
    setLiveIncidents([]);
    setLivePitStops([]);
    setRecordsError("");
    clearError("snapshot");
    let timer: ReturnType<typeof setTimeout> | undefined;
    const load = async () => {
      try {
        const value = await api<{ laps?: Row[]; incidents?: Row[]; pit_reservations?: Row[] }>(`/sessions/${session}/laps`);
        if (alive) {
          setCompletedLaps(asArray(value.laps));
          setLiveIncidents(asArray(value.incidents));
          setLivePitStops(asArray(value.pit_reservations));
          setRecordsError("");
        }
      } catch (e) {
        if (alive) setRecordsError(e instanceof Error ? e.message : "Unable to load lap and race-control records");
      } finally {
        if (alive) timer = setTimeout(() => { void load(); }, 5000);
      }
    };
    void load();
    return () => { alive = false; if (timer) clearTimeout(timer); };
  }, [clearError, session]);
  const createDemoRace = async () => {
    setDemoBusy(true);
    clearError();
    setDemoMessage("");
    try {
      const created = await api<{ session_id?: string | number; event_name?: string; car_count?: number } & Record<string, unknown>>("/demo-races", {
        method: "POST",
        body: JSON.stringify({}),
      });
      const { sessionRows } = await refreshLists();
      const newSession = sessionRows.find((r) => String(r.id) === String(created.session_id));
      if (newSession) setSession(String(newSession.id));
      setDriver("");
      setDemoMessage(`${created.event_name || "Generated race"} is live with ${created.car_count} cars.`);
    } catch (e) {
      reportError("demo", e instanceof Error ? e.message : "Unable to create live race");
    } finally {
      setDemoBusy(false);
    }
  };
  const removeDemoRace = async () => {
    if (!deleteRace) return;
    const race = deleteRace;
    setDemoBusy(true);
    clearError();
    try {
      await api(`/demo-races/${encodeURIComponent(String(race.session_id))}`, { method: "DELETE" });
      const { sessionRows, raceRows } = await refreshLists();
      if (session === String(race.session_id)) {
        const activeDemo = raceRows.find((r: Row) => r.state === "ACTIVE");
        const next = activeDemo && sessionRows.find((r) => String(r.id) === String(activeDemo.session_id));
        const nextSession = String(next?.id || sessionRows.find((r: Row) => r.state === "ACTIVE")?.id || "");
        setSession(nextSession);
        if (!nextSession) {
          setPackets([]);
          setTiming({ cars: [], safety_car: false });
          setSnapshot(null);
          setStatus("Choose an active session");
        }
        setDriver("");
      }
      setDeleteRace(null);
      setDemoMessage("Generated race deleted.");
    } catch (e) {
      reportError("demo", e instanceof Error ? e.message : "Unable to delete generated race");
    } finally {
      setDemoBusy(false);
    }
  };
  useEffect(() => {
    if (!session) { setStatus("Choose an active session"); return; }
    setStatus("Connecting · live stream");
    setSessionDrivers([]);
    setPackets([]);
    setTiming({ cars: [], safety_car: false });
    setSnapshot(null);
    let alive = true,
      ws: WebSocket | undefined,
      timer: ReturnType<typeof setTimeout> | undefined,
      attempt = 0,
      startedAt: string | undefined,
      refreshRequest = 0,
      sessionState = "",
      streamConnected = false;
    const updateStreamStatus = () => {
      if (sessionState === "COMPLETED") setStatus("Completed · final timing");
      else if (sessionState === "PAUSED") setStatus(streamConnected ? "Paused · stream connected" : "Paused · reconnecting");
      else if (sessionState === "SCHEDULED") setStatus("Scheduled · waiting to start");
      else if (sessionState === "CANCELLED") setStatus("Cancelled · stream stopped");
      else setStatus(streamConnected ? "Connected · live stream" : "Connecting · live stream");
    };
    const belongsToCurrentRun = (packet: Row) => {
      if (String(packet.session_id || session) !== session) return false;
      if (!startedAt || !packet.ts) return true;
      const packetTime = new Date(String(packet.ts)).getTime();
      const runStart = new Date(String(startedAt)).getTime();
      return (
        !Number.isFinite(packetTime) ||
        !Number.isFinite(runStart) ||
        packetTime >= runStart
      );
    };
    const refresh = async () => {
      const request = ++refreshRequest;
      try {
        const s = await api<{ session?: Row; drivers?: Row[]; packets?: Row[] } & Record<string, unknown>>(`/sessions/${session}/live`);
        if (!alive || request !== refreshRequest) return;
        if (alive) {
          const sessionData = s.session || s;
          sessionState = String(sessionData.state || sessionState);
          setSnapshot(sessionData);
          setSessionDrivers(asArray(s.drivers));
          startedAt = (sessionData.started_at as string | undefined) || startedAt;
          setTiming((prev) => ({
            ...prev,
            safety_car: (s.session?.safety_car as boolean | undefined) ?? prev.safety_car,
          }));
          if (Array.isArray(s.packets))
            setPackets(s.packets.filter(belongsToCurrentRun));
          clearError("snapshot");
          updateStreamStatus();
          if (sessionState === "COMPLETED" || sessionState === "CANCELLED")
            ws?.close();
        }
      } catch (e) {
        if (alive && request === refreshRequest)
          reportError("snapshot", e instanceof Error ? e.message : "Unable to fetch snapshot");
      }
    };
    const connect = () => {
      if (!alive) return;
      const wsBase = API_BASE.replace(/^http/, "ws");
      ws = new WebSocket(`${wsBase}/api/ws/sessions/${session}`);
      ws.onopen = () => {
        if (!alive) return;
        attempt = 0;
        streamConnected = true;
        updateStreamStatus();
      };
      ws.onmessage = (e) => {
        if (!alive) return;
        try {
          const msg = JSON.parse(e.data);
          if (
            msg.type === "session.state" &&
            String(msg.session_id || session) === session
          ) {
            const stateData = msg.data || {};
            const nextStartedAt = stateData.started_at || msg.started_at;
            const startsNewRun = Boolean(nextStartedAt && startedAt && String(nextStartedAt) !== startedAt);
            const resetsRun = stateData.state === "PAUSED" &&
              Object.prototype.hasOwnProperty.call(stateData, "started_at") &&
              !stateData.started_at && Boolean(startedAt);
            if (startsNewRun || resetsRun) {
              setPackets([]);
              setCompletedLaps([]);
              setLiveIncidents([]);
              setLivePitStops([]);
              setTiming({ cars: [], safety_car: false });
              if (resetsRun) startedAt = undefined;
            }
            if (nextStartedAt) startedAt = String(nextStartedAt);
            sessionState = String(stateData.state || sessionState);
            updateStreamStatus();
            if (sessionState === "CANCELLED") ws?.close();
            void refresh();
          }
          setSnapshot((prev) => ({
            ...prev,
            ...(msg.data || {}),
            last_event: msg,
          }));
          if (
            msg.type === "timing.update" &&
            String(msg.session_id || session) === session &&
            !Array.isArray(msg.data)
          ) {
            setTiming(msg.data || { cars: [] });
          }
          if (
            msg.type === "telemetry.sample" &&
            belongsToCurrentRun(msg.data || {})
          )
            setPackets((p) => [...p, msg.data].slice(-100));
        } catch {}
      };
      ws.onerror = () => {
        if (!alive) return;
        streamConnected = false;
        if (sessionState === "COMPLETED" || sessionState === "PAUSED" || sessionState === "SCHEDULED" || sessionState === "CANCELLED") updateStreamStatus();
        else setStatus("Stream interrupted · reconnecting");
      };
      ws.onclose = () => {
        if (!alive) return;
        streamConnected = false;
        if (sessionState === "COMPLETED" || sessionState === "PAUSED" || sessionState === "SCHEDULED" || sessionState === "CANCELLED") updateStreamStatus();
        else setStatus("Disconnected · reconnecting");
        if (sessionState === "COMPLETED" || sessionState === "CANCELLED") return;
        const delay = Math.min(1000 * 2 ** attempt++, 15000);
        timer = setTimeout(() => {
          void refresh();
          connect();
        }, delay);
      };
    };
    void refresh();
    connect();
    return () => {
      alive = false;
      clearTimeout(timer);
      ws?.close();
    };
  }, [clearError, reportError, session]);
  const shown = packets.filter((p) => !driver || p.driver_id === driver);
  const namedDrivers = new Map<string, Row>();
  for (const person of sessionDrivers) namedDrivers.set(String(person.id), person);
  const latestByDriver = new Map<string, Row>();
  for (const packet of packets) {
    if (packet.driver_id) latestByDriver.set(String(packet.driver_id), packet);
  }
  const timingCars: Row[] = Array.isArray(timing.cars) ? timing.cars : [];
  const timingByDriver = new Map(
    timingCars.map((car) => [String(car.driver_id), car]),
  );
  const driverIds = new Set([
    ...latestByDriver.keys(),
    ...timingByDriver.keys(),
  ]);
  const runningOrder: Row[] = [...driverIds]
    .map((id): Row => {
      const packet = latestByDriver.get(id) || {};
      const car = timingByDriver.get(id) || {};
      const person = namedDrivers.get(id) || {};
      const laps = completedLaps
        .filter((sample) => String(sample.driver_id) === id)
        .map((sample) => Number(sample.lap_time_ms))
        .filter((time) => Number.isFinite(time) && time > 0);
      return {
        ...packet,
        ...car,
        driver_id: id,
        driver_name: person.full_name || person.number || id,
        team_name: person.team_name || "—",
        number: person.number,
        licence_number: person.licence_number || "—",
        last_lap_ms: car.last_lap_ms ?? packet.last_lap_ms ?? car.lap_time_ms ?? packet.lap_time_ms,
        best_lap_ms: laps.length ? Math.min(...laps) : undefined,
        sector_times_ms: Array.isArray(car.sector_ms)
          ? car.sector_ms.join(" / ")
          : Array.isArray(packet.sector_ms)
            ? packet.sector_ms.join(" / ")
            : undefined,
      };
    })
    .sort(
      (a: Row, b: Row) =>
        Number(a.position || 9999) - Number(b.position || 9999),
    );
  const leaderElapsed = Number(runningOrder[0]?.elapsed_ms);
  const orderRows: Row[] = runningOrder.map((car: Row, index): Row => {
    const elapsed = Number(car.elapsed_ms);
    return {
      ...car,
      gap:
        index === 0
          ? "LEADER"
          : Number.isFinite(elapsed) && Number.isFinite(leaderElapsed)
            ? Number(car.lap || 0) < Number(runningOrder[0]?.lap || 0)
              ? `+${Number(runningOrder[0]?.lap || 0) - Number(car.lap || 0)} lap${Number(runningOrder[0]?.lap || 0) - Number(car.lap || 0) === 1 ? "" : "s"}`
              : Number(car.sector || 0) < Number(runningOrder[0]?.sector || 0)
                ? `+${Number(runningOrder[0]?.sector || 0) - Number(car.sector || 0)} sector${Number(runningOrder[0]?.sector || 0) - Number(car.sector || 0) === 1 ? "" : "s"}`
                : `+${(Math.max(0, elapsed - leaderElapsed) / 1000).toFixed(3)} s`
            : "—",
    };
  });
  const chartPackets = shown.slice(-80).map((packet) => {
    const temps = Array.isArray(packet.tire_temp_c) ? packet.tire_temp_c : [];
    return {
      ...packet,
      temp_fl: temps[0],
      temp_fr: temps[1],
      temp_rl: temps[2],
      temp_rr: temps[3],
    };
  });
  const hasTireTemperatures = shown.some(
    (packet) =>
      Array.isArray(packet.tire_temp_c) && packet.tire_temp_c.length > 0,
  );
  const visibleDemoRaces = showCompletedDemos
    ? demoRaces
    : demoRaces.filter((race) => race.state === "ACTIVE" || race.state === "PAUSED")
      .concat(demoRaces.filter((race) => race.state !== "ACTIVE" && race.state !== "PAUSED").slice(0, 5));
  const selectedLaps = completedLaps.filter((lap) => !driver || String(lap.driver_id) === driver);
  const visibleLaps = showAllLaps ? selectedLaps : selectedLaps.slice(-100);
  return (
    <>
      <PageHeader
        eyebrow="RACE CONTROL / LIVE TIMING"
        title="Live session"
        description="A fresh session snapshot and MongoDB telemetry stream, updated over WebSocket."
      />
      {canManageDemos && (
        <section className="demo-race-hero panel" aria-labelledby="demo-race-title">
          <div>
            <div className="eyebrow">LIVE DEMO / READY TO RUN</div>
            <h2 id="demo-race-title">Put a full grid on track</h2>
            <p>Start a generated race with 8–16 fictional drivers and live timing. Sessions support up to 72 laps.</p>
          </div>
          <Button disabled={demoBusy} data-primary="true" onClick={() => void createDemoRace()}>
            <Plus size={15} /> {demoBusy ? "Starting race…" : "Create live race"}
          </Button>
        </section>
      )}
      {demoMessage && <div className="notice" role="status">{demoMessage}</div>}
      {demoRaces.length > 0 && (
        <section className="panel demo-races-panel" aria-labelledby="demo-races-title">
          <div className="panel-heading">
            <div><div className="eyebrow">GENERATED SESSIONS</div><h2 id="demo-races-title">Live race demos</h2></div>
            <span className="muted">{demoRaces.length} race{demoRaces.length === 1 ? "" : "s"}</span>
          </div>
          <div className="demo-race-list">
            {visibleDemoRaces.map((race: Row) => (
              <div className="demo-race-row" key={String(race.session_id)}>
                <button className="demo-race-select" onClick={() => { autoFollow.current = false; setSession(String(race.session_id)); setDriver(""); }} aria-label={`Show ${race.event_name} ${String(race.session_id).slice(0, 8)} live timing`}>
                  <span className="demo-race-name">{String(race.event_name || "Generated race")}</span>
                  <span className="demo-race-meta">{String(race.circuit_name || "Circuit pending")} · {String(race.car_count)} cars · {String(race.total_laps)} laps · {String(race.created_at || "").slice(0, 10)} · {String(race.session_id).slice(0, 8)}</span>
                </button>
                <span className={`demo-state ${race.state === "ACTIVE" ? "is-active" : ""}`}>{String(race.state)}</span>
                {canManageDemos && <button className="icon-button danger-icon" aria-label={`Delete ${race.event_name} ${String(race.session_id).slice(0, 8)}`} disabled={demoBusy} onClick={() => setDeleteRace(race)}><Trash2 size={15} /></button>}
              </div>
            ))}
          </div>
          {demoRaces.length > visibleDemoRaces.length && <Button kind="secondary" onClick={() => setShowCompletedDemos(true)}>Show all {demoRaces.length} generated races</Button>}
          {showCompletedDemos && demoRaces.length > 6 && <Button kind="secondary" onClick={() => setShowCompletedDemos(false)}>Show recent races</Button>}
        </section>
      )}
      <div className="toolbar select-toolbar">
        <label>
          Session
          <select value={session} onChange={(e) => { autoFollow.current = false; setSession(e.target.value); setDriver(""); }}>
            <option value="">Select session</option>
            {sessions.map((s) => (
              <option key={String(s.id)} value={String(s.id)}>
                {String(s.event_name || s.session_type || s.id)} · {String(s.state)} · {String(s.scheduled_at || "").slice(0, 10)} · {String(s.id).slice(0, 8)}
              </option>
            ))}
          </select>
        </label>
        <label>
          Driver
          <select value={driver} onChange={(e) => setDriver(e.target.value)}>
            <option value="">All drivers</option>
            {[...namedDrivers.values()].filter((d) => driverIds.has(String(d.id))).map((d) => (
              <option key={String(d.id)} value={String(d.id)}>
                {String(d.full_name || d.number || d.id)}
              </option>
            ))}
          </select>
        </label>
        <span className="stream-state">
          <i
            className={
              status.startsWith("Connected") ? "green-dot" : "amber-dot"
            }
          />
          {status}
        </span>
      </div>
      {error && <div className="notice error-notice">{error}</div>}
      {session && (
        <>
          {Boolean(timing.safety_car ?? snapshot?.safety_car) && (
            <div className="safety-car-banner">
              <TriangleAlert size={16} /> SAFETY CAR DEPLOYED
            </div>
          )}
          <div className="panel running-order-panel">
            <div className="panel-heading">
              <div>
                <div className="eyebrow">LIVE TIMING / RUNNING ORDER</div>
                <h2>{orderRows.length} cars on timing</h2>
              </div>
              <span className="live-badge">
                <i /> {status}
              </span>
            </div>
            {orderRows.length ? (
              <DataTable
                rows={orderRows.map((car) => ({
                  ...car,
                  position: car.position ?? "—",
                  sector: car.sector ?? "—",
                  last_lap_ms: car.last_lap_ms ?? "—",
                  best_lap_ms: car.best_lap_ms ?? "—",
                  tire_compound: car.tire_compound ?? "—",
                  tire_age_laps: car.tire_age_laps ?? "—",
                  tire_wear_pct: car.tire_wear_pct ?? "—",
                  pit_state: car.pit_state ?? "—",
                }))}
                columns={[
                  "position",
                  "number",
                  "driver_name",
                  "licence_number",
                  "team_name",
                  "gap",
                  "lap",
                  "sector",
                  "sector_times_ms",
                  "last_lap_ms",
                  "best_lap_ms",
                  "tire_compound",
                  "tire_age_laps",
                  "tire_wear_pct",
                  "pit_state",
                  "pit_box_number",
                ]}
              />
            ) : (
              <StateMessage empty="Waiting for timing and telemetry packets from this session." />
            )}
          </div>
          <div className="panel">
            <div className="panel-heading"><div><div className="eyebrow">RECORDED LAPS</div><h2>Driver lap and sector history</h2></div><span className="muted">{selectedLaps.length} completed driver laps</span></div>
            {recordsError && <div className="notice error-notice" role="status">Lap and race-control records could not be refreshed: {recordsError}. Retrying automatically in 5 seconds.</div>}
            {selectedLaps.length > 100 && <div className="inline-form"><span className="muted">Showing {showAllLaps ? "all" : "latest 100"} laps</span><Button kind="secondary" onClick={() => setShowAllLaps((value) => !value)}>{showAllLaps ? "Show latest 100" : "Show all laps"}</Button></div>}
            <DataTable rows={visibleLaps.map((lap) => ({
              driver_name: namedDrivers.get(String(lap.driver_id))?.full_name || lap.driver_id,
              lap: lap.lap,
              sector_1_ms: Array.isArray(lap.sector_ms) ? lap.sector_ms[0] : null,
              sector_2_ms: Array.isArray(lap.sector_ms) ? lap.sector_ms[1] : null,
              sector_3_ms: Array.isArray(lap.sector_ms) ? lap.sector_ms[2] : null,
              lap_time_ms: lap.lap_time_ms,
              position: lap.position,
            }))} columns={["driver_name","lap","sector_1_ms","sector_2_ms","sector_3_ms","lap_time_ms","position"]} />
          </div>
          <div className="panel">
            <div className="panel-heading"><div><div className="eyebrow">RACE CONTROL RECORDS</div><h2>Incidents and pit stops</h2></div></div>
            <h3>Incidents</h3>
            <DataTable rows={liveIncidents} columns={["driver_name","lap","description","state"]} />
            <h3>Pit stops</h3>
            <DataTable rows={livePitStops} columns={["driver_name","team_name","box_number","starts_at","ends_at","status"]} />
          </div>
          <div className="snapshot-strip">
            {Object.entries(snapshot || {})
              .filter(
                ([k, v]) =>
                  !["participants", "drivers", "timing", "safety_car"].includes(
                    k,
                  ) && typeof v !== "object",
              )
              .map(([k, v]) => (
                <div key={k}>
                  <small>{k.replaceAll("_", " ")}</small>
                  <b>{pretty(v)}</b>
                </div>
              ))}
          </div>
          {driver && shown.length > 0 && (
            <div className="telemetry-charts">
              {[
                ["speed_kph", "Speed · km/h", "#d9ff3f"],
                ["throttle_pct", "Throttle · %", "#8eafff"],
                ["brake_pct", "Brake · %", "#ff6b62"],
                ["lap_time_ms", "Lap time · ms", "#4fd4bd"],
                ["tire_wear_pct", "Tire wear · %", "#ffc45c"],
              ].map(([key, title, color]) => (
                <div className="panel chart-panel" key={key}>
                  <div className="eyebrow">SELECTED DRIVER TELEMETRY</div>
                  <h2>{title}</h2>
                  <div className="chart">
                    <ResponsiveContainer width="100%" height={190}>
                      <LineChart
                        data={chartPackets}
                        margin={{ top: 15, right: 8, bottom: 0, left: -16 }}
                      >
                        <CartesianGrid stroke="#29313a" strokeDasharray="3 4" />
                        <XAxis
                          dataKey="lap"
                          stroke="#77818b"
                          tick={{ fontSize: 9 }}
                          tickLine={false}
                        />
                        <YAxis
                          stroke="#77818b"
                          tick={{ fontSize: 9 }}
                          tickLine={false}
                        />
                        <Tooltip
                          contentStyle={{
                            background: "#11161c",
                            border: "1px solid #37414b",
                            fontSize: 10,
                          }}
                        />
                        <Line
                          type="monotone"
                          dataKey={key}
                          stroke={color}
                          dot={false}
                          connectNulls
                          strokeWidth={2}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              ))}
              {hasTireTemperatures && (
                <div className="panel chart-panel">
                  <div className="eyebrow">SELECTED DRIVER TELEMETRY</div>
                  <h2>Tire temperatures · °C</h2>
                  <div className="chart">
                    <ResponsiveContainer width="100%" height={190}>
                      <LineChart
                        data={chartPackets}
                        margin={{ top: 15, right: 8, bottom: 0, left: -16 }}
                      >
                        <CartesianGrid stroke="#29313a" strokeDasharray="3 4" />
                        <XAxis
                          dataKey="lap"
                          stroke="#77818b"
                          tick={{ fontSize: 9 }}
                          tickLine={false}
                        />
                        <YAxis
                          stroke="#77818b"
                          tick={{ fontSize: 9 }}
                          tickLine={false}
                        />
                        <Tooltip
                          contentStyle={{
                            background: "#11161c",
                            border: "1px solid #37414b",
                            fontSize: 10,
                          }}
                        />
                        <Line
                          type="monotone"
                          dataKey="temp_fl"
                          name="Front left"
                          stroke="#ff6b62"
                          dot={false}
                          connectNulls
                          strokeWidth={2}
                        />
                        <Line
                          type="monotone"
                          dataKey="temp_fr"
                          name="Front right"
                          stroke="#ffc45c"
                          dot={false}
                          connectNulls
                          strokeWidth={2}
                        />
                        <Line
                          type="monotone"
                          dataKey="temp_rl"
                          name="Rear left"
                          stroke="#8eafff"
                          dot={false}
                          connectNulls
                          strokeWidth={2}
                        />
                        <Line
                          type="monotone"
                          dataKey="temp_rr"
                          name="Rear right"
                          stroke="#4fd4bd"
                          dot={false}
                          connectNulls
                          strokeWidth={2}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}
            </div>
          )}
          <div className="panel">
            <div className="panel-heading">
              <div>
                <div className="eyebrow">LATEST TELEMETRY</div>
                <h2>{shown.length} samples in view</h2>
              </div>
              <span className="live-badge">
                <i /> {status}
              </span>
            </div>
            <DataTable
              rows={shown.slice(-30).reverse()}
              columns={[
                "ts",
                "driver_id",
                "lap",
                "sector",
                "position",
                "speed_kph",
                "throttle_pct",
                "brake_pct",
                "tire_compound",
                "pit_state",
                "pit_box_number",
                "pit_reservation_id",
              ]}
            />
          </div>
        </>
      )}
      {deleteRace && (
        <Modal title="Delete generated race?" close={() => !demoBusy && setDeleteRace(null)}>
          <div className="decision-form">
            <p>Delete <strong>{String(deleteRace.event_name || "this generated race")}</strong> and its generated drivers and telemetry? This action cannot be undone.</p>
            <div className="form-actions">
              <Button kind="secondary" disabled={demoBusy} onClick={() => setDeleteRace(null)}>Keep race</Button>
              <Button kind="danger" disabled={demoBusy} onClick={() => void removeDemoRace()}>{demoBusy ? "Deleting…" : "Delete race"}</Button>
            </div>
          </div>
        </Modal>
      )}
    </>
  );
}
export function PitWall() {
  const { user } = useAuth();
  const [boxes, setBoxes] = useState<Row[]>([]), [res, setRes] = useState<Row[]>([]),
    [strategy, setStrategy] = useState<Row[]>([]), [history, setHistory] = useState<Row>({}),
    [strategyLoading, setStrategyLoading] = useState(false), [strategyError, setStrategyError] = useState(""),
    [selectedReservation, setSelectedReservation] = useState<Row | null>(null),
    [events, setEvents] = useState<Row[]>([]), [sessions, setSessions] = useState<Row[]>([]), [teams, setTeams] = useState<Row[]>([]),
    [event, setEvent] = useState(""), [selectedSession, setSelectedSession] = useState(""), [error, setError] = useState(""),
    [loading, setLoading] = useState(false), [saving, setSaving] = useState(false), [message, setMessage] = useState("");
  const loadRequest = useRef(0);
  const load = useCallback(async (ev = "", sid = "") => {
    const request = ++loadRequest.current;
    setLoading(true); setError("");
    try {
      const [e, s, t] = await Promise.all([listAll("/events"), listAll("/sessions"), listAll("/teams")]);
      if (request !== loadRequest.current) return;
      const eventRows = asArray(e), sessionRows = asArray(s);
      const preferred = sessionRows.filter((r: Row) => r.state === "ACTIVE").sort((a: Row, b: Row) => String(b.started_at || "").localeCompare(String(a.started_at || "")))[0] || sessionRows.find((r: Row) => r.state === "SCHEDULED" && r.session_type === "RACE");
      const targetEvent = ev || String(preferred?.event_id || eventRows[0]?.id || "");
      const targetSession = sid || String(sessionRows.find((r: Row) => r.event_id === targetEvent && r.state === "ACTIVE")?.id || sessionRows.find((r: Row) => r.event_id === targetEvent && r.state === "SCHEDULED" && r.session_type === "RACE")?.id || sessionRows.find((r: Row) => r.event_id === targetEvent)?.id || "");
      setEvents(eventRows); setSessions(sessionRows); setTeams(asArray(t));
      if (targetEvent) setEvent(targetEvent);
      setSelectedSession(targetSession);
      if (targetEvent && targetSession) {
        const [b, r, strat] = await Promise.allSettled([api<Row[]>(`/pit-boxes?event_id=${encodeURIComponent(targetEvent)}`), api<Row[]>(`/pit-reservations?session_id=${encodeURIComponent(targetSession)}`), api<Row>(`/sessions/${encodeURIComponent(targetSession)}/pit-strategy`)]);
        if (request !== loadRequest.current) return;
        if (b.status === "rejected") throw b.reason;
        if (r.status === "rejected") throw r.reason;
        setBoxes(asArray(b.value)); setRes(asArray(r.value));
        if (strat.status === "fulfilled") { setStrategy(asArray(strat.value.strategy)); setHistory((strat.value.historical_summary || {}) as Row); setStrategyError(""); }
        else { setStrategy([]); setHistory({}); setStrategyError(strat.reason instanceof Error ? strat.reason.message : "Unable to load pit strategy"); }
      } else { setBoxes([]); setRes([]); setStrategy([]); setHistory({}); setStrategyError(""); }
    } catch (x) { if (request === loadRequest.current) setError(x instanceof Error ? x.message : "Unable to load pit records"); }
    finally { if (request === loadRequest.current) setLoading(false); }
  }, []);
  useEffect(() => { void load(); }, [load]);
  useEffect(() => () => { loadRequest.current += 1; }, []);
  useEffect(() => {
    if (!selectedSession) return;
    let disposed = false; let timer: ReturnType<typeof setTimeout>;
    const poll = async () => {
      const request = loadRequest.current; setStrategyLoading(true);
      try {
        const [b, r, s] = await Promise.all([api<Row[]>(`/pit-boxes?event_id=${encodeURIComponent(event)}`), api<Row[]>(`/pit-reservations?session_id=${encodeURIComponent(selectedSession)}`), api<Row>(`/sessions/${encodeURIComponent(selectedSession)}/pit-strategy`)]);
        if (!disposed && request === loadRequest.current) { setBoxes(asArray(b)); setRes(asArray(r)); setStrategy(asArray(s.strategy)); setHistory((s.historical_summary || {}) as Row); setError(""); setStrategyError(""); }
      } catch (e) { if (!disposed && request === loadRequest.current) setStrategyError(e instanceof Error ? e.message : "Unable to refresh pit strategy"); }
      finally { if (!disposed) setStrategyLoading(false); }
      if (!disposed) timer = setTimeout(() => { void poll(); }, 5000);
    };
    timer = setTimeout(() => { void poll(); }, 5000);
    return () => { disposed = true; clearTimeout(timer); };
  }, [event, selectedSession]);
  const canManageReservation = (r: Row) => user?.role === "ADMIN" || user?.role === "STEWARD" || (user?.role === "PRINCIPAL" && teams.some((team) => team.id === r.team_id && team.principal_user_id === user.id));
  const updateReservation = async (status: "CANCELLED" | "COMPLETED") => {
    if (!selectedReservation?.id) return; setSaving(true); setError("");
    try { await api(`/pit-reservations/${selectedReservation.id}`, { method: "PATCH", body: JSON.stringify({ status }) }); setSelectedReservation(null); setMessage(`Reservation ${status.toLowerCase()}.`); await load(event, selectedSession); }
    catch (e) { setError(e instanceof Error ? e.message : "Unable to update reservation"); }
    finally { setSaving(false); }
  };
  const sessionState = sessions.find((s) => String(s.id) === selectedSession)?.state || "";
  const historyDrivers = asArray(history.by_driver).map((driver) => ({ ...driver, laps: Array.isArray(driver.laps) ? driver.laps.join(", ") : "—" }));
  const clearPitWallSelection = () => {
    setBoxes([]); setRes([]); setStrategy([]); setHistory({});
    setSelectedReservation(null); setStrategyError(""); setError("");
  };
  const value = (v: unknown, suffix = "") => v == null || v === "" ? "—" : `${String(v)}${suffix}`;
  const statusText = (s: unknown) => ({ PENDING: "Stop decision due", IN_PIT: "Pit stop allocated", NOT_DUE: "Continue this stint", NO_FUTURE_STOP: "No further stop planned", NO_AUTOMATIC_STRATEGY: "No automatic strategy" } as Record<string, string>)[String(s)] || pretty(s);
  return <>
    <PageHeader eyebrow="RACE CONTROL / PIT WALL" title="Pit Wall" description="Pit decisions are generated automatically from tire age and race state. No manual pit stop request is needed." />
    <div className="toolbar select-toolbar">
      <label>Event<select value={event} onChange={(e) => { clearPitWallSelection(); setSelectedSession(""); setEvent(e.target.value); void load(e.target.value, ""); }}><option value="">Select event</option>{events.map((e) => <option key={String(e.id)} value={String(e.id)}>{String(e.name || e.id)} · {String(e.start_date || "").slice(0, 10)} · {String(e.id).slice(0, 8)}</option>)}</select></label>
      <label>Session<select value={selectedSession} onChange={(e) => { clearPitWallSelection(); setSelectedSession(e.target.value); void load(event, e.target.value); }}><option value="">Select session</option>{sessions.filter((s) => !event || s.event_id === event).map((s) => <option key={String(s.id)} value={String(s.id)}>{String(s.session_type || s.id)} · {String(s.state)} · {String(s.scheduled_at || "").slice(0, 10)} · {String(s.id).slice(0, 8)}</option>)}</select></label>
      <span className="record-count">{boxes.length} BOXES · {res.length} PIT {res.length === 1 ? "STOP" : "STOPS"}</span><ReloadButton onClick={() => void load(event, selectedSession)} data-primary="true" />
    </div>
    <StateMessage error={error} loading={loading} retry={() => void load()} />{message && <div className="notice">{message}</div>}

    <div className="panel"><div className="panel-heading"><div><div className="eyebrow">AUTOMATIC STRATEGY {strategyLoading ? "· UPDATING" : ""}</div><h2>Driver pit decisions</h2></div><span className="muted">{String(sessionState || "No session selected")}</span></div><p className="muted">The strategy engine tracks tire age and schedules stops at the configured stint target. Pit reservations are created automatically.</p>
      {strategyError ? <div className="state" role="alert"><strong>Strategy unavailable</strong><p>{strategyError}</p><button className="text-button" onClick={() => void load(event, selectedSession)}>Try again</button></div> : !selectedSession ? <div className="state" role="status">Select a session to view its automatic pit strategy.</div> : !strategy.length ? <div className="state" role="status">No driver strategy is available for this session.</div> : <div className="dashboard-grid">{strategy.map((d, i) => { const assigned = d.assigned_box as Row | null; return <article className="panel" key={String(d.driver_id || i)}><div className="panel-heading"><div><div className="eyebrow">{String(d.team_name || "Team")}{d.driver_number ? ` · #${d.driver_number}` : ""}</div><h3>{String(d.driver_name || "Driver")}</h3></div><span className="live-badge">{statusText(d.status)}</span></div><div className="detail-row"><span>Current lap</span><b>{value(d.current_lap)}</b></div><div className="detail-row"><span>Tire</span><b>{value(d.tire_compound)} · {value(d.tire_age_laps)} {Number(d.tire_age_laps) === 1 ? "lap" : "laps"}</b></div><div className="detail-row"><span>Tire wear</span><b>{value(d.tire_wear_pct, "%")}</b></div>{sessionState !== "COMPLETED" && <><div className="detail-row"><span>Recommended stop</span><b>{d.recommended_stop_lap == null ? "—" : `Lap ${d.recommended_stop_lap}`}</b></div><div className="detail-row"><span>Pit window</span><b>{d.pit_window_start_lap == null && d.pit_window_end_lap == null ? "—" : `Lap ${value(d.pit_window_start_lap)}–${value(d.pit_window_end_lap)}`}</b></div><div className="detail-row"><span>Decision in</span><b>{d.laps_until_decision == null ? "—" : `${d.laps_until_decision} ${Number(d.laps_until_decision) === 1 ? "lap" : "laps"}`}</b></div></>}<p className="muted">{String(d.reason || "Automatic strategy is monitoring this stint.")}</p>{assigned && <div className="notice">Box {value(assigned.box_number)} reserved · {String(assigned.status || "").toLowerCase()}</div>}</article>; })}</div>}
    </div>
    {(sessionState === "COMPLETED" || Number(history.total_stops) > 0) && <div className="panel"><div className="panel-heading"><div><div className="eyebrow">RACE HISTORY</div><h2>Completed pit stops</h2></div><span className="muted">{value(history.total_stops, " total stops")}</span></div>{historyDrivers.length ? <DataTable rows={historyDrivers} columns={["driver_name", "team_name", "stop_count", "laps"]} /> : <div className="state" role="status">No completed pit stops were recorded for this race.</div>}</div>}
    {!loading && !error && <div className="dashboard-grid"><div className="panel"><div className="panel-heading"><div><div className="eyebrow">PIT BOXES</div><h2>Selected event infrastructure</h2></div></div><DataTable rows={boxes} columns={["number", "status", "team_name", "starts_at", "ends_at"]} /></div><div className="panel"><div className="panel-heading"><div><div className="eyebrow">AUTOMATIC ALLOCATIONS</div><h2>Pit stop queue</h2></div></div><DataTable rows={res} columns={["driver_name", "team_name", "box_number", "allocation_source", "starts_at", "ends_at", "status"]} onSelect={(row) => setSelectedReservation(row)} /></div></div>}
    {selectedReservation && <Modal title="Pit reservation" close={() => setSelectedReservation(null)}><p>{String(selectedReservation.team_name || "Team")} · box {String(selectedReservation.box_number || "—")}</p><p className="muted">{String(selectedReservation.starts_at || "")} → {String(selectedReservation.ends_at || "")}</p><p>Status: {String(selectedReservation.status || "—")}</p><p>Allocation: {String(selectedReservation.allocation_source || "—")}</p>{selectedReservation.allocation_source === "MANUAL" && selectedReservation.status === "RESERVED" && canManageReservation(selectedReservation) && <div className="form-actions"><Button kind="danger" disabled={saving} onClick={() => void updateReservation("CANCELLED")}>Cancel reservation</Button><Button kind="secondary" disabled={saving} onClick={() => void updateReservation("COMPLETED")}>Mark completed</Button></div>}</Modal>}
  </>;
}
export function Analytics() {
  const [rows, setRows] = useState<Row[]>([]),
    [page, setPage] = useState(0),
    [champ, setChamp] = useState(""),
    [season, setSeason] = useState(""),
    [circuit, setCircuit] = useState(""),
    [driver, setDriver] = useState(""),
    [team, setTeam] = useState(""),
    [opts, setOpts] = useState<{
      championships: Row[];
      circuits: Row[];
      drivers: Row[];
      teams: Row[];
    }>({ championships: [], circuits: [], drivers: [], teams: [] }),
    [error, setError] = useState(""),
    [hasQueried, setHasQueried] = useState(false),
    [busy, setBusy] = useState(false);
  const searchRequest = useRef(0);
  const search = async () => {
    const request = ++searchRequest.current;
    setBusy(true);
    setError("");
    try {
      const p = new URLSearchParams();
      if (champ) p.set("championship_id", champ);
      if (season) p.set("season", season);
      if (circuit) p.set("circuit_id", circuit);
      if (driver) p.set("driver_id", driver);
      if (team) p.set("team_id", team);
      const result = await listAll(`/analytics/drivers?${p}`);
      if (request !== searchRequest.current) return;
      setRows(result);
      setHasQueried(true);
      setPage(0);
    } catch (e) {
      if (request === searchRequest.current) setError(e instanceof Error ? e.message : "Analytics request failed");
    } finally {
      if (request === searchRequest.current) setBusy(false);
    }
  };
  useEffect(() => {
    let disposed = false;
    Promise.all([
      listAll("/championships"),
      listAll("/circuits"),
      listAll("/drivers"),
      listAll("/teams"),
    ])
      .then(([c, ci, d, t]) => {
        if (disposed) return;
        setOpts({
          championships: asArray(c),
          circuits: asArray(ci),
          drivers: asArray(d),
          teams: asArray(t),
        });
      })
      .catch((e) => { if (!disposed) setError(e.message); });
    return () => { disposed = true; };
  }, []);
  useEffect(() => () => { searchRequest.current += 1; }, []);
  const analyticsPageSize = 50;
  const analyticsPages = Math.max(1, Math.ceil(rows.length / analyticsPageSize));
  const visibleAnalyticsRows = rows.slice(page * analyticsPageSize, (page + 1) * analyticsPageSize);
  const analyticsColumns = [
    "driver_name",
    "number",
    "team_name",
    "sessions",
    "classified",
    "best_finish",
    "wins",
    "average_best_lap_seconds",
    "points",
  ];
  const displayAnalyticsRows = visibleAnalyticsRows.map((row) => {
    const averageLapMs = row.avg_lap_time_ms;
    const averageLapSeconds =
      averageLapMs == null || averageLapMs === "" || !Number.isFinite(Number(averageLapMs))
        ? "—"
        : (Number(averageLapMs) / 1000).toFixed(3);
    return {
      ...row,
      driver_name: row.full_name || "—",
      average_best_lap_seconds: averageLapSeconds,
    };
  });
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
export function DbmsCenter() {
  const { user } = useAuth();
  if (user?.role !== "ADMIN") {
    return <>
      <PageHeader eyebrow="PLATFORM / DATABASE ENGINEERING" title="DBMS operations" description="Database diagnostics require an administrator account." />
      <StateMessage error="ADMIN role required to run database operations." />
    </>;
  }
  return <>
    <PageHeader eyebrow="PLATFORM / DATABASE ENGINEERING" title="DBMS workspace" description="Inspect live PostgreSQL and MongoDB records, explore the model, and run real database operations from one workspace." action={<Button data-primary="true" onClick={() => { if (typeof window !== "undefined") window.location.hash = "overview"; }}>Overview</Button>} />
    <DbmsWorkspace />
  </>;
}
