import { useLayoutEffect, useRef, type RefObject } from "react";
import { useReducedMotion } from "./use-reduced-motion";

type RunningFlip = { animation: Animation; originalWillChange: string };

export function useFlip(
  ref: RefObject<HTMLElement | null>,
  keys: readonly (string | number)[],
): void {
  const reducedMotion = useReducedMotion();
  const previousTops = useRef(new Map<string, number>());
  const previousKeys = useRef<string[] | null>(null);
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
    const rootTop = root?.getBoundingClientRect().top ?? 0;
    for (const key of keys) {
      const normalizedKey = String(key);
      const row = rows.get(normalizedKey);
      if (row) {
        currentTops.set(normalizedKey, row.getBoundingClientRect().top - rootTop);
      }
    }

    const currentKeys = keys.map(String);
    const previousKeysValue = previousKeys.current;
    const keyOrderChanged =
      previousKeysValue !== null &&
      (previousKeysValue.length !== currentKeys.length ||
        previousKeysValue.some((key, index) => key !== currentKeys[index]));

    if (
      !reducedMotion &&
      keys.length <= 30 &&
      keyOrderChanged &&
      previousTops.current.size > 0
    ) {
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
    previousKeys.current = currentKeys;
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
