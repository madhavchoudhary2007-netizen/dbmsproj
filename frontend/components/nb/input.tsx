"use client";

import * as React from "react";

import { cn } from "@/lib/cn";

const controlClasses =
  "block min-h-12 w-full min-w-0 rounded-none border-4 border-ink bg-paper px-3 py-2 font-sans text-[length:var(--fs-body)] font-medium text-ink focus-visible:ring-4 focus-visible:ring-yellow focus-visible:outline-4 focus-visible:outline-solid focus-visible:outline-ink focus-visible:outline-offset-4 disabled:cursor-not-allowed disabled:opacity-60";

export const NbInput = React.forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement>
>(function NbInput({ className, style, type, ...props }, ref) {
  return (
    <input
      {...props}
      ref={ref}
      type={type ?? "text"}
      style={{ minWidth: "44px", ...style }}
      className={cn(controlClasses, className)}
    />
  );
});

NbInput.displayName = "NbInput";

export const NbSelect = React.forwardRef<
  HTMLSelectElement,
  React.SelectHTMLAttributes<HTMLSelectElement>
>(function NbSelect({ className, style, ...props }, ref) {
  return (
    <select
      {...props}
      ref={ref}
      style={{ minWidth: "44px", ...style }}
      className={cn(controlClasses, className)}
    />
  );
});

NbSelect.displayName = "NbSelect";

export const NbTextarea = React.forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement>
>(function NbTextarea({ className, style, ...props }, ref) {
  return (
    <textarea
      {...props}
      ref={ref}
      style={{ minWidth: "44px", ...style }}
      className={cn(controlClasses, "min-h-24 resize-y", className)}
    />
  );
});

NbTextarea.displayName = "NbTextarea";
