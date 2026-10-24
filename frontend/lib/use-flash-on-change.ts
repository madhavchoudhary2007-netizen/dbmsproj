import { useLayoutEffect, useRef, type RefObject } from "react";
import { useReducedMotion } from "./use-reduced-motion";

type RunningFlash = { animation: Animation };

export function useFlashOnChange<T>(
  ref: RefObject<HTMLElement | null>,
  value: T,
): void {
  const reducedMotion = useReducedMotion();
  const previousValue = useRef(value);
  const hasMounted = useRef(false);
  const lastStartedAt = useRef(Number.NEGATIVE_INFINITY);
  const running = useRef<RunningFlash | null>(null);

  useLayoutEffect(() => {
    const element = ref.current;
    if (reducedMotion) {
      running.current?.animation.cancel();
      running.current = null;
    }

    if (!hasMounted.current) {
      hasMounted.current = true;
      previousValue.current = value;
      return;
    }
    const changed = !Object.is(previousValue.current, value);
    previousValue.current = value;
    if (!changed || reducedMotion || !element || running.current) return;

    const now = performance.now();
    if (now - lastStartedAt.current < 200) return;
    const original = getComputedStyle(element).backgroundColor;
    const highlight = getComputedStyle(element).getPropertyValue("--nb-yellow").trim();
    if (!highlight) return;

    lastStartedAt.current = now;
    const item: RunningFlash = {
      animation: element.animate(
        [
          { backgroundColor: original },
          { backgroundColor: highlight },
          { backgroundColor: original },
        ],
        { duration: 200, easing: "ease-out" },
      ),
    };
    running.current = item;
    const cleanup = () => {
      if (running.current === item) running.current = null;
    };
    item.animation.onfinish = cleanup;
    item.animation.oncancel = cleanup;
  }, [value, reducedMotion, ref]);

  useLayoutEffect(() => () => {
    running.current?.animation.cancel();
    running.current = null;
  }, []);
}
