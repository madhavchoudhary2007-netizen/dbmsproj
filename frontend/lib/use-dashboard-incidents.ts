import { useCallback, useEffect, useRef, useState } from "react";
import { api, Row } from "./api";
import { ViewState } from "./data-state";

function messageOf(reason: unknown): string {
  return reason instanceof Error ? reason.message : String(reason);
}

function validateRows(value: unknown): Row[] {
  if (
    !Array.isArray(value) ||
    !value.every((row) =>
      typeof row === "object" && row !== null && !Array.isArray(row) &&
      (!("id" in row) || typeof row.id === "string"),
    )
  ) {
    throw new Error("Invalid latest incidents response: expected an array of incident objects with string IDs.");
  }
  return value;
}

export function useDashboardIncidents(): {
  state: ViewState<Row[]>;
  reload: () => void;
} {
  const [rows, setRows] = useState<Row[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const rowsRef = useRef<Row[] | null>(null);
  const request = useRef<AbortController | null>(null);
  const generation = useRef(0);

  const reload = useCallback(() => {
    if (request.current) return;
    const controller = new AbortController();
    request.current = controller;
    const current = ++generation.current;
    if (rowsRef.current === null) setLoading(true);
    setError("");

    void api<unknown>("/incidents?limit=5", { signal: controller.signal })
      .then((response) => {
        if (controller.signal.aborted || generation.current !== current) return;
        const latest = validateRows(response);
        rowsRef.current = latest;
        setRows(latest);
        setError("");
        setLoading(false);
      })
      .catch((reason: unknown) => {
        if (controller.signal.aborted || generation.current !== current) return;
        setError(messageOf(reason));
        setLoading(false);
      })
      .finally(() => {
        if (generation.current === current) request.current = null;
      });
  }, []);

  useEffect(() => {
    reload();
    return () => {
      generation.current += 1;
      request.current?.abort();
      request.current = null;
    };
  }, [reload]);

  let state: ViewState<Row[]>;
  if (loading) state = { status: "loading" };
  else if (rows === null && error) {
    state = {
      status: "error",
      error: { message: error, retryable: true },
      retry: reload,
    };
  } else if (rows === null) state = { status: "loading" };
  else if (error) {
    state = {
      status: "partial",
      data: rows,
      filter: { label: `Latest incidents unavailable: ${error}`, clear: reload },
      totalCount: rows.length,
    };
  } else if (rows.length === 0) state = { status: "empty", reason: "no-data" };
  else state = { status: "populated", data: rows };

  return { state, reload };
}
