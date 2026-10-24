import { api } from "./api";

const CACHE_TTL_MS = 10_000;

export interface DashboardData {
  active_sessions?: unknown;
  scheduled_events?: unknown;
  open_incidents?: unknown;
  drivers?: unknown;
  active_session?: Record<string, unknown>;
  next_event?: Record<string, unknown> | null;
  [key: string]: unknown;
}

interface Consumer {
  reject: (reason?: unknown) => void;
  resolve: (value: DashboardData) => void;
  signal?: AbortSignal;
  onAbort?: () => void;
  settled: boolean;
}

interface Flight {
  controller: AbortController;
  consumers: Set<Consumer>;
  cancelled: boolean;
  finished: boolean;
}

let cachedData: DashboardData | undefined;
let cacheExpiresAt = 0;
let currentFlight: Flight | undefined;

function abortError(): Error {
  const error = new Error("The operation was aborted");
  error.name = "AbortError";
  return error;
}

function removeAbortListener(consumer: Consumer): void {
  if (consumer.signal && consumer.onAbort) {
    consumer.signal.removeEventListener("abort", consumer.onAbort);
  }
}

function finishFlight(flight: Flight, data?: DashboardData, reason?: unknown): void {
  if (flight.finished) return;
  flight.finished = true;

  const isCurrent = currentFlight === flight;
  if (isCurrent) {
    currentFlight = undefined;
    // A canceled flight may settle after a replacement; only the active one caches.
    if (reason === undefined && data !== undefined) {
      cachedData = data;
      cacheExpiresAt = Date.now() + CACHE_TTL_MS;
    }
  }

  for (const consumer of flight.consumers) {
    removeAbortListener(consumer);
    if (consumer.settled) continue;
    consumer.settled = true;
    if (reason === undefined && data !== undefined) consumer.resolve(data);
    else consumer.reject(reason);
  }
  flight.consumers.clear();
}

function cancelFlight(flight: Flight): void {
  if (flight.finished || flight.cancelled) return;
  flight.cancelled = true;
  // Clear first so a new consumer starts a fresh request before abort settles.
  if (currentFlight === flight) currentFlight = undefined;
  flight.controller.abort();
}

function startFlight(): Flight {
  const controller = new AbortController();
  const promise = api<DashboardData>("/dashboard", { signal: controller.signal });
  const flight: Flight = {
    controller,
    consumers: new Set(),
    cancelled: false,
    finished: false,
  };
  currentFlight = flight;
  void promise.then(
    (data) => finishFlight(flight, data),
    (reason: unknown) => finishFlight(flight, undefined, reason),
  );
  return flight;
}

function attachConsumer(flight: Flight, signal?: AbortSignal): Promise<DashboardData> {
  return new Promise<DashboardData>((resolve, reject) => {
    const consumer: Consumer = { resolve, reject, signal, settled: false };
    const onAbort = (): void => {
      if (consumer.settled) return;
      consumer.settled = true;
      removeAbortListener(consumer);
      flight.consumers.delete(consumer);
      reject(abortError());
      if (flight.consumers.size === 0) cancelFlight(flight);
    };
    consumer.onAbort = onAbort;
    flight.consumers.add(consumer);
    if (signal) {
      signal.addEventListener("abort", onAbort, { once: true });
      if (signal.aborted) onAbort();
    }
  });
}

export function readDashboardFeed(options: { signal?: AbortSignal; force?: boolean } = {}): Promise<DashboardData> {
  const { signal, force = false } = options;
  if (signal?.aborted) return Promise.reject(abortError());

  if (!force && cachedData !== undefined && cacheExpiresAt > Date.now()) {
    return Promise.resolve(cachedData);
  }

  const flight = currentFlight ?? startFlight();
  return attachConsumer(flight, signal);
}
