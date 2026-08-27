import { useState, useRef, useEffect } from 'react';
import type { KeyboardEvent } from 'react';
import { JarvisWebSocket } from '../services/websocket';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  isStreaming?: boolean;
}

export const JarvisChat = ({ ws }: { ws: JarvisWebSocket | null }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const [sessionId] = useState('sess-' + Math.random().toString(36).substring(2, 9));

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (!ws) return;
    
    const unsubscribe = ws.subscribe((data) => {
      if (data.type === 'ai_response_start') {
        setMessages((prev) => [
          ...prev, 
          { id: 'msg-' + Date.now(), role: 'assistant', content: '', isStreaming: true }
        ]);
      } else if (data.type === 'ai_response_delta') {
        setMessages((prev) => {
          const newMessages = [...prev];
          const lastMsg = newMessages[newMessages.length - 1];
          if (lastMsg && lastMsg.role === 'assistant' && lastMsg.isStreaming) {
            lastMsg.content += data.delta;
          }
          return newMessages;
        });
      } else if (data.type === 'ai_response_complete') {
        setMessages((prev) => {
          const newMessages = [...prev];
          const lastMsg = newMessages[newMessages.length - 1];
          if (lastMsg && lastMsg.role === 'assistant' && lastMsg.isStreaming) {
            lastMsg.isStreaming = false;
          }
          return newMessages;
        });
      } else if (data.type === 'ai_response_error') {
        setMessages((prev) => [
          ...prev, 
          { id: 'err-' + Date.now(), role: 'assistant', content: `[ERROR] ${data.error}`, isStreaming: false }
        ]);
      }
    });
    
    return () => unsubscribe();
  }, [ws]);

  const handleSend = () => {
    if (!input.trim() || !ws) return;
    
    const newMsg: ChatMessage = {
      id: 'msg-' + Date.now(),
      role: 'user',
      content: input
    };
    
    setMessages(prev => [...prev, newMsg]);
    ws.send({
      type: 'chat_message',
      session_id: sessionId,
      message: input
    });
    setInput('');
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', border: '1px solid #333', marginLeft: '1rem', height: '80vh' }}>
      <div style={{ flex: 1, overflowY: 'auto', padding: '1rem' }}>
        {messages.map((m) => (
          <div key={m.id} style={{
            marginBottom: '1rem',
            textAlign: m.role === 'user' ? 'right' : 'left'
          }}>
            <div style={{
              display: 'inline-block',
              padding: '0.8rem',
              borderRadius: '8px',
              backgroundColor: m.role === 'user' ? '#113333' : '#1a1a1a',
              border: m.role === 'user' ? '1px solid #00ffcc' : '1px solid #555',
              maxWidth: '80%',
              whiteSpace: 'pre-wrap',
              color: m.role === 'user' ? '#fff' : (m.isStreaming ? '#00ffcc' : '#ccc')
            }}>
              {m.content}
              {m.isStreaming && <span style={{ opacity: 0.5 }}> █</span>}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      <div style={{ padding: '1rem', borderTop: '1px solid #333', display: 'flex' }}>
        <textarea 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask J.A.R.V.I.S... (Enter to send, Shift+Enter for newline)"
          style={{ flex: 1, backgroundColor: '#0a0a0a', color: '#00ffcc', border: '1px solid #555', padding: '0.5rem', fontFamily: 'monospace', resize: 'none', height: '60px' }}
        />
        <button 
          onClick={handleSend}
          style={{ marginLeft: '1rem', backgroundColor: '#00ffcc', color: '#000', border: 'none', padding: '0 1.5rem', fontWeight: 'bold', cursor: 'pointer' }}
        >
          SEND
        </button>
      </div>
    </div>
  );
};
