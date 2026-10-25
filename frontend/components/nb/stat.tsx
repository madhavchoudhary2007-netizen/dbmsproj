import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "@/lib/cn";
import { Arrow } from "./motifs";
import { NbSticker } from "./sticker";
import type { NbStickerProps } from "./sticker";

type StatDirection = "up" | "down" | "flat";
type StatTone = "paper" | "red" | "yellow" | "violet" | "mint";

const toneClasses: Record<StatTone, string> = {
  paper: "bg-paper",
  red: "bg-red",
  yellow: "bg-yellow",
  violet: "bg-violet",
  mint: "bg-mint",
};

export interface NbStatProps extends HTMLAttributes<HTMLDivElement> {
  value: ReactNode;
  label: ReactNode;
  delta?: string;
  direction?: StatDirection;
  tone?: StatTone;
  stickerTilt?: NbStickerProps["tilt"];
}

export function NbStat({ value, label, delta, direction = "flat", tone = "paper", stickerTilt, className, ...props }: NbStatProps) {
  return (
    <div {...props} className={cn("border-4 border-ink p-4", toneClasses[tone], className)}>
      <dl><dt><NbSticker tone="yellow" tilt={stickerTilt}>{label}</NbSticker></dt><dd className="mt-3 font-mono text-3xl font-bold tabular-nums leading-none text-ink">{value}</dd></dl>
      {delta ? <p className="mt-3 flex items-center gap-2 text-sm font-bold text-ink" data-direction={direction}><span className="sr-only">{direction} </span><Arrow className={cn("size-6", direction === "down" && "rotate-90")} direction={direction === "flat" ? "right" : "diagonal"} /><span>{delta}</span></p> : null}
    </div>
  );
}
