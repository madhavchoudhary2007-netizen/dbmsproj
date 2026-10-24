"use client";

import { forwardRef, type ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/cn";

type NbButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "accent" | "danger" | "ghost";
  size?: "md" | "lg";
  busy?: boolean;
};

const variants = {
  primary: "bg-red",
  secondary: "bg-paper",
  accent: "bg-yellow",
  danger: "bg-red",
  ghost: "bg-cream",
};

const sizes = {
  md: "min-h-[44px] min-w-[44px] px-4 py-2",
  lg: "min-h-[56px] min-w-[44px] px-4 py-4",
};

export const NbButton = forwardRef<HTMLButtonElement, NbButtonProps>(
  function NbButton(
    {
      children,
      className,
      variant = "secondary",
      size = "md",
      busy = false,
      disabled,
      type = "button",
      ...props
    },
    ref,
  ) {
    return (
      <button
        {...props}
        ref={ref}
        type={type}
        disabled={disabled || busy}
        aria-busy={busy || props["aria-busy"] || undefined}
        className={cn("nb-plinth inline-flex min-h-[44px] min-w-[44px] align-top [--nb-sh:4px]", className)}
      >
        <span
          className={cn(
            "nb-face flex min-h-[44px] min-w-[44px] w-full items-center justify-center gap-2 border-4 border-ink text-ink font-bold rounded-none",
            variants[variant],
            sizes[size],
          )}
        >
          {busy ? (
            <>
              <span aria-hidden="true" className="size-2 bg-ink" />
              <span>Working…</span>
            </>
          ) : (
            <>
              {variant === "danger" && <span aria-hidden="true">!</span>}
              {children}
            </>
          )}
        </span>
      </button>
    );
  },
);
