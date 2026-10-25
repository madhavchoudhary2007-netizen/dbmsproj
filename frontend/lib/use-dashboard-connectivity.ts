import { useCallback, useEffect, useRef, useState } from "react";
import { API_BASE } from "./api";

type LeaseState = "up" | "down" | "unknown";
type WebSocketState = "up" | "down" | "idle" | "connecting";

interface ConnectivityState {
  lease: LeaseState;
  websocket: WebSocketState;
  readinessError: string;
  websocketError: string;
  loading: boolean;
}

function errorMessage(reason: unknown): string {
  return reason instanceof Error ? reason.message : String(reason);
}

export function readRuntimeLease(status: number, body: unknown): "up" | "down" {
  if (typeof body !== "object" || body === null || Array.isArray(body)) {
    throw new Error("Invalid readiness response.");
  }
  const report = body as Record<string, unknown>;
  const services = report.services;
  if (
    typeof services !== "object" || services === null || Array.isArray(services) ||
    (services as Record<string, unknown>).runtime_lease !== "up" &&
      (services as Record<string, unknown>).runtime_lease !== "down"
  ) {
    throw new Error("Invalid readiness response: runtime lease status is missing.");
  }
  const lease = (services as Record<string, "up" | "down">).runtime_lease;
  if (status === 200 && report.status === "ready") return lease;
  if (status === 503 && report.status === "not_ready") return lease;
  throw new Error(`Readiness request failed (${status}).`);
}

export function sessionWebSocketUrl(sessionId: string): string {
  return `${API_BASE.replace(/^http/, "ws")}/api/ws/sessions/${encodeURIComponent(sessionId)}`;
}

export function useDashboardConnectivity(sessionId?: string): {
  lease: LeaseState;
  websocket: WebSocketState;
  error: string;
  loading: boolean;
  reload: () => void;
} {
  const [state, setState] = useState<ConnectivityState>({
    lease: "unknown",
    websocket: sessionId ? "connecting" : "idle",
    readinessError: "",
    websocketError: "",
    loading: true,
  });
  const request = useRef<AbortController | null>(null);
  const generation = useRef(0);

  const reload = useCallback(() => {
    if (request.current) return;
    const controller = new AbortController();
    request.current = controller;
    const current = ++generation.current;
    setState((previous) => ({ ...previous, loading: true, readinessError: "" }));

    void fetch(`${API_BASE}/health/ready`, {
      method: "GET",
      credentials: "include",
      cache: "no-store",
      signal: controller.signal,
    })
      .then(async (response) => {
        const body: unknown = await response.json();
        return readRuntimeLease(response.status, body);
      })
      .then((lease) => {
        if (controller.signal.aborted || generation.current !== current) return;
        setState((previous) => ({ ...previous, lease, readinessError: "", loading: false }));
      })
      .catch((reason: unknown) => {
        if (controller.signal.aborted || generation.current !== current) return;
        setState((previous) => ({ ...previous, readinessError: errorMessage(reason), loading: false }));
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

  useEffect(() => {
    if (!sessionId) {
      setState((previous) => ({ ...previous, websocket: "idle", websocketError: "" }));
      return;
    }

    let active = true;
    let socket: WebSocket;
    setState((previous) => ({ ...previous, websocket: "connecting", websocketError: "" }));
    try {
      socket = new WebSocket(sessionWebSocketUrl(sessionId));
    } catch (reason: unknown) {
      setState((previous) => ({
        ...previous,
        websocket: "down",
        websocketError: errorMessage(reason),
      }));
      return;
    }

    const onOpen = () => {
      if (active) setState((previous) => ({ ...previous, websocket: "up", websocketError: "" }));
    };
    const onError = () => {
      if (active) setState((previous) => ({ ...previous, websocket: "down", websocketError: "WebSocket connection failed." }));
    };
    const onClose = () => {
      if (active) setState((previous) => ({ ...previous, websocket: "down" }));
    };
    socket.addEventListener("open", onOpen);
    socket.addEventListener("error", onError);
    socket.addEventListener("close", onClose);

    return () => {
      active = false;
      socket.removeEventListener("open", onOpen);
      socket.removeEventListener("error", onError);
      socket.removeEventListener("close", onClose);
      socket.close();
    };
  }, [sessionId]);

  return {
    lease: state.lease,
    websocket: state.websocket,
    error: [state.readinessError, state.websocketError].filter(Boolean).join(" "),
    loading: state.loading,
    reload,
  };
}
