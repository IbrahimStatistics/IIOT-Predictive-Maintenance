import { useState } from 'react';
import { LineChart, Line, ResponsiveContainer, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { deriveChannelStatus, deriveTrend, downsample } from '../lib/channelAnalysis';
import { useRawWindow } from '../lib/useTelemetry';

const STATUS_META = {
  nominal: { label: 'NOMINAL', color: 'var(--status-ok)', bg: 'var(--status-ok-bg)' },
  warn: { label: 'WARNING', color: 'var(--status-warn)', bg: 'var(--status-warn-bg)' },
  fault: { label: 'OUTLIER', color: 'var(--status-fault)', bg: 'var(--status-fault-bg)' },
};

const TREND_META = {
  up: { glyph: '▲', color: 'var(--status-warn)' },
  down: { glyph: '▼', color: 'var(--color-ink-muted)' },
  stable: { glyph: '▬', color: 'var(--color-ink-muted)' },
};

function formatTime(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleTimeString('en-GB', { hour12: false });
}

function Tick(props) {
  const { x, y, payload } = props;
  return (
    <text x={x} y={y + 12} textAnchor="middle" fontSize={10} fill="var(--color-ink-muted)" fontFamily="var(--font-mono)">
      {formatTime(payload.value)}
    </text>
  );
}

function CustomTooltip({ active, payload, unit }) {
  if (!active || !payload || !payload.length) return null;
  const p = payload[0].payload;
  return (
    <div style={styles.tooltip}>
      <div className="mono" style={{ fontSize: 11, color: '#B7BEC7' }}>{formatTime(p.t)}</div>
      <div className="mono" style={{ fontSize: 13, fontWeight: 600 }}>{p.v.toFixed(4)} {unit}</div>
    </div>
  );
}

/**
 * `series`: array of { t: isoTimestamp, v: number } — RMS per window, oldest first.
 * `rawSource`: optional { table: 'current'|'vibration', field: 'Ia' } to enable
 * the on-demand raw waveform toggle for this channel.
 */
export function GaugeCard({ label, series, unit = 'A', machineId, rawSource }) {
  const [showWaveform, setShowWaveform] = useState(false);
  const hasData = series && series.length > 0;
  const latest = hasData ? series[series.length - 1].v : null;
  const values = hasData ? series.map((p) => p.v) : [];
  const min = values.length ? Math.min(...values) : null;
  const max = values.length ? Math.max(...values) : null;
  const status = deriveChannelStatus(series);
  const trend = deriveTrend(series);
  const statusMeta = STATUS_META[status];
  const trendMeta = TREND_META[trend];

  const { data: rawRow } = useRawWindow(rawSource?.table, machineId, showWaveform && Boolean(rawSource));
  const rawArray = rawSource && rawRow && rawRow[0] ? rawRow[0][rawSource.field] : null;
  const waveformData = rawArray ? downsample(rawArray, 400).map((v, i) => ({ i, v })) : null;

  return (
    <div style={styles.card}>
      <div style={styles.header}>
        <div>
          <div className="label">{label}</div>
          <div style={styles.readoutRow}>
            <span className="mono" style={styles.readout}>
              {latest != null ? latest.toFixed(3) : '—.———'}
            </span>
            <span style={{ fontSize: 11, color: 'var(--color-ink-muted)' }}>{unit}</span>
            {hasData && (
              <span style={{ color: trendMeta.color, fontSize: 11, marginLeft: 4 }} title={`Trend: ${trend}`}>
                {trendMeta.glyph}
              </span>
            )}
          </div>
        </div>
        <span style={{ ...styles.pill, color: statusMeta.color, background: statusMeta.bg }}>
          {statusMeta.label}
        </span>
      </div>

      {hasData && (
        <div style={styles.rangeRow} className="mono">
          <span>MIN {min.toFixed(3)}</span>
          <span>MAX {max.toFixed(3)}</span>
        </div>
      )}

      <div style={{ height: 100 }}>
        {series && series.length > 1 ? (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={series} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
              <CartesianGrid stroke="var(--color-border)" strokeDasharray="2 3" vertical={false} />
              <XAxis dataKey="t" tick={<Tick />} axisLine={{ stroke: 'var(--color-border)' }} tickLine={false} interval="preserveStartEnd" minTickGap={40} />
              <YAxis width={0} tick={false} axisLine={false} tickLine={false} domain={['auto', 'auto']} />
              <Tooltip content={<CustomTooltip unit={unit} />} />
              <Line type="monotone" dataKey="v" stroke="var(--color-chrome)" strokeWidth={1.5} dot={false} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div style={styles.waiting} className="label">Awaiting data…</div>
        )}
      </div>

      {rawSource && (
        <>
          <button style={styles.toggle} onClick={() => setShowWaveform((s) => !s)}>
            {showWaveform ? 'Hide raw waveform' : 'View raw waveform'}
          </button>
          {showWaveform && (
            <div style={{ height: 70, marginTop: 4 }}>
              {waveformData ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={waveformData} margin={{ top: 2, right: 4, bottom: 0, left: 4 }}>
                    <YAxis hide domain={['auto', 'auto']} />
                    <Line type="monotone" dataKey="v" stroke="var(--color-accent)" strokeWidth={1} dot={false} isAnimationActive={false} />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div style={styles.waiting} className="label">Loading latest window…</div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}

const styles = {
  card: {
    background: 'var(--color-panel)',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius)',
    padding: 'var(--space-3) var(--space-4)',
  },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 2 },
  readoutRow: { display: 'flex', alignItems: 'baseline', gap: 4, marginTop: 2 },
  readout: { fontSize: 20, fontWeight: 500, color: 'var(--color-ink)' },
  pill: {
    fontFamily: 'var(--font-display)',
    fontSize: 10,
    fontWeight: 600,
    letterSpacing: '0.06em',
    padding: '3px 7px',
    borderRadius: 'var(--radius)',
  },
  rangeRow: {
    display: 'flex',
    gap: 12,
    fontSize: 10,
    color: 'var(--color-ink-muted)',
    marginBottom: 4,
  },
  waiting: { height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' },
  toggle: {
    marginTop: 6,
    width: '100%',
    background: 'transparent',
    border: '1px solid var(--color-border)',
    color: 'var(--color-ink-muted)',
    fontFamily: 'var(--font-display)',
    fontSize: 10,
    letterSpacing: '0.05em',
    textTransform: 'uppercase',
    padding: '4px',
    cursor: 'pointer',
  },
};
