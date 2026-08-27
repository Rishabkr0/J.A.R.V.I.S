
import { useEffect, useState } from 'react';
import { JarvisWebSocket } from '../services/websocket';
import { getHealth } from '../services/api';

export const JarvisStatus = ({ externalWs }: { externalWs?: JarvisWebSocket | null }) => {
  const [jarvisState, setJarvisState] = useState<string>('UNKNOWN');
  const [wsConnected, setWsConnected] = useState(false);
  const [apiHealth, setApiHealth] = useState<any>(null);
  const [events, setEvents] = useState<any[]>([]);

  useEffect(() => {
    getHealth().then(setApiHealth).catch(() => setApiHealth({ status: 'error' }));
  }, []);

  useEffect(() => {
    const ws = externalWs || new JarvisWebSocket(setWsConnected);
    
    if (!externalWs) {
      ws.connect();
    } else {
      setWsConnected(true);
    }

    const unsubscribe = ws.subscribe((data) => {
      if (data.type === 'state_changed') {
        setJarvisState(data.state);
      }
      setEvents((prev) => [...prev.slice(-4), data]); // keep last 5
    });

    return () => unsubscribe();
  }, [externalWs]);

  return (
    <div style={{ fontFamily: 'monospace', padding: '2rem', color: '#00ffcc', backgroundColor: '#0a0a0a', minHeight: '100vh' }}>
      <h1>J.A.R.V.I.S. Core Interface</h1>
      
      <div style={{ border: '1px solid #333', padding: '1rem', marginBottom: '1rem' }}>
        <h3>System Status</h3>
        <p>Backend API: {apiHealth?.status === 'ok' ? '✅ ONLINE' : '❌ OFFLINE'} (v{apiHealth?.version})</p>
        <p>WebSocket: {wsConnected ? '✅ CONNECTED' : '❌ DISCONNECTED'}</p>
      </div>

      <div style={{ border: '1px solid #333', padding: '1rem', marginBottom: '1rem' }}>
        <h3>Current State</h3>
        <h2 style={{ color: jarvisState === 'ERROR' ? '#ff3333' : '#00ffcc' }}>{jarvisState}</h2>
      </div>

      <div style={{ border: '1px solid #333', padding: '1rem' }}>
        <h3>Event Log</h3>
        {events.map((e, i) => (
          <div key={i} style={{ padding: '0.5rem', borderBottom: '1px solid #222' }}>
            [{new Date().toLocaleTimeString()}] {JSON.stringify(e)}
          </div>
        ))}
      </div>
    </div>
  );
};
