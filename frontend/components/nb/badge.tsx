import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "@/lib/cn";

const statusToneClasses: Record<string, string> = {
  SCHEDULED: "bg-cream",
  LIVE: "bg-red",
  ACTIVE: "bg-red",
  PAUSED: "bg-yellow",
  RESERVED: "bg-yellow",
  OPEN: "bg-yellow",
  FINISHED: "bg-mint",
  COMPLETED: "bg-mint",
  APPROVED: "bg-mint",
  ARCHIVED: "bg-paper",
  REJECTED: "bg-red",
  CANCELLED: "bg-cream",
};

export interface NbBadgeProps extends HTMLAttributes<HTMLSpanElement> {
  status: string;
  children?: ReactNode;
}

export function NbBadge({ className, children, status, ...props }: NbBadgeProps) {
  const statusKey = status.trim().toUpperCase();
  const isLive = statusKey === "LIVE";
  const toneClass = statusToneClasses[statusKey] ?? "bg-cream";

  return (
    <span
      {...props}
      className={cn(
        "inline-flex items-center gap-2 border-4 border-ink px-3 py-2 font-sans text-sm font-bold uppercase leading-tight text-ink",
        toneClass,
        isLive && "rounded-full",
      )}
    >
      {isLive && <span aria-hidden="true" className="h-2 w-2 shrink-0 rounded-full bg-ink" />}
      {children ?? status}
    </span>
  );
}
