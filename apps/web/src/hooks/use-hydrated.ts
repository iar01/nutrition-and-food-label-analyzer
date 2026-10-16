import { useSyncExternalStore } from 'react';

const subscribe = (): (() => void) => () => {};

/** false during server rendering and the first client render, true afterwards. */
export function useHydrated(): boolean {
  return useSyncExternalStore(subscribe, () => true, () => false);
}
