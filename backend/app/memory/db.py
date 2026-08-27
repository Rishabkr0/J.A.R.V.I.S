import sqlite3
import uuid
import time
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

logger = logging.getLogger("jarvis.memory.db")

class MemoryItem(BaseModel):
    id: str
    type: str
    key: str
    value: str
    confidence: float
    importance: float
    source: str
    created_at: float
    updated_at: float
    last_accessed_at: float
    access_count: int
    enabled: bool

class MemoryDatabase:
    def __init__(self, db_path: str = "data/jarvis_memory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    confidence REAL DEFAULT 1.0,
                    importance REAL DEFAULT 0.5,
                    source TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    last_accessed_at REAL NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    enabled INTEGER DEFAULT 1
                )
            """)
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_key ON memories(key)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type)")

    def _is_sensitive(self, text: str) -> bool:
        """Filters out obvious credentials from being stored in memory."""
        patterns = [
            r"sk-[a-zA-Z0-9]{30,}",         # API Keys (OpenAI/Anthropic/Gemini)
            r"password is",
            r"(?i)api_key",
            r"(?i)api key",
            r"(?i)secret",
            r"Bearer [a-zA-Z0-9\-\._~+/]+=", # JWT tokens
        ]
        for p in patterns:
            if re.search(p, text):
                return True
        return False

    def create_memory(self, type: str, key: str, value: str, source: str = "explicit", 
                      confidence: float = 1.0, importance: float = 0.5) -> Optional[MemoryItem]:
        
        if self._is_sensitive(value) or self._is_sensitive(key):
            logger.warning("Attempted to store sensitive information. Rejected.")
            return None

        # Deduplication/Update
        existing = self.get_memory_by_key(key)
        if existing:
            return self.update_memory(existing.id, value=value, confidence=confidence, source=source)

        mem_id = str(uuid.uuid4())
        now = time.time()
        
        with self.conn:
            self.conn.execute("""
                INSERT INTO memories 
                (id, type, key, value, confidence, importance, source, created_at, updated_at, last_accessed_at, access_count, enabled)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (mem_id, type, key, value, confidence, importance, source, now, now, now, 0, 1))
            
        logger.info(f"Created memory: {key} = {value}")
        return self.get_memory(mem_id)

    def get_memory(self, mem_id: str) -> Optional[MemoryItem]:
        cursor = self.conn.execute("SELECT * FROM memories WHERE id = ?", (mem_id,))
        row = cursor.fetchone()
        if row:
            return MemoryItem(**dict(row))
        return None

    def get_memory_by_key(self, key: str) -> Optional[MemoryItem]:
        cursor = self.conn.execute("SELECT * FROM memories WHERE key = ?", (key,))
        row = cursor.fetchone()
        if row:
            return MemoryItem(**dict(row))
        return None

    def update_memory(self, mem_id: str, value: str = None, confidence: float = None, source: str = None) -> Optional[MemoryItem]:
        updates = []
        params = []
        if value is not None:
            if self._is_sensitive(value):
                return None
            updates.append("value = ?")
            params.append(value)
        if confidence is not None:
            updates.append("confidence = ?")
            params.append(confidence)
        if source is not None:
            updates.append("source = ?")
            params.append(source)
            
        if not updates:
            return self.get_memory(mem_id)
            
        updates.append("updated_at = ?")
        params.append(time.time())
        params.append(mem_id)
        
        query = f"UPDATE memories SET {', '.join(updates)} WHERE id = ?"
        with self.conn:
            self.conn.execute(query, tuple(params))
            
        return self.get_memory(mem_id)

    def mark_accessed(self, mem_id: str):
        with self.conn:
            self.conn.execute("UPDATE memories SET last_accessed_at = ?, access_count = access_count + 1 WHERE id = ?", 
                              (time.time(), mem_id))

    def delete_memory(self, mem_id: str) -> bool:
        with self.conn:
            cursor = self.conn.execute("DELETE FROM memories WHERE id = ?", (mem_id,))
            return cursor.rowcount > 0

    def clear_all(self):
        with self.conn:
            self.conn.execute("DELETE FROM memories")
            
    def list_memories(self, limit: int = 50, offset: int = 0) -> List[MemoryItem]:
        cursor = self.conn.execute("SELECT * FROM memories ORDER BY updated_at DESC LIMIT ? OFFSET ?", (limit, offset))
        return [MemoryItem(**dict(row)) for row in cursor.fetchall()]

    def search_memories(self, query: str, limit: int = 5) -> List[MemoryItem]:
        """Lightweight parameterized search, ranked by recency + importance."""
        if not query.strip():
            return []
            
        # Basic keyword match
        keywords = query.lower().split()
        if not keywords: return []
        
        # Build parameterized LIKE query
        conditions = []
        params = []
        for kw in keywords:
            if len(kw) < 3: continue # Skip tiny words like "is", "my"
            conditions.append("(key LIKE ? OR value LIKE ?)")
            params.extend([f"%{kw}%", f"%{kw}%"])
            
        if not conditions:
            # Fallback if query only had small words
            conditions.append("(key LIKE ? OR value LIKE ?)")
            params.extend([f"%{query}%", f"%{query}%"])

        where_clause = " OR ".join(conditions)
        
        # Score = (importance * 10) + (1 / (now - updated_at)) - sort is complex in raw SQL, 
        # so we'll fetch matches and sort in python since dataset is small.
        sql = f"SELECT * FROM memories WHERE {where_clause}"
        cursor = self.conn.execute(sql, tuple(params))
        rows = cursor.fetchall()
        
        results = [MemoryItem(**dict(row)) for row in rows]
        
        now = time.time()
        def score(m: MemoryItem):
            age_days = max(0.1, (now - m.updated_at) / 86400)
            return (m.importance * 10) + (1.0 / age_days) + (m.confidence * 5)
            
        results.sort(key=score, reverse=True)
        
        for m in results[:limit]:
            self.mark_accessed(m.id)
            
        return results[:limit]

# Global instance for app lifecycle
memory_db = MemoryDatabase()
