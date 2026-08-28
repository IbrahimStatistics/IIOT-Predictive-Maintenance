import { usePolling } from './usePolling';

/** Fleet overview: machine_id, last_seen, window_count for every machine. */
export function useMachines() {
  return usePolling('/machines', 4000);
}

/** Per-window RMS summary for a machine's current-signature channels (Ia/Ib/Ic). */
export function useCurrentSummary(machineId, limit = 40) {
  const path = machineId
    ? `/telemetry/current/summary?machine_id=${encodeURIComponent(machineId)}&limit=${limit}`
    : null;
  return usePolling(path, 3000);
}

/** Per-window RMS summary for a machine's vibration channels (Ax/Ay/Az). */
export function useVibrationSummary(machineId, limit = 40) {
  const path = machineId
    ? `/telemetry/vibration/summary?machine_id=${encodeURIComponent(machineId)}&limit=${limit}`
    : null;
  return usePolling(path, 3000);
}

/**
 * Fetches the single latest raw window (full sample array) for a channel,
 * only while `enabled` — this is NOT part of the always-on polling set,
 * since raw arrays are large. Used by the waveform toggle in GaugeCard.
 */
export function useRawWindow(table, machineId, enabled) {
  const path = enabled && machineId
    ? `/telemetry/${table}?machine_id=${encodeURIComponent(machineId)}&limit=1`
    : null;
  return usePolling(path, 5000);
}

/** Derives a status ('ok' | 'offline') from a machine's last_seen timestamp.
 * Pure function, not a hook — kept separate so it's independently testable.
 */
export function deriveMachineStatus(lastSeen, staleAfterMs = 15000) {
  if (!lastSeen) return 'offline';
  const age = Date.now() - new Date(lastSeen).getTime();
  return age > staleAfterMs ? 'offline' : 'ok';
}
