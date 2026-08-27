import uuid
import logging
from typing import List, Dict, Any
from app.core.config import settings

logger = logging.getLogger('jarvis.session')

class ConversationSession:
    def __init__(self, session_id: str = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.history: List[Dict[str, str]] = []

    def add_user_message(self, content: str):
        self.history.append({'role': 'user', 'content': content})
        self._trim_history()

    def add_assistant_message(self, content: str):
        self.history.append({'role': 'assistant', 'content': content})
        self._trim_history()

    def _trim_history(self):
        if len(self.history) > settings.MAX_CONVERSATION_MESSAGES:
            self.history = self.history[-settings.MAX_CONVERSATION_MESSAGES:]

class SessionManager:
    _sessions: Dict[str, ConversationSession] = {}

    @classmethod
    def get_or_create(cls, session_id: str = None) -> ConversationSession:
        if not session_id or session_id not in cls._sessions:
            session = ConversationSession(session_id)
            cls._sessions[session.session_id] = session
            return session
        return cls._sessions[session_id]
