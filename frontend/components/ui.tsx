"use client";
import { useEffect, useId, useRef, useState } from "react";
import {
  Plus,
  RefreshCw,
  Search,
  X,
  AlertCircle,
  LoaderCircle,
} from "lucide-react";
import { Row, pretty } from "@/lib/api";
export function PageHeader({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow: string;
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="page-head">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {action}
    </div>
  );
}
export function Button({
  children,
  onClick,
  type = "button",
  disabled = false,
  kind = "primary",
}: {
  children: React.ReactNode;
  onClick?: () => void;
  type?: "button" | "submit";
  disabled?: boolean;
  kind?: "primary" | "secondary" | "danger";
}) {
  return (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      className={`button ${kind}`}
    >
      {children}
    </button>
  );
}
export function StateMessage({
  error,
  loading,
  empty,
  retry,
}: {
  error?: string;
  loading?: boolean;
  empty?: string;
  retry?: () => void;
}) {
  if (loading)
    return (
      <div className="state">
        <LoaderCircle className="spin" /> Loading from API…
      </div>
    );
  if (error)
    return (
      <div className="state error">
        <AlertCircle />
        <div>
          <strong>Request failed</strong>
          <p>{error}</p>
          {retry && (
            <button className="text-button" onClick={retry}>
              Try again
            </button>
          )}
        </div>
      </div>
    );
  if (empty) return <div className="state">{empty}</div>;
  return null;
}
export function PartialStateNotice({
  shownCount,
  totalCount,
  filterLabel,
  onClear,
}: {
  shownCount: number;
  totalCount: number;
  filterLabel: string;
  onClear: () => void;
}) {
  return (
    <div className="state" role="status" aria-live="polite">
      <span>Showing {shownCount} of {totalCount} records</span>
      <button
        className="text-button"
        onClick={onClear}
        aria-label={`Clear filter: ${filterLabel}`}
        style={{ minHeight: 44, paddingInline: 12 }}
      >
        Clear filter
      </button>
    </div>
  );
}
export function DataTable({
  rows,
  columns,
  onSelect,
}: {
  rows: Row[];
  columns: string[];
  onSelect?: (row: Row) => void;
}) {
  if (!rows.length)
    return <div className="state">No records returned by the API.</div>;
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c}>{c.replaceAll("_", " ")}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr
              key={String(r.id || i)}
              onClick={() => onSelect?.(r)}
              onKeyDown={onSelect ? (event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  onSelect(r);
                }
              } : undefined}
              tabIndex={onSelect ? 0 : undefined}
              className={onSelect ? "clickable" : ""}
            >
              {columns.map((c) => (
                <td key={c}>{pretty(r[c])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
export function SearchBox({
  value,
  onChange,
  placeholder = "Filter records",
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <label className="search">
      <Search size={15} aria-hidden="true" />
      <input
        aria-label={placeholder || "Filter records"}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
      />
    </label>
  );
}
type ModalEntry = {
  element: HTMLElement;
  close: () => void;
  previousFocus: HTMLElement | null;
};
const modalStack: ModalEntry[] = [];
let previousBodyOverflow = "";

function focusableElements(container: HTMLElement) {
  return Array.from(
    container.querySelectorAll<HTMLElement>(
      'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
    ),
  ).filter((element) => element.getClientRects().length > 0);
}

export function Modal({
  title,
  close,
  children,
}: {
  title: string;
  close: () => void;
  children: React.ReactNode;
}) {
  const titleId = useId();
  const closeRef = useRef<HTMLButtonElement>(null);
  const modalRef = useRef<HTMLElement>(null);
  const closeCallbackRef = useRef(close);
  useEffect(() => {
    closeCallbackRef.current = close;
  }, [close]);
  useEffect(() => {
    const previousFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const element = modalRef.current;
    if (!element) return;
    if (modalStack.length === 0) {
      previousBodyOverflow = document.body.style.overflow;
      document.body.style.overflow = "hidden";
    }
    const entry: ModalEntry = {
      element,
      close: () => closeCallbackRef.current(),
      previousFocus,
    };
    modalStack.push(entry);
    closeRef.current?.focus();
    const onKeyDown = (event: KeyboardEvent) => {
      if (modalStack.at(-1) !== entry) return;
      if (event.key === "Escape") {
        event.preventDefault();
        entry.close();
        return;
      }
      if (event.key !== "Tab") return;
      const focusable = focusableElements(element);
      if (!focusable.length) {
        event.preventDefault();
        element.focus();
        return;
      }
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && (document.activeElement === first || !element.contains(document.activeElement))) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && (document.activeElement === last || !element.contains(document.activeElement))) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      const wasTopModal = modalStack.at(-1) === entry;
      const index = modalStack.indexOf(entry);
      if (index !== -1) modalStack.splice(index, 1);
      if (modalStack.length === 0) {
        document.body.style.overflow = previousBodyOverflow;
      }
      if (wasTopModal && previousFocus?.isConnected) previousFocus.focus();
    };
  }, []);
  return (
    <div
      className="modal-backdrop"
      onMouseDown={(e) => e.target === e.currentTarget && modalStack.at(-1)?.element === modalRef.current && closeCallbackRef.current()}
    >
      <section ref={modalRef} className="modal" role="dialog" tabIndex={-1} aria-modal="true" aria-labelledby={titleId}>
        <header>
          <h2 id={titleId}>{title}</h2>
          <button ref={closeRef} aria-label="Close" onClick={close}>
            <X size={18} />
          </button>
        </header>
        {children}
      </section>
    </div>
  );
}
type FieldOption = string | { value: string; label: string };
export function ResourceEditor({
  fields,
  initial,
  save,
  busy,
}: {
  fields: {
    name: string;
    label?: string;
    type?: string;
    required?: boolean;
    min?: number;
    max?: number;
    options?: FieldOption[];
  }[];
  initial?: Row;
  save: (row: Row) => Promise<void>;
  busy: boolean;
}) {
  const [vals, setVals] = useState<Row>(initial || {}),
    [err, setErr] = useState("");
  return (
    <form
      className="form-grid"
      onSubmit={async (e) => {
        e.preventDefault();
        setErr("");
        try {
          const payload = { ...vals };
          fields
            .filter((f) => f.type === "datetime-local")
            .forEach((f) => {
              const v = payload[f.name];
              if (typeof v === "string" && v)
                payload[f.name] = new Date(v).toISOString();
            });
          await save(payload);
        } catch (ex) {
          setErr(ex instanceof Error ? ex.message : "Save failed");
        }
      }}
    >
      {fields.map((f) => (
        <label key={f.name}>
          {f.label || f.name.replaceAll("_", " ")}
          {f.options ? (
            <select
              required={f.required}
              value={
                f.type === "datetime-local" && vals[f.name]
                  ? new Date(String(vals[f.name]))
                      .toLocaleString("sv-SE")
                      .replace(" ", "T")
                      .slice(0, 16)
                  : String(vals[f.name] ?? "")
              }
              onChange={(e) => setVals({ ...vals, [f.name]: e.target.value })}
            >
              <option value="">Select…</option>
              {f.options.map((x) => {
                const value = typeof x === "string" ? x : x.value;
                const label = typeof x === "string" ? x : x.label;
                return (
                  <option key={value} value={value}>
                    {label}
                  </option>
                );
              })}
            </select>
          ) : (
            <input
              required={f.required}
              type={f.type || "text"}
              min={f.min}
              max={f.max}
              value={
                f.type === "datetime-local" && vals[f.name]
                  ? new Date(String(vals[f.name]))
                      .toLocaleString("sv-SE")
                      .replace(" ", "T")
                      .slice(0, 16)
                  : String(vals[f.name] ?? "")
              }
              onChange={(e) =>
                setVals({
                  ...vals,
                  [f.name]:
                    f.type === "number"
                      ? e.target.value === "" ? undefined : Number(e.target.value)
                      : e.target.value,
                })
              }
            />
          )}
        </label>
      ))}
      {err && <div className="form-error" role="alert">{err}</div>}
      <div className="form-actions">
        <Button type="submit" disabled={busy}>
          {busy ? "Saving…" : "Save record"}
        </Button>
      </div>
    </form>
  );
}
export function ReloadButton({ onClick }: { onClick: () => void }) {
  return (
    <button className="icon-button" onClick={onClick} aria-label="Refresh">
      <RefreshCw size={15} />
    </button>
  );
}
export function AddButton({
  onClick,
  children = "New record",
}: {
  onClick: () => void;
  children?: string;
}) {
  return (
    <Button onClick={onClick}>
      <Plus size={15} />
      {children}
    </Button>
  );
}
