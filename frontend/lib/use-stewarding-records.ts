import { useCallback, useEffect, useRef, useState } from "react";
import { apiRead } from "@/lib/api";

export type StewardPenalty = {
  id: string;
  incident_id: string;
  driver_id: string;
  driver_name: string | null;
  session_id: string;
  lap: number;
  points: number;
  time_seconds: number;
  grid_places: number;
  created_at: string;
};

export type StewardLicence = {
  driver_id: string;
  driver_name: string | null;
  licence_number: string;
  eligibility: string;
  season: number;
  points: number;
};

const PAGE_SIZE = 50;

function useStewardingRecords<T>(source: "penalties" | "licences", season?: number) {
  const [rows, setRows] = useState<T[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [loaded, setLoaded] = useState(false);
  const [offset, setOffset] = useState(0);
  const [revision, setRevision] = useState(0);
  const pending = useRef<{ key: string; controller: AbortController } | undefined>(undefined);
  const queued = useRef(false);
  const generation = useRef(0);

  const url = source === "licences"
    ? `/stewarding/licences?season=${season}&limit=${PAGE_SIZE}&offset=${offset}`
    : `/stewarding/penalties?limit=${PAGE_SIZE}&offset=${offset}`;

  const reload = useCallback(() => setRevision((value) => value + 1), []);
  const previous = useCallback(() => {
    if (offset > 0) {
      setRows([]);
      setError("");
      setLoaded(false);
      setOffset((value) => Math.max(0, value - PAGE_SIZE));
    }
  }, [offset]);
  const next = useCallback(() => {
    if (rows.length === PAGE_SIZE) {
      setRows([]);
      setError("");
      setLoaded(false);
      setOffset((value) => value + PAGE_SIZE);
    }
  }, [rows.length]);

  useEffect(() => {
    if (pending.current?.key === url) {
      queued.current = true;
      return;
    }
    pending.current?.controller.abort();
    queued.current = false;
    const controller = new AbortController();
    const requestGeneration = ++generation.current;
    pending.current = { key: url, controller };
    setLoading(true);
    void apiRead<T[]>(url, { signal: controller.signal }).then((result) => {
      if (requestGeneration !== generation.current) return;
      setRows(result.slice(0, PAGE_SIZE));
      setLoaded(true);
      setError("");
    }).catch((cause: unknown) => {
      if (requestGeneration !== generation.current || controller.signal.aborted) return;
      setError(cause instanceof Error ? cause.message : "Unable to load stewarding records");
    }).finally(() => {
      if (requestGeneration === generation.current) {
        pending.current = undefined;
        setLoading(false);
        if (queued.current) {
          queued.current = false;
          setRevision((value) => value + 1);
        }
      }
    });
  }, [revision, url]);

  useEffect(() => () => {
    generation.current += 1;
    pending.current?.controller.abort();
    pending.current = undefined;
  }, []);

  return { rows, loading, error, loaded, offset, pageSize: PAGE_SIZE, hasNext: rows.length === PAGE_SIZE, previous, next, reload };
}

export function useStewardingPenalties() {
  return useStewardingRecords<StewardPenalty>("penalties");
}

export function useStewardingLicences() {
  const season = useState(() => new Date().getUTCFullYear())[0];
  return { ...useStewardingRecords<StewardLicence>("licences", season), season };
}
