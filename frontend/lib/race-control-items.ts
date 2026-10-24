import type { DashboardData } from "./dashboard-feed";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function trimmedString(value: unknown): string | undefined {
  if (typeof value !== "string") return undefined;
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : undefined;
}

function eventLabel(value: unknown): string | undefined {
  if (!isRecord(value)) return undefined;

  const name = trimmedString(value.name);
  const circuit = trimmedString(value.circuit_name);
  return name ? (circuit ? `${name} — ${circuit}` : name) : undefined;
}

export function raceControlItems(data: DashboardData | null): readonly string[] {
  if (!isRecord(data)) return [];

  const items: string[] = [];
  const activeSession = isRecord(data.active_session) ? data.active_session : undefined;
  if (activeSession) {
    const activeName = trimmedString(activeSession.event_name) ?? trimmedString(activeSession.name);
    if (activeName) {
      const circuit = trimmedString(activeSession.circuit_name);
      items.push(`ACTIVE: ${circuit ? `${activeName} — ${circuit}` : activeName}`);
    }
  }

  const incidents = data.open_incidents;
  if (typeof incidents === "number" && Number.isFinite(incidents) && incidents >= 0) {
    items.push(`OPEN INCIDENTS: ${incidents}`);
  }

  const nextName = eventLabel(data.next_event);
  if (nextName) items.push(`NEXT: ${nextName}`);

  return items;
}
