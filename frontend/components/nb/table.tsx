"use client";

import type { Key, ReactNode, Ref } from "react";

import { cn } from "@/lib/cn";
import type { ViewState } from "@/lib/data-state";
import { NbState } from "@/components/nb/state";

export type NbTableColumn<T extends Record<string, unknown>> = {
  key: string;
  title: ReactNode;
  numeric?: boolean;
  render?: (row: T) => ReactNode;
};

export type NbTableProps<T extends Record<string, unknown>> = {
  state: ViewState<readonly T[]>;
  columns: readonly NbTableColumn<T>[];
  rowKey: (row: T, index: number) => Key;
  caption: string;
  empty?: string;
  onSelect?: (row: T) => void;
  className?: string;
  pageSize?: number;
  sourceMessage?: string;
  ref?: Ref<HTMLTableElement>;
};

export function NbTable<T extends Record<string, unknown>>({
  state,
  columns,
  rowKey,
  caption,
  empty = "No records returned by the API.",
  onSelect,
  className,
  pageSize = 8,
  sourceMessage,
  ref,
}: NbTableProps<T>) {
  const isNestedControl = (target: EventTarget | null) => target instanceof HTMLElement && Boolean(target.closest("a,button,input,select,textarea,[role=button],[role=link],[contenteditable=true]"));
  const renderTable = (rows: readonly T[]) => (
    <div className="min-w-0 max-w-full overflow-x-auto shadow-nb-4">
      <table ref={ref} className={cn("min-w-full border-collapse text-left", className)}>
        <caption className="sr-only">{caption}</caption>
        <thead className="sticky top-0 z-10">
          <tr>
            {columns.map((column) => (
              <th key={column.key} scope="col" className={cn("!border-b-2 !border-[var(--nb-ink)] !bg-[var(--nb-ink)] !px-3 !py-3 !text-[length:var(--fs-data)] !font-bold !text-[var(--nb-paper)]", column.numeric && "text-right")}>{column.title}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => {
            const selectable = Boolean(onSelect);
            const select = () => onSelect?.(row);
            return (
              <tr
                key={rowKey(row, index)}
                className={cn("h-12 odd:!bg-[var(--nb-paper)] even:!bg-[var(--nb-cream)] hover:!bg-[var(--nb-yellow)] focus-visible:outline-4 focus-visible:outline-[var(--nb-yellow)] focus-visible:outline-offset-[-4px]", selectable && "clickable")}
                onClick={onSelect ? (event) => { if (!isNestedControl(event.target)) select(); } : undefined}
                onKeyDown={onSelect ? (event) => {
                  if ((event.key === "Enter" || event.key === " ") && !isNestedControl(event.target)) {
                    event.preventDefault();
                    select();
                  }
                } : undefined}
                tabIndex={selectable ? 0 : undefined}
              >
                {columns.map((column) => (
                  <td key={column.key} className={cn("h-12 !border-b-2 !border-[var(--nb-ink)] !px-3 !py-2 !text-[length:var(--fs-data)] !text-[var(--nb-ink)]", column.numeric && "font-mono tabular-nums text-right")}>{column.render ? column.render(row) : String(row[column.key] ?? "—")}</td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );

  return <NbState state={state} empty={empty} className={className} sourceMessage={sourceMessage} skeletonRows={pageSize}>{renderTable}</NbState>;
}
