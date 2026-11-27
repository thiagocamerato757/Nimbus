import { useCallback, useEffect, useRef, useState } from 'react';
import { ApiError, requestSnapshot, type Snapshot } from './api';

// All screens can subscribe to a versioned API snapshot. Polls never overlap;
// revisions prevent a slower earlier response from replacing newer state.
export function useLiveQuery<T>(path: string) {
  const [snapshot, setSnapshot] = useState<Snapshot<T> | null>(null);
  const [error, setError] = useState('');
  const active = useRef(true);
  const accept = useCallback((next: Snapshot<T>) => {
    if (active.current) setSnapshot(previous =>
      previous && Number(previous.version) > Number(next.version) ? previous : next);
  }, []);
  const refresh = useCallback(async () => {
    try {
      accept(await requestSnapshot<T>(path));
      if (active.current) setError('');
    } catch (e) {
      if (active.current) setError(e instanceof ApiError ? e.code : 'unexpected');
    }
  }, [accept, path]);
  useEffect(() => {
    active.current = true;
    let stopped = false;
    let timer: ReturnType<typeof setTimeout>;
    async function poll() {
      await refresh();
      if (!stopped) timer = setTimeout(() => void poll(), 1000);
    }
    void poll();
    const wake = () => { void refresh(); };
    window.addEventListener('focus', wake);
    return () => {
      stopped = true; active.current = false; clearTimeout(timer);
      window.removeEventListener('focus', wake);
    };
  }, [refresh]);
  return { snapshot, refresh, accept, error };
}
