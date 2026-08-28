import { useState } from 'react';
import { AuthProvider, useAuth } from './lib/AuthContext';
import { useMachines } from './lib/useTelemetry';
import { LoginScreen } from './components/LoginScreen';
import { TopBar } from './components/TopBar';
import { MachineStrip } from './components/MachineStrip';
import { MachineDetail } from './components/MachineDetail';
import './theme.css';

function Dashboard() {
  const { data: machines, error } = useMachines();
  const [selectedId, setSelectedId] = useState(null);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <TopBar connected={!error} />
      <MachineStrip machines={machines} selectedId={selectedId} onSelect={setSelectedId} />
      <div style={{ flex: 1, overflowY: 'auto' }}>
        <MachineDetail machineId={selectedId} />
      </div>
    </div>
  );
}

function Shell() {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <Dashboard /> : <LoginScreen />;
}

export default function App() {
  return (
    <AuthProvider>
      <Shell />
    </AuthProvider>
  );
}
