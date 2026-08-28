/**
 * Derives a status from how far the latest reading deviates from the
 * recent trend within the visible window. This is a statistical outlier
 * check, NOT fault detection — there's no calibrated threshold or trained
 * model behind it yet. Labelled as a heuristic everywhere it's shown.
 */
export function deriveChannelStatus(series) {
  if (!series || series.length < 5) return 'nominal';
  const values = series.map((p) => p.v);
  const latest = values[values.length - 1];
  const rest = values.slice(0, -1);
  const mean = rest.reduce((a, b) => a + b, 0) / rest.length;
  const variance = rest.reduce((a, b) => a + (b - mean) ** 2, 0) / rest.length;
  const std = Math.sqrt(variance);
  if (std === 0) return 'nominal';
  const z = Math.abs((latest - mean) / std);
  if (z > 2.5) return 'fault';
  if (z > 1.2) return 'warn';
  return 'nominal';
}

/** 'up' | 'down' | 'stable', comparing the recent half of the window to the prior half. */
export function deriveTrend(series, lookback = 5) {
  if (!series || series.length < 4) return 'stable';
  const values = series.map((p) => p.v);
  const n = Math.min(lookback, Math.floor(values.length / 2)) || 1;
  const recent = values.slice(-n);
  const prior = values.slice(-2 * n, -n);
  if (prior.length === 0) return 'stable';
  const avg = (arr) => arr.reduce((a, b) => a + b, 0) / arr.length;
  const recentAvg = avg(recent);
  const priorAvg = avg(prior);
  const scale = Math.abs(priorAvg) || 1;
  const pct = (recentAvg - priorAvg) / scale;
  if (pct > 0.05) return 'up';
  if (pct < -0.05) return 'down';
  return 'stable';
}

/** Downsamples a raw sample array to roughly `target` points for waveform display. */
export function downsample(arr, target = 400) {
  if (!arr || arr.length <= target) return arr || [];
  const step = Math.ceil(arr.length / target);
  const out = [];
  for (let i = 0; i < arr.length; i += step) out.push(arr[i]);
  return out;
}
