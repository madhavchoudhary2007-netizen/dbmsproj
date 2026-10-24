"use client";

import type { CSSProperties, ReactNode } from "react";

import { assertNever, type ViewState } from "@/lib/data-state";
import { cn } from "@/lib/cn";
import { NbButton } from "@/components/nb/button";
import { NbCard } from "@/components/nb/card";
import { StarBurst } from "@/components/nb/motifs";
import { NbSticker } from "@/components/nb/sticker";
import { NbSkeleton } from "@/components/nb/skeleton";

export type NbStateProps<T> = {
  state: ViewState<T>;
  empty: string;
  children: (data: T) => ReactNode;
  className?: string;
  nextAction?: ReactNode;
  shownCount?: number;
  sourceMessage?: string;
  loadingLabel?: string;
  skeletonRows?: number;
};

const stateCardStyle: CSSProperties = {
  color: "var(--nb-ink)",
  border: "4px solid var(--nb-ink)",
  display: "block",
  fontSize: "clamp(0.875rem, 0.8rem + 0.35vw, 1rem)",
};

export function NbState<T>({
  state,
  empty,
  children,
  className,
  nextAction,
  shownCount,
  sourceMessage,
  loadingLabel,
  skeletonRows,
}: NbStateProps<T>) {
  switch (state.status) {
    case "loading":
      return <NbSkeleton className={className} label={loadingLabel} rows={skeletonRows} data-testid="state-loading" />;
    case "populated":
      return (
        <div className={className} data-testid="state-populated">
          {children(state.data)}
        </div>
      );
    case "empty":
      return <NbCard className={cn("state", className)} data-testid="state-empty" tone="paper" style={{ ...stateCardStyle, background: "var(--nb-paper)" }} role="status">
          <div className="flex items-center gap-3">
            <NbSticker decorative tone="yellow">NO DATA ON TRACK</NbSticker>
            <StarBurst width={48} height={48} />
          </div>
          <p style={{ color: "inherit" }}>{empty}</p>
          {nextAction}
        </NbCard>;
    case "error":
      return <NbCard className={cn("state error", className)} data-testid="state-error" tone="red" style={{ ...stateCardStyle, background: "var(--nb-red)" }} role="alert" aria-live="assertive">
          <div className="flex items-start gap-3">
            <span aria-hidden="true" className="inline-flex size-11 shrink-0 items-center justify-center border-4 border-ink bg-ink text-2xl font-bold text-red">!</span>
            <div>
              <strong>Request failed</strong>
              <p style={{ color: "inherit" }}>{state.error.message}</p>
              {state.error.retryable ? (
                <NbButton variant="secondary" onClick={state.retry}>Try again</NbButton>
              ) : (
                nextAction
              )}
            </div>
          </div>
        </NbCard>;
    case "partial": {
      const count = shownCount ?? (Array.isArray(state.data) ? state.data.length : 0);
      return <NbCard className={cn("state", className)} data-testid="state-partial" tone="yellow" style={{ ...stateCardStyle, background: "var(--nb-yellow)" }} role="status">
          <div className="tx-caution" aria-hidden="true" />
          <p style={{ color: "inherit" }}>Showing {count} of {state.totalCount} records</p>
          <NbButton
            variant="secondary"
            onClick={state.filter.clear}
            aria-label={`Clear filter: ${state.filter.label}`}
          >
            Clear filter
          </NbButton>
          {sourceMessage && <p style={{ color: "inherit" }}>{sourceMessage}</p>}
          {children(state.data)}
        </NbCard>;
    }
    default:
      return assertNever(state);
  }
}
