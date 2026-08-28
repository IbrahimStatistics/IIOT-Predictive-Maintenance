import { useEffect, useRef, useState, useCallback } from 'react';
import { useAuth } from './AuthContext';
import { API_BASE } from './AuthContext';

/**
 * Polls a GET endpoint on an interval and returns { data, error, loading }.
 *
 * This is the ONLY place in the app that knows requests are polled rather
 * than pushed. If this later becomes a WebSocket subscription, every
 * component using it keeps working unchanged — only this file changes.
 *
 * @param {string|null} path - API path, or null to skip fetching
 * @param {number} intervalMs
 */
export function usePolling(path, intervalMs = 3000) {
  const { token, logout } = useAuth();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const timerRef = useRef(null);
  const abortRef = useRef(null);

  const fetchOnce = useCallback(async () => {
    if (!path || !token) return;
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const res = await fetch(`${API_BASE}${path}`, {
        headers: { Authorization: `Bearer ${token}` },
        signal: controller.signal,
      });

      if (res.status === 401) {
        logout();
        return;
      }
      if (!res.ok) {
        throw new Error(`Request failed (${res.status})`);
      }

      const json = await res.json();
      setData(json);
      setError(null);
    } catch (err) {
      if (err.name !== 'AbortError') {
        setError(err.message);
      }
    } finally {
      setLoading(false);
    }
  }, [path, token, logout]);

  useEffect(() => {
    if (!path || !token) return undefined;

    fetchOnce();
    timerRef.current = setInterval(fetchOnce, intervalMs);

    // Cleanup is what makes this safe to mount/unmount repeatedly —
    // no leaked intervals, no stale requests resolving after unmount.
    return () => {
      clearInterval(timerRef.current);
      abortRef.current?.abort();
    };
  }, [path, token, intervalMs, fetchOnce]);

  return { data, error, loading };
}
