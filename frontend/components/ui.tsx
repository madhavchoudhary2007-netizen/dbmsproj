"use client";

import {
  RefreshCw,
  AlertCircle,
  LoaderCircle,
} from "lucide-react";
import { Row, pretty } from "@/lib/api";

export { Modal } from "./modal";
export type { ModalProps } from "./modal";
export { ResourceEditor } from "./resource-editor";
export type {
  FieldOption,
  ResourceEditorField,
  ResourceEditorProps,
} from "./resource-editor";

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
  "data-primary": dataPrimary,
}: {
  children: React.ReactNode;
  onClick?: () => void;
  type?: "button" | "submit";
  disabled?: boolean;
  kind?: "primary" | "secondary" | "danger";
  "data-primary"?: string | boolean;
}) {
  return (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      data-primary={dataPrimary}
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
      <div className="state" role="status" aria-live="polite">
        <LoaderCircle className="spin" /> Loading from API…
      </div>
    );
  if (error)
    return (
      <div className="state error" role="alert" aria-live="assertive">
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
  if (empty) return <div className="state" role="status" aria-live="polite">{empty}</div>;
  return null;
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
    return <div className="state" role="status">No records returned by the API.</div>;
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

export function ReloadButton({ onClick, "data-primary": dataPrimary }: { onClick: () => void; "data-primary"?: string | boolean }) {
  return (
    <button className="icon-button" onClick={onClick} aria-label="Refresh" data-primary={dataPrimary}>
      <RefreshCw size={15} />
    </button>
  );
}