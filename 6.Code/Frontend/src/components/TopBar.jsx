import { useEffect, useState } from 'react';
import { useAuth } from '../lib/AuthContext';

export function TopBar({ connected }) {
  const { logout } = useAuth();
  const [now, setNow] = useState(new Date());

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <header style={styles.bar}>
      <div style={styles.left}>
        <div style={styles.badge}>SW</div>
        <div>
          <div style={styles.title}>SmartWatch Manager</div>
          <div className="label" style={{ color: '#B7BEC7' }}>Motor Condition Monitoring</div>
        </div>
      </div>

      <div style={styles.right}>
        <div style={styles.statusGroup}>
          <span style={{ ...styles.dot, background: connected ? 'var(--status-ok)' : 'var(--status-fault)' }} />
          <span className="label" style={{ color: '#B7BEC7' }}>
            {connected ? 'LINK OK' : 'LINK LOST'}
          </span>
        </div>
        <div className="mono" style={styles.clock}>
          {now.toLocaleTimeString('en-GB')}
        </div>
        <button onClick={logout} style={styles.logout}>Sign out</button>
      </div>
    </header>
  );
}

const styles = {
  bar: {
    height: 56,
    background: 'var(--color-chrome)',
    color: '#fff',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '0 var(--space-5)',
    borderBottom: '3px solid var(--color-accent)',
  },
  left: { display: 'flex', alignItems: 'center', gap: 12 },
  badge: {
    width: 32,
    height: 32,
    background: 'var(--color-chrome-dark)',
    color: 'var(--color-accent)',
    fontFamily: 'var(--font-mono)',
    fontWeight: 600,
    fontSize: 13,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: { fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: 16, letterSpacing: '0.02em' },
  right: { display: 'flex', alignItems: 'center', gap: 24 },
  statusGroup: { display: 'flex', alignItems: 'center', gap: 8 },
  dot: { width: 8, height: 8, borderRadius: '50%', display: 'inline-block' },
  clock: { fontSize: 14, color: '#D7DBE0', minWidth: 76, textAlign: 'right' },
  logout: {
    background: 'transparent',
    border: '1px solid #5B6470',
    color: '#D7DBE0',
    padding: '6px 12px',
    fontFamily: 'var(--font-display)',
    fontSize: 12,
    letterSpacing: '0.04em',
    textTransform: 'uppercase',
    cursor: 'pointer',
  },
};
