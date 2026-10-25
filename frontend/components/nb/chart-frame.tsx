"use client";

import type { ReactNode } from "react";

import { cn } from "@/lib/cn";
import type { ViewState } from "@/lib/data-state";
import { NbCard } from "@/components/nb/card";
import { NbSkeleton } from "@/components/nb/skeleton";
import { NbState } from "@/components/nb/state";

export type NbActiveDotProps = {
  cx?: number;
  cy?: number;
};

export function NbActiveDot({ cx, cy }: NbActiveDotProps) {
  if (cx === undefined || cy === undefined) return null;

  return <rect x={cx - 4} y={cy - 4} width={8} height={8} fill="#000000" aria-hidden="true" />;
}

export type NbChartTooltipPayloadItem = {
  name?: string;
  value?: string | number;
  color?: string;
};

export type NbChartTooltipProps = {
  active?: boolean;
  label?: string | number;
  payload?: readonly NbChartTooltipPayloadItem[];
};

export function NbChartTooltip({ active, label, payload }: NbChartTooltipProps) {
  if (!active || !payload?.length) return null;

  return (
    <div className="border-4 border-ink bg-paper p-4 text-ink shadow-nb-4" role="status">
      {label !== undefined && <p className="font-mono font-bold">{label}</p>}
      <dl className={cn(label !== undefined && "mt-2", "space-y-2")}>
        {payload.map((item, index) => (
          <div className="flex items-baseline justify-between gap-4" key={`${item.name ?? "series"}-${index}`}>
            <dt>{item.name ?? "Series"}</dt>
            <dd className="font-mono">{item.value ?? ""}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

export type NbChartFrameProps<T> = {
  title: string;
  state: ViewState<T>;
  children: (data: T) => ReactNode;
  empty: string;
  className?: string;
  sourceMessage?: string;
  description?: string;
  partialActionLabel?: string;
  partialActionAriaLabel?: string;
};

export function NbChartFrame<T>({
  title,
  state,
  children,
  empty,
  className,
  sourceMessage,
  description,
  partialActionLabel,
  partialActionAriaLabel,
}: NbChartFrameProps<T>) {
  const chartState =
    state.status === "loading" ? (
      <div className="mt-4" role="group" aria-label={`Loading ${title}`} data-testid="chart-loading">
        <NbSkeleton variant="chart" />
      </div>
    ) : (
      <NbState state={state} empty={empty} sourceMessage={sourceMessage} partialActionLabel={partialActionLabel} partialActionAriaLabel={partialActionAriaLabel} className="mt-4">
        {(data) => (
          <div role="img" aria-label={title}>
            {children(data)}
          </div>
        )}
      </NbState>
    );

  return (
    <NbCard className={cn("chart-frame", className)} tone="paper">
      <h2 className="font-bold" style={{ fontSize: "var(--fs-h2)" }}>{title}</h2>
      {description && <p className="mt-2">{description}</p>}
      {chartState}
    </NbCard>
  );
}
