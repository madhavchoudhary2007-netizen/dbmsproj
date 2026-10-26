"use client";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api, asArray, list, Row } from "@/lib/api";
import { Button, PageHeader } from "@/components/ui";
import { NbMarquee } from "@/components/nb/marquee";
import { NbSelect } from "@/components/nb/input";
import { NbTable } from "@/components/nb/table";
import type { NbTableColumn } from "@/components/nb/table";
import type { ViewState } from "@/lib/data-state";
import { useFlip } from "@/lib/use-flip";
import { useAuth } from "@/components/auth";

export default function Page() {
  const [chs, setChs] = useState<Row[]>([]),
    [champ, setChamp] = useState(""),
    [rows, setRows] = useState<Row[]>([]),
    [loading, setLoading] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [message, setMessage] = useState("");
  const { user } = useAuth();
  const canRecalculate = user?.role === "ADMIN" || user?.role === "STEWARD";
  const bodyRef = useRef<HTMLTableSectionElement | null>(null);
  const rowKeys = useMemo(() => rows.map((row, index) => String(row.driver_id ?? row.id ?? row.rank ?? index)), [rows]);
  useFlip(bodyRef, rowKeys);

  useEffect(() => {
    list("/championships")
      .then((x) => {
        const a = asArray(x);
        setChs(a);
        if (a[0]?.id) setChamp(String(a[0].id));
      })
      .catch((e) => setError(e.message));
  }, []);
  const load = useCallback(async () => {
    if (!champ) return;
    setLoading(true);
    setError("");
    try {
      setRows(asArray(await api(`/championships/${champ}/standings`)));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to load standings");
    } finally {
      setLoading(false);
    }
  }, [champ]);
  useEffect(() => { void load(); }, [load]);
  const recalc = async () => {
    setBusy(true);
    setMessage("");
    try {
      const result = await api(`/championships/${champ}/recalculate`, { method: "POST" });
      setMessage(`Standings recalculated. ${JSON.stringify(result)}`);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Recalculation failed");
    } finally {
      setBusy(false);
    }
  };
  const columns: NbTableColumn<Row>[] = [
    { key: "rank", title: "Pos", numeric: true },
    { key: "driver_name", title: "Driver", render: (row) => <strong>{String(row.driver_name ?? "—")}</strong> },
    { key: "number", title: "Car", numeric: true },
    { key: "team_name", title: "Team" },
    { key: "points", title: "Points", numeric: true },
    { key: "wins", title: "Wins", numeric: true },
    { key: "podiums", title: "Podiums", numeric: true },
  ];
  const state: ViewState<readonly Row[]> = error
    ? { status: "error", error: { message: error, retryable: true }, retry: () => void load() }
    : loading
      ? { status: "loading" }
      : !champ
        ? { status: "empty", reason: "first-use" }
        : rows.length
          ? { status: "populated", data: rows }
          : { status: "empty", reason: "no-data" };
  const podium = rows.slice(0, 3);
  const topTen = rows.slice(0, 10).map((row) => `${String(row.rank ?? "—")} · ${String(row.driver_name ?? "—")} · ${String(row.points ?? 0)} PTS`);

  return (
    <>
      <PageHeader eyebrow="CHAMPIONSHIP / CLASSIFICATION" title="Standings" description="Persisted championship classification. Recalculate invokes the database standings routine." />
      <div className="toolbar select-toolbar standings-controls">
        <label>
          Championship
          <NbSelect value={champ} onChange={(e) => setChamp(e.target.value)}>
            <option value="">Select championship</option>
            {chs.map((c) => <option key={String(c.id)} value={String(c.id)}>{String(c.name || c.id)} · {String(c.season || "")}</option>)}
          </NbSelect>
        </label>
        {canRecalculate && <Button data-primary="true" onClick={() => void recalc()} disabled={!champ || busy}>{busy ? "Recalculating…" : "Recalculate standings"}</Button>}
      </div>
      {message && <div className="notice">{message}</div>}
      {rows.some((row) => row.provisional === true) && (
        <div className="notice">Provisional standings: historical time and grid penalties are recorded but not applied to official order or points. Review the penalties before treating standings as final.</div>
      )}
      {topTen.length > 0 && <section className="standings-ticker" aria-label="Top ten points"><h2>Top ten · points</h2><NbMarquee items={topTen} tone="red" /></section>}
      {podium.length > 0 && (
        <section className="standings-podium" aria-label="Top three standings">
          {[[2, podium[1]], [1, podium[0]], [3, podium[2]]].filter((entry): entry is [number, Row] => Boolean(entry[1])).map(([place, row]) => (
            <article className={`podium-card podium-place-${place}`} key={String(row.driver_id ?? row.id ?? row.rank)}>
              <span className="podium-position">{String(row.rank ?? place)}</span>
              <h2>{String(row.driver_name ?? "—")}</h2>
              <p>{String(row.team_name ?? "—")}</p>
              <strong>{String(row.points ?? 0)} <span>points</span></strong>
            </article>
          ))}
        </section>
      )}
      <section className="standings-data" aria-label="Full standings">
        {state.status === "empty" && champ && <div className="standings-empty-accent" aria-hidden="true" />}
        <NbTable state={state} columns={columns} rowKey={(row, index) => String(row.driver_id ?? row.id ?? row.rank ?? index)} caption="Championship standings" bodyRef={bodyRef} empty={champ ? "No standings have been recorded for this championship." : "Select a championship to view standings."} />
      </section>
    </>
  );
}
