import type { ReactNode, SVGProps } from "react";

import { cn } from "@/lib/cn";

type MotifProps = Omit<SVGProps<SVGSVGElement>, "aria-hidden" | "focusable" | "points"> & { className?: string };
type StarBurstProps = MotifProps & { points?: 8 | 12 };
type ArrowProps = MotifProps & { direction?: "right" | "diagonal" };
type RaceFlagProps = MotifProps & { tone?: "green" | "yellow" | "red" | "chequered" };

function MotifSvg({ children, className, ...props }: MotifProps & { children: ReactNode }) {
  return (
    <svg
      {...props}
      className={cn("shrink-0", className)}
      aria-hidden="true"
      focusable={false}
      stroke="var(--nb-ink)"
      strokeWidth={3}
      strokeLinecap="square"
      strokeLinejoin="miter"
    >
      {children}
    </svg>
  );
}

export function StarBurst({ points = 8, ...props }: StarBurstProps) {
  const vertices = Array.from({ length: points * 2 }, (_, index) => {
    const radius = index % 2 === 0 ? 20 : 9;
    const angle = (Math.PI * index) / points - Math.PI / 2;
    return `${24 + Math.cos(angle) * radius},${24 + Math.sin(angle) * radius}`;
  }).join(" ");
  return <MotifSvg {...props} viewBox="0 0 48 48" fill="var(--nb-yellow)"><polygon points={vertices} /></MotifSvg>;
}

export function Arrow({ direction = "right", ...props }: ArrowProps) {
  return <MotifSvg {...props} viewBox="0 0 48 24" fill="none"><path d={direction === "diagonal" ? "M8 20 36 4M25 4h11v11" : "M4 12h36M28 4l12 8-12 8"} /></MotifSvg>;
}

export function CheckerStrip(props: MotifProps) {
  return <MotifSvg {...props} viewBox="0 0 64 16" fill="var(--nb-ink)"><rect width="64" height="16" fill="var(--nb-paper)" stroke="none" />{Array.from({ length: 8 }, (_, index) => <rect key={index} x={(index % 8) * 8} y={index % 2 ? 0 : 8} width="8" height="8" />)}<path d="M0 0h64v16H0z" fill="none" /></MotifSvg>;
}

export function SpeedLines(props: MotifProps) {
  return <MotifSvg {...props} viewBox="0 0 48 24" fill="none"><path d="M4 6h40M4 12h32M4 18h24" /></MotifSvg>;
}

export function RaceFlag({ tone = "green", ...props }: RaceFlagProps) {
  const fill = tone === "green" ? "var(--nb-mint)" : tone === "yellow" ? "var(--nb-yellow)" : "var(--nb-red)";
  return (
    <MotifSvg {...props} viewBox="0 0 48 48" fill="none">
      <path d="M8 4v40" />
      {tone === "chequered" ? (
        <g fill="var(--nb-ink)" stroke="none">
          <rect x="8" y="4" width="32" height="32" fill="var(--nb-paper)" />
          <path d="M8 4h8v8H8zm16 0h8v8h-8zM16 12h8v8h-8zm16 0h8v8h-8zM8 20h8v8H8zm16 0h8v8h-8zM16 28h8v8h-8zm16 0h8v8h-8z" />
        </g>
      ) : (
        <>
          <path d="M8 4h32L32 20l8 16H8z" fill={fill} />
          <path
            d={
              tone === "green"
                ? "M16 12a5 5 0 1 0 10 0 5 5 0 1 0-10 0"
                : tone === "yellow"
                  ? "m24 8 5 10H19z"
                  : "M18 8l12 12m0-12L18 20"
            }
          />
        </>
      )}
    </MotifSvg>
  );
}
