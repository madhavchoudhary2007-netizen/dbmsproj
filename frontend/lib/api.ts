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

export function getToken() {
  return typeof window === "undefined"
    ? null
    : localStorage.getItem("apexgrid_token");
}

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
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(
    `${API_ROOT}${path.startsWith("/") ? path : `/${path}`}`,
    { ...options, headers, cache: "no-store" },
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
