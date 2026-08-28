import { useState } from 'react';
import { useAuth } from '../lib/AuthContext';

export function LoginScreen() {
  const { login } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await login(username, password);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div style={styles.wrap}>
      <div style={styles.panel}>
        <div style={styles.badge}>SW</div>
        <h1 style={styles.title}>SmartWatch Manager</h1>
        <p className="label" style={{ marginBottom: 24 }}>Operator sign-in</p>

        <form onSubmit={handleSubmit}>
          <label className="label" htmlFor="username">Username</label>
          <input
            id="username"
            style={styles.input}
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoFocus
            required
          />

          <label className="label" htmlFor="password" style={{ marginTop: 16, display: 'block' }}>
            Password
          </label>
          <input
            id="password"
            type="password"
            style={styles.input}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          {error && <div style={styles.error}>{error}</div>}

          <button type="submit" style={styles.button} disabled={submitting}>
            {submitting ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
      </div>
    </div>
  );
}

const styles = {
  wrap: {
    height: '100%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'var(--color-surface)',
  },
  panel: {
    width: 340,
    background: 'var(--color-panel)',
    border: '1px solid var(--color-border)',
    boxShadow: 'var(--bezel-shadow)',
    padding: 'var(--space-6)',
  },
  badge: {
    width: 40,
    height: 40,
    background: 'var(--color-chrome)',
    color: 'var(--color-accent)',
    fontFamily: 'var(--font-mono)',
    fontWeight: 600,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  title: { fontSize: 20, marginBottom: 4 },
  input: {
    width: '100%',
    padding: '8px 10px',
    marginTop: 6,
    border: '1px solid var(--color-border-strong)',
    borderRadius: 'var(--radius)',
    fontFamily: 'var(--font-body)',
    fontSize: 14,
    background: '#fff',
    color: 'var(--color-ink)',
  },
  button: {
    width: '100%',
    marginTop: 24,
    padding: '10px',
    background: 'var(--color-chrome)',
    color: '#fff',
    border: 'none',
    borderRadius: 'var(--radius)',
    fontFamily: 'var(--font-display)',
    fontWeight: 600,
    letterSpacing: '0.04em',
    textTransform: 'uppercase',
    fontSize: 13,
    cursor: 'pointer',
  },
  error: {
    marginTop: 12,
    padding: '8px 10px',
    background: 'var(--status-fault-bg)',
    color: 'var(--status-fault)',
    fontSize: 13,
    borderLeft: '3px solid var(--status-fault)',
  },
};
