import { useCurrentSummary, useVibrationSummary } from '../lib/useTelemetry';
import { GaugeCard } from './GaugeCard';

const CURRENT_CHANNELS = [
  { key: 'ia_rms', label: 'PHASE A', rawField: 'Ia', unit: 'A rms' },
  { key: 'ib_rms', label: 'PHASE B', rawField: 'Ib', unit: 'A rms' },
  { key: 'ic_rms', label: 'PHASE C', rawField: 'Ic', unit: 'A rms' },
];

const VIBRATION_CHANNELS = [
  { key: 'vib_axial_rms', label: 'AXIAL', rawField: 'Vib_axial', unit: 'g rms' },
  { key: 'vib_base_rms', label: 'BASE', rawField: 'Vib_base', unit: 'g rms' },
  { key: 'vib_carc_rms', label: 'CARCASS', rawField: 'Vib_carc', unit: 'g rms' },
  { key: 'vib_acpe_rms', label: 'BEARING (EXT)', rawField: 'Vib_acpe', unit: 'g rms' },
  { key: 'vib_acpi_rms', label: 'BEARING (INT)', rawField: 'Vib_acpi', unit: 'g rms' },
];

function toSeries(rows, key) {
  if (!rows) return [];
  // API returns newest-first; reverse so charts read left-to-right in time.
  return [...rows].reverse().map((r) => ({ t: r.time, v: r[key] }));
}

export function MachineDetail({ machineId }) {
  const { data: currentRows, error: currentError } = useCurrentSummary(machineId);
  const { data: vibrationRows, error: vibrationError } = useVibrationSummary(machineId);

  if (!machineId) {
    return (
      <div style={styles.placeholder}>
        <span className="label">Select a machine above to view telemetry</span>
      </div>
    );
  }

  return (
    <div style={styles.wrap}>
      <Section title="Motor Current Signature" error={currentError}>
        <div style={styles.grid}>
          {CURRENT_CHANNELS.map((ch) => (
            <GaugeCard
              key={ch.key}
              label={ch.label}
              unit={ch.unit}
              series={toSeries(currentRows, ch.key)}
              machineId={machineId}
              rawSource={{ table: 'current', field: ch.rawField }}
            />
          ))}
        </div>
      </Section>

      <Section title="Vibration" error={vibrationError}>
        <div style={styles.grid}>
          {VIBRATION_CHANNELS.map((ch) => (
            <GaugeCard
              key={ch.key}
              label={ch.label}
              unit={ch.unit}
              series={toSeries(vibrationRows, ch.key)}
              machineId={machineId}
              rawSource={{ table: 'vibration', field: ch.rawField }}
            />
          ))}
        </div>
      </Section>
    </div>
  );
}

function Section({ title, error, children }) {
  return (
    <div style={styles.section}>
      <h2 style={styles.sectionTitle}>{title}</h2>
      {error && <div style={styles.error}>{error}</div>}
      {children}
    </div>
  );
}

const styles = {
  wrap: { padding: '0 var(--space-5) var(--space-6)' },
  placeholder: {
    padding: 'var(--space-7)',
    textAlign: 'center',
  },
  section: { marginBottom: 'var(--space-5)' },
  sectionTitle: { fontSize: 15, marginBottom: 'var(--space-3)', color: 'var(--color-ink)' },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
    gap: 'var(--space-3)',
  },
  error: {
    marginBottom: 'var(--space-3)',
    padding: '6px 10px',
    background: 'var(--status-fault-bg)',
    color: 'var(--status-fault)',
    fontSize: 13,
    borderLeft: '3px solid var(--status-fault)',
  },
};
