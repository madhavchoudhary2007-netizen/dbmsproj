"use client";

import { NbMarquee } from "@/components/nb/marquee";
import { NbSkeleton } from "@/components/nb/skeleton";

export type ShellFeedConnection = "LIVE" | "RECONNECTING" | "OFFLINE";
export type ShellRaceControlState = "empty" | "loading" | "populated" | "error" | "partial";

const sessionDescription = "API SESSION uses dashboard HTTP polling, not WebSocket.";

export interface ShellFeedStatusProps {
  connection: ShellFeedConnection;
  error: string;
  onRefresh: () => void;
}

export function ShellFeedStatus({ connection, error, onRefresh }: ShellFeedStatusProps) {
  const statusDescription = error ? `${connection}: ${error}` : connection;
  const statusTitle = `${statusDescription}. ${sessionDescription}`;

  return (
    <div className="feed-status" data-connection={connection}>
      <span className="sr-only">API SESSION. {statusTitle}</span>
      <button type="button" aria-label="Refresh race control feed" title={statusTitle} onClick={onRefresh}>
        <span aria-hidden="true" className="status-dot" />
        <span className="feed-connection">{connection}</span>
      </button>
    </div>
  );
}

export interface ShellRaceControlProps {
  items: readonly string[];
  status: ShellRaceControlState;
  error: string;
  onRefresh: () => void;
}

function feedTitle(items: readonly string[]) {
  return items.join(" • ");
}

function RaceControlMarquee({ items }: { items: readonly string[] }) {
  if (items.length === 0) return null;

  return <NbMarquee items={items} tone="red" className="race-control-feed" title={feedTitle(items)} />;
}

function RefreshFeedButton({ onRefresh }: { onRefresh: () => void }) {
  return (
    <button type="button" aria-label="Refresh race control feed" title="Refresh race control feed" onClick={onRefresh}>
      <span aria-hidden="true">Refresh</span>
    </button>
  );
}

export function ShellRaceControl({ items, status, error, onRefresh }: ShellRaceControlProps) {
  if (status === "empty" || (status === "populated" && items.length === 0)) {
    return (
      <div data-feed-state="empty" className="race-control-feed-state" role="status">
        <span className="sr-only">Race control feed is empty.</span>
      </div>
    );
  }

  if (status === "loading") {
    return (
      <div data-feed-state="loading" className="race-control-feed-state race-control-feed-loading" role="status" aria-busy="true">
        {items.length > 0 ? (
          <RaceControlMarquee items={items} />
        ) : (
          <NbSkeleton label="Loading race control feed…" style={{ height: 40, minHeight: 40 }} />
        )}
      </div>
    );
  }

  if (status === "error") {
    return (
      <div data-feed-state="error" className="race-control-feed-state race-control-feed-message" role="alert">
        <span>{error || "Race control feed unavailable."}</span>
        <RefreshFeedButton onRefresh={onRefresh} />
      </div>
    );
  }

  if (status === "partial") {
    const partialMessage = error || "Showing stale race control data.";

    return (
      <div data-feed-state="partial" className="race-control-feed-state race-control-feed-partial" role="status">
        <RaceControlMarquee items={items} />
        <div className="race-control-feed-message">
          <span>{partialMessage}</span>
          <RefreshFeedButton onRefresh={onRefresh} />
        </div>
      </div>
    );
  }

  return (
    <div data-feed-state="populated" className="race-control-feed-state">
      <RaceControlMarquee items={items} />
    </div>
  );
}
