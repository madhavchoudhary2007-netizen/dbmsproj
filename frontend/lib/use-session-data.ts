import { useCallback, useEffect, useState } from "react";
import { asArray, listAll, Row } from "@/lib/api";

type SessionData = {
  rows: Row[];
  events: Row[];
  drivers: Row[];
  err: string;
  loading: boolean;
  load: () => Promise<void>;
};

export function useSessionData(): SessionData {
  const [rows, setRows] = useState<Row[]>([]),
    [events, setEvents] = useState<Row[]>([]),
    [drivers, setDrivers] = useState<Row[]>([]),
    [err, setErr] = useState(""),
    [loading, setLoading] = useState(true);
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
  return { rows, events, drivers, err, loading, load };
}
