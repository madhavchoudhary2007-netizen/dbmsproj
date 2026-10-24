"use client";

import { useMemo, useSyncExternalStore } from "react";

type DelayedFlagStore = {
  getSnapshot: () => boolean;
  getServerSnapshot: () => boolean;
  subscribe: (listener: () => void) => () => void;
};

function createDelayedFlagStore(active: boolean, delay: number): DelayedFlagStore {
  let visible = false;
  let timer: ReturnType<typeof setTimeout> | undefined;
  const listeners = new Set<() => void>();
  return {
    getSnapshot: () => visible,
    getServerSnapshot: () => false,
    subscribe: (listener) => {
      listeners.add(listener);
      if (active && !visible && timer === undefined && typeof window !== "undefined") {
        timer = setTimeout(() => {
          timer = undefined;
          visible = true;
          listeners.forEach((current) => current());
        }, Math.max(0, delay));
      }
      return () => {
        listeners.delete(listener);
        if (listeners.size === 0 && timer !== undefined) {
          clearTimeout(timer);
          timer = undefined;
        }
      };
    },
  };
}

export function useDelayedFlag(active: boolean, delay = 150): boolean {
  const store = useMemo(() => createDelayedFlagStore(active, delay), [active, delay]);
  return useSyncExternalStore(store.subscribe, store.getSnapshot, store.getServerSnapshot);
}
