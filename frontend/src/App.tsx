import { useState, useEffect } from 'react';
import { JarvisChat } from './components/JarvisChat';
import { MemoryManager } from './components/MemoryManager';
import { JarvisWebSocket } from './services/websocket';

function App() {
  const [ws, setWs] = useState<JarvisWebSocket | null>(null);
  const [activeTab, setActiveTab] = useState<'chat' | 'memory'>('chat');
  const [browserStatus, setBrowserStatus] = useState<string>('OFFLINE');

  useEffect(() => {
    const socket = new JarvisWebSocket(() => {});
    const unsubscribe = socket.subscribe((data) => {
      if (data.type === 'browser_status') {
        setBrowserStatus(data.status);
      }
    });
    socket.connect();
    setWs(socket);

    return () => {
      unsubscribe();
      socket.disconnect();
    };
  }, []);

  return (
    <div style={{ display: 'flex', height: '100vh', backgroundColor: '#000', color: '#fff', fontFamily: 'sans-serif' }}>
      <div style={{ width: '250px', borderRight: '1px solid #333', padding: '1rem', display: 'flex', flexDirection: 'column' }}>
        <h1 style={{ color: '#00ffcc', margin: '0 0 2rem 0', fontSize: '1.5rem', letterSpacing: '2px' }}>
          J.A.R.V.I.S.
        </h1>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <button 
            onClick={() => setActiveTab('chat')}
            style={{ textAlign: 'left', padding: '0.8rem', backgroundColor: activeTab === 'chat' ? '#113333' : 'transparent', color: activeTab === 'chat' ? '#00ffcc' : '#888', border: 'none', borderLeft: activeTab === 'chat' ? '3px solid #00ffcc' : '3px solid transparent', cursor: 'pointer', fontWeight: 'bold' }}
          >
            CHAT & VOICE
          </button>
          <button 
            onClick={() => setActiveTab('memory')}
            style={{ textAlign: 'left', padding: '0.8rem', backgroundColor: activeTab === 'memory' ? '#113333' : 'transparent', color: activeTab === 'memory' ? '#00ffcc' : '#888', border: 'none', borderLeft: activeTab === 'memory' ? '3px solid #00ffcc' : '3px solid transparent', cursor: 'pointer', fontWeight: 'bold' }}
          >
            MEMORY
          </button>
          <div style={{ padding: '0.8rem', color: '#555', cursor: 'not-allowed' }}>SETTINGS</div>
        </div>
        <div style={{ color: '#444', fontSize: '0.8rem' }}>
          System: Online<br/>
          Core: Operational<br/>
          <span style={{ color: browserStatus === 'OFFLINE' ? '#ff3333' : (browserStatus === 'ERROR' ? '#ffaa00' : '#00ffcc') }}>
            Browser: {browserStatus}
          </span>
        </div>
      </div>
      
      <div style={{ flex: 1, display: 'flex' }}>
        {activeTab === 'chat' ? (
          <JarvisChat ws={ws} />
        ) : (
          <MemoryManager />
        )}
      </div>
    </div>
  );
}

export default App;
