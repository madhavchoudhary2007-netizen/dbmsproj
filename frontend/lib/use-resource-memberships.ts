import { useCallback, useEffect, useRef, useState } from "react";
import { api, asArray, Row } from "./api";

export function useResourceMemberships(endpoint: string): {
  members: Row[];
  currentMembers: Row[];
  loading: boolean;
  error: string;
  setError: React.Dispatch<React.SetStateAction<string>>;
  clear: () => void;
  load: (id: string) => Promise<void>;
} {
  const [members, setMembers] = useState<Row[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const generation = useRef(0);
  const active = useRef<AbortController | undefined>(undefined);
  const cancel = useCallback(() => {
    generation.current++;
    active.current?.abort();
    active.current = undefined;
  }, []);
  const clear = useCallback(() => {
    cancel();
    setMembers([]);
    setError("");
    setLoading(false);
  }, [cancel]);
  const load = useCallback(async (id: string) => {
    active.current?.abort();
    const controller = new AbortController();
    active.current = controller;
    const request = ++generation.current;
    setLoading(true);
    setError("");
    try {
      const rows = await api(`${endpoint}/${id}/memberships`, { signal: controller.signal });
      if (request === generation.current) setMembers(asArray(rows));
    } catch (e) {
      if (request !== generation.current || controller.signal.aborted) return;
      setError(e instanceof Error ? e.message : "Unable to load membership history");
      throw e;
    } finally {
      if (request === generation.current) {
        active.current = undefined;
        setLoading(false);
      }
    }
  }, [endpoint]);
  useEffect(() => () => cancel(), [cancel]);
  const today = new Date().toISOString().slice(0, 10);
  const currentMembers = members.filter((member) =>
    typeof member.start_date === "string" &&
    member.start_date <= today &&
    (member.end_date == null || member.end_date === "" ||
      (typeof member.end_date === "string" && member.end_date >= today)),
  );
  return { members, currentMembers, loading, error, setError, clear, load };
}
