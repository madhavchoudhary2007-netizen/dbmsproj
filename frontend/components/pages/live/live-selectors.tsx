import type { MutableRefObject } from "react";
import type { Row } from "@/lib/api";

interface LiveSelectorsProps {
  session: string;
  setSession: (s: string) => void;
  driver: string;
  setDriver: (s: string) => void;
  autoFollow: MutableRefObject<boolean>;
  sessions: Row[];
  namedDrivers: Map<string, Row>;
  driverIds: Set<string>;
  status: string;
  primary?: boolean;
}

export function LiveSelectors({
  session,
  setSession,
  driver,
  setDriver,
  autoFollow: autoFollowRef,
  sessions,
  namedDrivers,
  driverIds,
  status,
  primary = false,
}: LiveSelectorsProps) {
  return (
    <div className="toolbar select-toolbar">
      <label>
        Session
        <select data-primary={primary ? "true" : undefined} value={session} onChange={(e) => { autoFollowRef.current = false; setSession(e.target.value); setDriver(""); }}>
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
  );
}
