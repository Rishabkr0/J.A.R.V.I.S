
import { useState, useEffect } from 'react';
import { JarvisStatus } from './components/JarvisStatus';
import { JarvisChat } from './components/JarvisChat';
import { JarvisWebSocket } from './services/websocket';

function App() {
  const [ws, setWs] = useState<JarvisWebSocket | null>(null);

  useEffect(() => {
    const socket = new JarvisWebSocket(() => {});
    socket.connect();
    setWs(socket);
    
    // Quick cleanup
    return () => {
       // Ideally close socket if needed
    };
  }, []);

  return (
    <div style={{ display: 'flex', backgroundColor: '#000', color: '#fff', minHeight: '100vh' }}>
      <div style={{ width: '300px' }}>
        <JarvisStatus externalWs={ws} />
      </div>
      <div style={{ flex: 1, padding: '1rem' }}>
        <JarvisChat ws={ws} />
      </div>
    </div>
  );
}

export default App;
