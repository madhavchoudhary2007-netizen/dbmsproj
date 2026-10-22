export const API_BASE = (
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
).replace(/\/$/, "");
export const API_ROOT = `${API_BASE}/api`;
export type User = {
  id: string;
  email: string;
  full_name: string;
  role: string;
};
export type Row = Record<string, unknown> & { id?: string };

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function formatErrorDetail(value: unknown): string | undefined {
  if (typeof value === "string") return value.trim() || undefined;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  if (Array.isArray(value)) {
    const messages = value.map(formatErrorDetail).filter((message): message is string => !!message);
    return messages.length ? messages.join("; ") : undefined;
  }
  if (!isRecord(value)) return undefined;

  const message = typeof value.msg === "string" ? value.msg : value.message;
  if (typeof message === "string") {
    const location = value.loc;
    if (Array.isArray(location)) {
      const path = location
        .filter((part) => !["body", "query", "path", "header", "cookie"].includes(String(part)))
        .map(String)
        .join(".");
      return path ? `${path}: ${message}` : message;
    }
    if (typeof location === "string") return `${location}: ${message}`;
    return message;
  }

  for (const key of ["detail", "errors"]) {
    if (key in value) return formatErrorDetail(value[key]);
  }
  const fields = Object.entries(value)
    .filter(([key]) => !/^(input|value)$/i.test(key) && !/(^|[_-])(password|passwd|token|secret|authorization|credential|api[_-]?key)(?:$|[_-])/i.test(key))
    .map(([key, fieldValue]) => {
      const detail = formatErrorDetail(fieldValue);
      return detail ? `${key}: ${detail}` : undefined;
    })
    .filter((field): field is string => !!field);
  return fields.length ? fields.join("; ") : undefined;
}

export async function api<T = any>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData) && options.body)
    headers.set("Content-Type", "application/json");
  const method = (options.method ?? "GET").toUpperCase();
  if (["POST", "PUT", "PATCH", "DELETE"].includes(method) && typeof document !== "undefined") {
    const csrfCookie = document.cookie
      .split(";")
      .map((cookie) => cookie.trim())
      .find((cookie) => cookie.startsWith("apexgrid_csrf="))
      ?.slice("apexgrid_csrf=".length);
    if (csrfCookie !== undefined) headers.set("X-CSRF-Token", csrfCookie);
  }
  const response = await fetch(
    `${API_ROOT}${path.startsWith("/") ? path : `/${path}`}`,
    { ...options, headers, credentials: "include", cache: "no-store" },
  );
  if (!response.ok) {
    const status = `${response.status}${response.statusText ? ` ${response.statusText}` : ""}`;
    let detail: string | undefined;
    try {
      const body: unknown = await response.json();
      detail = formatErrorDetail(isRecord(body) ? body.detail ?? body.message ?? body.errors ?? body : body);
    } catch {}
    throw new Error(detail ? `${status}: ${detail}` : status);
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}

export type ApiReadOptions = Omit<RequestInit, "signal" | "method"> & {
  signal?: AbortSignal | AbortController | null;
  method?: "GET";
  retries?: number;
  retryDelayMs?: number;
  maxRetryDelayMs?: number;
};

const MAX_READ_RETRIES = 5;
const MAX_READ_DELAY_MS = 10_000;

function getAbortSignal(signal?: AbortSignal | AbortController | null): AbortSignal | undefined {
  if (!signal) return undefined;
  return "signal" in signal ? signal.signal : signal;
}

function isAbortError(error: unknown): boolean {
  return error instanceof Error && error.name === "AbortError";
}

function isRetryableReadError(error: unknown): boolean {
  if (error instanceof TypeError) return true;
  if (!(error instanceof Error)) return false;
  const status = error.message.match(/^(\d{3})(?:\s|:|$)/)?.[1];
  return status !== undefined && Number(status) >= 500 && Number(status) < 600;
}

function abortableDelay(ms: number, signal?: AbortSignal): Promise<void> {
  if (signal?.aborted) return Promise.reject(new DOMException("The operation was aborted", "AbortError"));
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      signal?.removeEventListener("abort", onAbort);
      resolve();
    }, ms);
    const onAbort = () => {
      clearTimeout(timer);
      signal?.removeEventListener("abort", onAbort);
      reject(new DOMException("The operation was aborted", "AbortError"));
    };
    signal?.addEventListener("abort", onAbort, { once: true });
  });
}

/** Opt-in GET read with bounded retries for transient network and server errors. */
export async function apiRead<T = any>(path: string, options: ApiReadOptions = {}): Promise<T> {
  const {
    signal: signalInput,
    method = "GET",
    retries = 2,
    retryDelayMs = 250,
    maxRetryDelayMs = 2_000,
    ...requestOptions
  } = options;
  if (method !== "GET") {
    throw new TypeError("apiRead only supports GET requests");
  }
  if (requestOptions.body != null) {
    throw new TypeError("apiRead does not support request bodies");
  }
  const signal = getAbortSignal(signalInput);
  const retryCount = Number.isFinite(retries)
    ? Math.min(MAX_READ_RETRIES, Math.max(0, Math.floor(retries)))
    : 0;
  const initialDelay = Number.isFinite(retryDelayMs)
    ? Math.min(MAX_READ_DELAY_MS, Math.max(0, retryDelayMs))
    : 250;
  const delayCap = Number.isFinite(maxRetryDelayMs)
    ? Math.min(MAX_READ_DELAY_MS, Math.max(0, maxRetryDelayMs))
    : 2_000;

  for (let attempt = 0; ; attempt += 1) {
    try {
      return await api<T>(path, { ...requestOptions, method, signal });
    } catch (error) {
      if (
        signal?.aborted || isAbortError(error) || attempt >= retryCount ||
        !isRetryableReadError(error)
      ) throw error;
      const delay = Math.min(delayCap, initialDelay * 2 ** attempt);
      await abortableDelay(delay, signal);
    }
  }
}

export const list = (path: string, params?: Record<string, string>) => {
  const q = new URLSearchParams({ limit: "200", offset: "0", ...params });
  return api<Row[]>(`${path}${path.includes("?") ? "&" : "?"}${q}`);
};
export async function listAll(path: string, params: Record<string, string> = {}): Promise<Row[]> {
  const rows: Row[] = [];
  const pageSize = 200;
  for (let offset = 0; ; offset += pageSize) {
    const page = asArray(await list(path, { ...params, limit: String(pageSize), offset: String(offset) }));
    rows.push(...page);
    if (page.length < pageSize) return rows;
  }
}
export const asArray = (v: any): Row[] =>
  Array.isArray(v)
    ? v
    : Array.isArray(v?.items)
      ? v.items
      : Array.isArray(v?.results)
        ? v.results
        : [];
export const label = (x: any) =>
  typeof x === "string" || typeof x === "number"
    ? String(x)
    : x?.name || x?.full_name || x?.email || x?.id || "—";
export const pretty = (x: any) => {
  if (x === null || x === undefined || x === "") return "—";
  if (typeof x === "boolean") return x ? "Yes" : "No";
  if (typeof x === "object") return label(x);
  return String(x);
};
