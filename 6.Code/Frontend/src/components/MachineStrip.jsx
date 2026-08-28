import { deriveMachineStatus } from '../lib/useTelemetry';

const STATUS_META = {
  ok: { label: 'RUNNING', color: 'var(--status-ok)', bg: 'var(--status-ok-bg)' },
  offline: { label: 'OFFLINE', color: 'var(--status-offline)', bg: 'var(--status-offline-bg)' },
};

export function MachineStrip({ machines, selectedId, onSelect }) {
  if (!machines || machines.length === 0) {
    return (
      <div style={styles.empty}>
        <span className="label">No machines reporting yet</span>
      </div>
    );
  }

  return (
    <div style={styles.strip}>
      {machines.map((m) => {
        const status = deriveMachineStatus(m.last_seen);
        const meta = STATUS_META[status];
        const selected = m.machine_id === selectedId;
        return (
          <button
            key={m.machine_id}
            onClick={() => onSelect(m.machine_id)}
            style={{
              ...styles.tile,
              borderColor: selected ? 'var(--color-accent)' : 'var(--color-border)',
              boxShadow: selected ? '0 0 0 2px var(--color-accent) inset' : 'var(--bezel-shadow)',
            }}
          >
            <div style={styles.tileTop}>
              <span style={{ ...styles.led, background: meta.color }} />
              <span className="label" style={{ color: meta.color }}>{meta.label}</span>
            </div>
            <div style={styles.tileId} className="mono">{m.machine_id}</div>
            <div style={styles.tileMeta}>
              <span className="label">WINDOWS</span>
              <span className="mono" style={styles.tileMetaValue}>{m.window_count ?? '—'}</span>
            </div>
          </button>
        );
      })}
    </div>
  );
}

const styles = {
  strip: {
    display: 'flex',
    gap: 'var(--space-3)',
    padding: 'var(--space-4) var(--space-5)',
    overflowX: 'auto',
    background: 'var(--color-surface)',
  },
  empty: {
    padding: 'var(--space-5)',
    textAlign: 'center',
  },
  tile: {
    minWidth: 168,
    background: 'var(--color-panel)',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius)',
    padding: 'var(--space-3) var(--space-4)',
    textAlign: 'left',
    cursor: 'pointer',
    flexShrink: 0,
  },
  tileTop: { display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 },
  led: { width: 8, height: 8, borderRadius: '50%', display: 'inline-block' },
  tileId: { fontSize: 15, fontWeight: 600, marginBottom: 10, color: 'var(--color-ink)' },
  tileMeta: { display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' },
  tileMetaValue: { fontSize: 13, color: 'var(--color-ink-muted)' },
};
