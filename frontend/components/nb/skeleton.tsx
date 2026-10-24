"use client";

import type { HTMLAttributes } from "react";

import { useDelayedFlag } from "@/lib/use-delayed-flag";

type NbSkeletonProps = HTMLAttributes<HTMLDivElement> & {
  variant?: "rows" | "card" | "chart";
  rows?: number;
  label?: string;
};

const blockStyle = { height: 36 };

export function NbSkeleton({
  className,
  style,
  variant = "rows",
  rows = 3,
  label = "Loading from API…",
  ...props
}: NbSkeletonProps) {
  const visible = useDelayedFlag(true, 150);
  const rowCount = Number.isFinite(rows) ? Math.min(8, Math.max(1, Math.floor(rows))) : 3;
  const reservedHeight = variant === "rows" ? 48 * (rowCount + 1) : variant === "card" ? 128 : 220;

  return (
    <div
      {...props}
      className={className}
      role="status"
      aria-busy="true"
      style={{ minHeight: reservedHeight, height: reservedHeight, ...style }}
    >
      <span className="sr-only">{label}</span>
      {visible &&
        (variant === "rows" ? (
          <div className="flex flex-col gap-3" style={{ height: reservedHeight, paddingBlockEnd: 12 }} aria-hidden="true">
            {Array.from({ length: rowCount + 1 }, (_, index) => (
              <div
                key={index}
                className="nb-skeleton"
                style={{ ...blockStyle, width: index === 0 ? "72%" : "100%" }}
              />
            ))}
          </div>
        ) : (
          <div className="nb-skeleton" style={{ height: "100%" }} aria-hidden="true" />
        ))}
    </div>
  );
}
