import { useState, useEffect } from 'react';

interface MemoryItem {
  id: string;
  type: string;
  key: string;
  value: string;
  confidence: number;
  importance: number;
  source: string;
  created_at: number;
  updated_at: number;
  last_accessed_at: number;
  access_count: number;
}

export const MemoryManager = () => {
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchMemories = async () => {
    setLoading(true);
    try {
      const url = search 
        ? `http://localhost:8000/api/memories/search?q=${encodeURIComponent(search)}`
        : `http://localhost:8000/api/memories`;
      const res = await fetch(url);
      const data = await res.json();
      setMemories(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMemories();
  }, [search]);

  const handleDelete = async (id: string) => {
    try {
      await fetch(`http://localhost:8000/api/memories/${id}`, { method: 'DELETE' });
      fetchMemories();
    } catch (e) {
      console.error(e);
    }
  };

  const handleClearAll = async () => {
    if (window.confirm("Are you sure you want to permanently delete ALL persistent memories? This cannot be undone.")) {
      try {
        await fetch(`http://localhost:8000/api/memories`, { method: 'DELETE' });
        fetchMemories();
      } catch (e) {
        console.error(e);
      }
    }
  };

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '1rem', color: '#fff' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
        <h2>Persistent Memory</h2>
        <button 
          onClick={handleClearAll}
          style={{ backgroundColor: '#ff3333', color: '#000', fontWeight: 'bold', padding: '0.5rem 1rem', border: 'none', cursor: 'pointer' }}
        >
          CLEAR ALL
        </button>
      </div>
      
      <div style={{ marginBottom: '1rem' }}>
        <input 
          type="text" 
          placeholder="Search memories..." 
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ width: '100%', padding: '0.5rem', backgroundColor: '#1a1a1a', color: '#00ffcc', border: '1px solid #555' }}
        />
      </div>

      <div style={{ flex: 1, overflowY: 'auto' }}>
        {loading ? (
          <p>Loading...</p>
        ) : memories.length === 0 ? (
          <p>No memories found.</p>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #555' }}>
                <th style={{ padding: '0.5rem' }}>Key</th>
                <th style={{ padding: '0.5rem' }}>Value</th>
                <th style={{ padding: '0.5rem' }}>Type</th>
                <th style={{ padding: '0.5rem' }}>Source</th>
                <th style={{ padding: '0.5rem' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {memories.map(m => (
                <tr key={m.id} style={{ borderBottom: '1px solid #333' }}>
                  <td style={{ padding: '0.5rem', fontWeight: 'bold', color: '#00ffcc' }}>{m.key.replace(/_/g, ' ')}</td>
                  <td style={{ padding: '0.5rem' }}>{m.value}</td>
                  <td style={{ padding: '0.5rem', fontSize: '0.8rem', color: '#888' }}>{m.type}</td>
                  <td style={{ padding: '0.5rem', fontSize: '0.8rem', color: '#888' }}>{m.source}</td>
                  <td style={{ padding: '0.5rem' }}>
                    <button 
                      onClick={() => handleDelete(m.id)}
                      style={{ backgroundColor: 'transparent', color: '#ff3333', border: '1px solid #ff3333', padding: '0.2rem 0.5rem', cursor: 'pointer' }}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
