import { useCallback, useEffect, useState } from "react";
import { listAll, Row } from "./api";

export function useResourceRows(endpoint: string): {
  rows: Row[];
  loading: boolean;
  error: string;
  load: () => Promise<void>;
} {
  const [rows, setRows] = useState<Row[]>([]),
    [loading, setLoading] = useState(true),
    [error, setError] = useState("");
  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setRows(await listAll(endpoint));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to load records");
    } finally {
      setLoading(false);
    }
  }, [endpoint]);
  useEffect(() => {
    void load();
  }, [load]);

  return { rows, loading, error, load };
}
