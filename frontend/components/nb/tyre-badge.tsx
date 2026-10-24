import type { CSSProperties, HTMLAttributes } from "react";

import { cn } from "@/lib/cn";

type TyreCompound = "SOFT" | "MEDIUM" | "HARD" | "INTERMEDIATE" | "WET";

const compoundLetters: Record<TyreCompound, string> = {
  SOFT: "S",
  MEDIUM: "M",
  HARD: "H",
  INTERMEDIATE: "I",
  WET: "W",
};

const compoundTones: Record<TyreCompound, string> = {
  SOFT: "bg-red",
  MEDIUM: "bg-yellow",
  HARD: "bg-paper",
  INTERMEDIATE: "bg-mint",
  WET: "bg-sky",
};

export interface TyreBadgeProps extends HTMLAttributes<HTMLSpanElement> {
  compound: TyreCompound;
}

export function TyreBadge({ className, style, compound, ...props }: TyreBadgeProps) {
  const tyreStyle: CSSProperties = {
    ...style,
    height: 28,
    width: 28,
  };

  return (
    <span
      {...props}
      role="img"
      aria-label={`${compound} tyre`}
      className={cn(
        "inline-flex shrink-0 items-center justify-center rounded-full border-4 border-ink font-sans text-sm font-bold leading-none text-ink",
        compoundTones[compound],
        className,
      )}
      style={tyreStyle}
    >
      {compoundLetters[compound]}
    </span>
  );
}
