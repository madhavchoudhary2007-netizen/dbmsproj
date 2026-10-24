"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { DashboardData, readDashboardFeed } from "./dashboard-feed";
type FeedStatus = "empty" | "loading" | "populated" | "error" | "partial";
type Connection = "LIVE" | "RECONNECTING" | "OFFLINE";
const POLL_INTERVAL_MS = 30_000;
function isVisible(): boolean { return typeof document !== "undefined" && document.visibilityState === "visible"; }
function isOnline(): boolean { return typeof navigator === "undefined" || navigator.onLine !== false; }
function isRecord(value: unknown): value is DashboardData { return typeof value === "object" && value !== null && !Array.isArray(value); }
function hasMeaningfulData(value: DashboardData): boolean {
  return Object.values(value).some((item) => item !== null && item !== undefined &&
    (typeof item === "number" ? Number.isFinite(item) : typeof item === "string" ? item.length > 0 :
      Array.isArray(item) ? item.length > 0 : typeof item === "object" ? Object.keys(item).length > 0 : true));
}
function errorMessage(error: unknown): string { return error instanceof Error ? error.message : String(error); }
export function useRaceControlFeed(enabled: boolean): {
  data: DashboardData | null;
  status: FeedStatus;
  error: string;
  refresh: () => void;
  connection: Connection;
} {
  const initiallyVisible = typeof document === "undefined" || isVisible();
  const [data, setData] = useState<DashboardData | null>(null);
  const [status, setStatus] = useState<FeedStatus>(enabled && initiallyVisible && isOnline() ? "loading" : "empty");
  const [error, setError] = useState("");
  const [connection, setConnection] = useState<Connection>(
    enabled && initiallyVisible && isOnline() ? "RECONNECTING" : "OFFLINE",
  );
  const dataRef = useRef<DashboardData | null>(null);
  const requestRef = useRef<((force?: boolean) => void) | null>(null);

  const refresh = useCallback(() => {
    requestRef.current?.(true);
  }, []);

  useEffect(() => {
    let disposed = false;
    let interval: ReturnType<typeof setInterval> | undefined;
    let inFlight: Promise<void> | undefined;
    let consumerController: AbortController | undefined;

    const stopRequest = (): void => { consumerController?.abort(); consumerController = undefined; inFlight = undefined; };

    const stopPolling = (): void => {
      if (interval !== undefined) { clearInterval(interval); interval = undefined; }
      stopRequest();
      if (!disposed) setConnection("OFFLINE");
    };

    const request = (force = false): void => {
      if (disposed || !enabled || !isVisible() || !isOnline() || inFlight) return;
      const controller = new AbortController();
      consumerController = controller;
      setStatus("loading");
      setError("");
      setConnection("RECONNECTING");

      let pending: Promise<void>;
      pending = readDashboardFeed({ signal: controller.signal, force })
        .then((nextData) => {
          if (disposed || controller.signal.aborted) return;
          if (!isRecord(nextData)) throw new Error("Invalid dashboard response");
          if (hasMeaningfulData(nextData)) {
            dataRef.current = nextData;
            setData(nextData);
            setStatus("populated");
          } else {
            dataRef.current = null;
            setData(null);
            setStatus("empty");
          }
          setError("");
          setConnection("LIVE");
        })
        .catch((nextError: unknown) => {
          if (disposed || controller.signal.aborted || (nextError instanceof Error && nextError.name === "AbortError")) return;
          const message = errorMessage(nextError);
          setError(message);
          setStatus(dataRef.current ? "partial" : "error");
          setConnection(isVisible() && isOnline() ? "RECONNECTING" : "OFFLINE");
        })
        .finally(() => {
          if (inFlight === pending) {
            inFlight = undefined;
            consumerController = undefined;
          }
        });
      inFlight = pending;
    };

    const startPolling = (): void => { if (interval === undefined && enabled && isVisible() && isOnline()) interval = setInterval(() => request(), POLL_INTERVAL_MS); };

    const handleVisibility = (): void => {
      if (!isVisible() || !isOnline()) { stopPolling(); return; }
      request();
      startPolling();
    };

    const handleOnline = (): void => { if (isVisible()) { request(true); startPolling(); } };
    const handleOffline = (): void => stopPolling();
    requestRef.current = request;
    if (enabled && isVisible() && isOnline()) {
      request();
      startPolling();
    } else if (!enabled) {
      dataRef.current = null;
      setData(null);
      setError("");
      setStatus("empty");
      setConnection("OFFLINE");
    } else {
      setConnection("OFFLINE");
    }
    document.addEventListener("visibilitychange", handleVisibility);
    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      disposed = true;
      requestRef.current = null;
      if (interval !== undefined) clearInterval(interval);
      stopRequest();
      document.removeEventListener("visibilitychange", handleVisibility);
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, [enabled]);

  return { data, status, error, refresh, connection };
}
