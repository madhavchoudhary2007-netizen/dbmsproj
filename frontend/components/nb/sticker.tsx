import type { CSSProperties, HTMLAttributes } from "react";

import { cn } from "@/lib/cn";

type StickerTilt = -3 | -2 | 2 | 3;
type StickerTone = "paper" | "cream" | "yellow" | "violet" | "mint" | "red";
type StickerStyle = CSSProperties & { "--tilt": `${StickerTilt}deg` };

const toneClasses: Record<StickerTone, string> = {
  paper: "bg-paper",
  cream: "bg-cream",
  yellow: "bg-yellow",
  violet: "bg-violet",
  mint: "bg-mint",
  red: "bg-red",
};

export interface NbStickerProps extends HTMLAttributes<HTMLSpanElement> {
  tilt?: StickerTilt;
  tone?: StickerTone;
  decorative?: boolean;
}

export function NbSticker({
  className,
  children,
  decorative = false,
  style,
  tilt = -2,
  tone = "yellow",
  ...props
}: NbStickerProps) {
  const stickerStyle = {
    ...style,
    "--tilt": `${tilt}deg`,
  } as StickerStyle;

  return (
    <span
      {...props}
      aria-hidden={decorative ? "true" : undefined}
      className={cn(
        "nb-sticker inline-block border-4 border-ink px-3 py-2 font-sans text-sm font-bold uppercase leading-tight text-ink",
        toneClasses[tone],
        className,
      )}
      style={stickerStyle}
    >
      {children}
    </span>
  );
}
