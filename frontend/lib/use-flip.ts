import { useLayoutEffect, useRef, type RefObject } from "react";
import { useReducedMotion } from "./use-reduced-motion";

type RunningFlip = { animation: Animation; originalWillChange: string };

export function useFlip(
  ref: RefObject<HTMLElement | null>,
  keys: readonly (string | number)[],
): void {
  const reducedMotion = useReducedMotion();
  const previousTops = useRef(new Map<string, number>());
  const running = useRef(new Map<HTMLElement, RunningFlip>());

  useLayoutEffect(() => {
    const activeAnimations = running.current;
    for (const [element, item] of activeAnimations) {
      if (activeAnimations.get(element) !== item) continue;
      item.animation.cancel();
      element.style.willChange = item.originalWillChange;
      activeAnimations.delete(element);
    }

    const root = ref.current;
    const rows = new Map<string, HTMLElement>();
    if (root) {
      for (const child of Array.from(root.children)) {
        if (child instanceof HTMLElement) {
          const key = child.getAttribute("data-flip-key");
          if (key !== null) rows.set(key, child);
        }
      }
    }

    const currentTops = new Map<string, number>();
    for (const key of keys) {
      const normalizedKey = String(key);
      const row = rows.get(normalizedKey);
      if (row) currentTops.set(normalizedKey, row.getBoundingClientRect().top);
    }

    if (!reducedMotion && keys.length <= 30 && previousTops.current.size > 0) {
      for (const [key, top] of currentTops) {
        const previousTop = previousTops.current.get(key);
        const row = rows.get(key);
        if (previousTop === undefined || !row) continue;
        const delta = previousTop - top;
        if (delta === 0) continue;

        const item: RunningFlip = {
          animation: row.animate(
            [{ transform: `translateY(${delta}px)` }, { transform: "translateY(0px)" }],
            { duration: 300, easing: "ease-out" },
          ),
          originalWillChange: row.style.willChange,
        };
        row.style.willChange = "transform";
        activeAnimations.set(row, item);
        const cleanup = () => {
          if (activeAnimations.get(row) !== item) return;
          row.style.willChange = item.originalWillChange;
          activeAnimations.delete(row);
        };
        item.animation.onfinish = cleanup;
        item.animation.oncancel = cleanup;
      }
    }

    previousTops.current = currentTops;
    return () => {
      for (const [element, item] of activeAnimations) {
        if (activeAnimations.get(element) !== item) continue;
        item.animation.cancel();
        element.style.willChange = item.originalWillChange;
        activeAnimations.delete(element);
      }
    };
  });
}
