import type { HTMLAttributes } from "react";

import { cn } from "@/lib/cn";

type MarqueeTone = "red" | "yellow" | "paper";
export interface NbMarqueeProps extends Omit<HTMLAttributes<HTMLUListElement>, "children"> {
  items: readonly string[];
  tone?: MarqueeTone;
}

const toneClasses: Record<MarqueeTone, string> = { red: "bg-red", yellow: "bg-yellow", paper: "bg-paper" };

export function NbMarquee({ items, tone = "red", className, ...props }: NbMarqueeProps) {
  return (
    <ul {...props} aria-live="off" className={cn("nb-marquee border-4 border-ink px-4 py-3 font-mono text-sm font-bold uppercase text-ink", toneClasses[tone], className)}>
      {items.map((item, index) => <li key={`${item}-${index}`} className="starting:opacity-0">{item}</li>)}
    </ul>
  );
}
