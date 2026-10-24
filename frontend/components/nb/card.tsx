import type { HTMLAttributes } from "react";
import { cn } from "@/lib/cn";

type NbCardProps = HTMLAttributes<HTMLDivElement> & {
  tone?: "paper" | "cream" | "yellow" | "violet" | "mint" | "red";
  shadow?: 4 | 8 | 12;
  interactive?: boolean;
};

const tones = {
  paper: "bg-paper",
  cream: "bg-cream",
  yellow: "bg-yellow",
  violet: "bg-violet",
  mint: "bg-mint",
  red: "bg-red",
};

const shadows = {
  4: "shadow-nb-4",
  8: "shadow-nb-8",
  12: "shadow-nb-12 max-[619px]:shadow-nb-8",
};

const plinthShadows = {
  4: "[--nb-sh:4px]",
  8: "[--nb-sh:8px]",
  12: "[--nb-sh:12px] max-[619px]:[--nb-sh:8px]",
};

export function NbCard({
  children,
  className,
  tone = "paper",
  shadow = 8,
  interactive = false,
  ...props
}: NbCardProps) {
  const faceClass = cn(
    "nb-face block border-4 border-ink max-[619px]:border-[3px] rounded-none p-4 text-ink",
    tones[tone],
    !interactive && shadows[shadow],
  );

  if (interactive) {
    return (
      <div className={cn("nb-plinth", plinthShadows[shadow], className)}>
        <div {...props} className={faceClass}>
          {children}
        </div>
      </div>
    );
  }

  return (
    <div {...props} className={cn(faceClass, className)}>
      {children}
    </div>
  );
}
