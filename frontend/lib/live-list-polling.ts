import type { MutableRefObject } from "react";
import type { Row } from "./api";

type LiveListRefresh = () => Promise<{
  sessionRows: Row[];
  raceRows: Row[];
  current: boolean;
}>;

export function startInitialLiveSelection(
  refreshLists: LiveListRefresh,
  autoFollow: MutableRefObject<boolean>,
  setSession: (s: string) => void,
  reportError: (source: "lists", message: string) => void,
): () => void {
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
}

export function startLiveListPolling(
  refreshLists: LiveListRefresh,
  session: string,
  autoFollow: MutableRefObject<boolean>,
  listRequest: MutableRefObject<number>,
  setSession: (s: string) => void,
  setDriver: (s: string) => void,
): () => void {
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
}
