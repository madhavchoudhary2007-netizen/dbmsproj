"use client";
import { useCallback, useEffect, useState } from "react";
import { api, asArray, list, Row } from "@/lib/api";
import { Button, DataTable, PageHeader, StateMessage } from "@/components/ui";
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
  useEffect(() => {
    void load();
  }, [load]);
  const recalc = async () => {
    setBusy(true);
    setMessage("");
    try {
      const result = await api(`/championships/${champ}/recalculate`, {
        method: "POST",
      });
      setMessage(`Standings recalculated. ${JSON.stringify(result)}`);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Recalculation failed");
    } finally {
      setBusy(false);
    }
  };
  return (
    <>
      <PageHeader
        eyebrow="CHAMPIONSHIP / CLASSIFICATION"
        title="Standings"
        description="Persisted championship classification. Recalculate invokes the database standings routine."
      />
      <div className="toolbar select-toolbar">
        <label>
          Championship
          <select value={champ} onChange={(e) => setChamp(e.target.value)}>
            <option value="">Select championship</option>
            {chs.map((c) => (
              <option key={String(c.id)} value={String(c.id)}>
                {String(c.name || c.id)} · {String(c.season || "")}
              </option>
            ))}
          </select>
        </label>
        {canRecalculate && (
          <Button onClick={() => void recalc()} disabled={!champ || busy}>
            {busy ? "Recalculating…" : "Recalculate standings"}
          </Button>
        )}
      </div>
      <StateMessage error={error} loading={loading} retry={() => void load()} />
      {message && <div className="notice">{message}</div>}
      {rows.some((row) => row.provisional === true) && (
        <div className="notice">
          Provisional standings: historical time and grid penalties are recorded but not applied to official order or points. Review the penalties before treating standings as final.
        </div>
      )}
      {!loading && !error && (
        <DataTable
          rows={rows}
          columns={
            rows[0]
              ? Object.keys(rows[0]).filter(
                  (k) => typeof rows[0][k] !== "object",
                )
              : [
                  "rank",
                  "driver_name",
                  "team_name",
                  "points",
                  "wins",
                  "podiums",
                ]
          }
        />
      )}
    </>
  );
}
