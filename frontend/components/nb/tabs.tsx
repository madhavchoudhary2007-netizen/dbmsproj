"use client";

import { forwardRef, useId, useRef, type KeyboardEvent } from "react";
import { cn } from "@/lib/cn";
import { NbButton } from "./button";

export type NbTabItem = {
  id: string;
  label: string;
  panelId?: string;
  disabled?: boolean;
};

export type NbTabsProps = {
  id?: string;
  label: string;
  items: readonly NbTabItem[];
  value: string;
  onChange: (id: string) => void;
  className?: string;
};

export const NbTabs = forwardRef<HTMLDivElement, NbTabsProps>(
  function NbTabs({ id, label, items, value, onChange, className }, ref) {
    const generatedId = useId();
    const tabPrefix = id ?? generatedId;
    const buttonsRef = useRef<Record<string, HTMLButtonElement | null>>({});
    const selected = items.find((item) => item.id === value && !item.disabled);
    const fallback = items.find((item) => !item.disabled);
    const selectedId = selected?.id ?? fallback?.id;

    const handleKeyDown = (event: KeyboardEvent<HTMLButtonElement>, itemId: string) => {
      const key = event.key;
      if (key !== "ArrowRight" && key !== "ArrowLeft" && key !== "Home" && key !== "End") return;
      event.preventDefault();
      const enabled = items.filter((item) => !item.disabled);
      if (!enabled.length) return;
      const currentIndex = Math.max(0, enabled.findIndex((item) => item.id === itemId));
      const nextIndex = key === "Home"
        ? 0
        : key === "End"
          ? enabled.length - 1
          : (currentIndex + (key === "ArrowRight" ? 1 : -1) + enabled.length) % enabled.length;
      const nextId = enabled[nextIndex].id;
      buttonsRef.current[nextId]?.focus();
      if (nextId !== value) onChange(nextId);
    };

    return (
      <div ref={ref} role="tablist" aria-label={label} className={cn("flex flex-wrap items-end gap-0", className)}>
        {items.map((item) => {
          const tabId = `${tabPrefix}-tab-${item.id}`;
          return (
            <NbButton
              key={item.id}
              ref={(button) => { buttonsRef.current[item.id] = button; }}
              type="button"
              role="tab"
              variant={item.id === selectedId ? "accent" : "secondary"}
              disabled={item.disabled}
              tabIndex={item.id === selectedId ? 0 : -1}
              aria-selected={item.id === selectedId}
              {...(item.panelId ? { "aria-controls": item.panelId } : {})}
              id={tabId}
              onClick={() => onChange(item.id)}
              onKeyDown={(event) => handleKeyDown(event, item.id)}
              className={cn("min-h-11 min-w-11", item.id === selectedId && "relative -top-1")}
            >
              {item.label}
            </NbButton>
          );
        })}
      </div>
    );
  },
);
