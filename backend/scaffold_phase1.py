import os
import pathlib

base = pathlib.Path(r'c:\Users\Rishab\Documents\J.A.R.V.I.S\backend')

files = {
    'app/core/config.py': '''from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = 'JARVIS'
    ENVIRONMENT: str = 'development'
    HOST: str = '0.0.0.0'
    PORT: int = 8000
    LOG_LEVEL: str = 'INFO'
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = 'gemini-2.5-flash'
    MAX_CONVERSATION_MESSAGES: int = 20

    class Config:
        env_file = '.env'

settings = Settings()
''',
    '.env.example': '''# JARVIS Environment Configuration
PORT=8000
HOST=0.0.0.0
LOG_LEVEL=INFO
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
MAX_CONVERSATION_MESSAGES=20
''',
    'app/providers/gemini.py': '''from typing import Any, AsyncGenerator
import logging
from app.providers.base import AIProvider
from app.core.config import settings

logger = logging.getLogger('jarvis.gemini')

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

JARVIS_SYSTEM_PROMPT = """You are J.A.R.V.I.S., a highly capable, concise, and professional personal AI assistant.
Keep your responses intelligent, calm, and slightly futuristic.
Do not be excessively verbose.
Do not pretend to have capabilities you do not currently possess (e.g., if you cannot execute OS commands yet, clearly state so).
"""

class GeminiProvider(AIProvider):
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        if self.api_key and genai:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    async def generate(self, prompt: str) -> str:
        if not self.client:
            raise ValueError('Gemini API key not configured or google-genai not installed.')
        
        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=JARVIS_SYSTEM_PROMPT,
            )
        )
        return response.text

    async def stream(self, prompt: str, history: list = None) -> AsyncGenerator[str, None]:
        if not self.client:
            raise ValueError('Gemini API key not configured.')
        
        # Format history for google-genai
        contents = []
        if history:
            for msg in history:
                role = 'user' if msg['role'] == 'user' else 'model'
                contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg['content'])]))
        
        contents.append(types.Content(role='user', parts=[types.Part.from_text(text=prompt)]))

        try:
            response_stream = await self.client.aio.models.generate_content_stream(
                model=self.model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=JARVIS_SYSTEM_PROMPT,
                )
            )
            async for chunk in response_stream:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.error(f'Gemini stream error: {e}')
            raise
''',
    'app/memory/__init__.py': '',
    'app/memory/session.py': '''import uuid
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
''',
    'app/orchestrator/router.py': '''import logging
import time
from typing import AsyncGenerator
from app.providers.base import AIProvider
from app.providers.gemini import GeminiProvider

logger = logging.getLogger('jarvis.router')

class BrainRouter:
    def __init__(self):
        self.gemini_provider = GeminiProvider()

    def select_provider(self) -> AIProvider:
        return self.gemini_provider

    async def stream_response(self, prompt: str, history: list = None) -> AsyncGenerator[dict, None]:
        provider = self.select_provider()
        
        start_time = time.time()
        logger.info('Provider routing started.')
        
        try:
            stream = provider.stream(prompt, history)
            first_token_received = False
            
            async for chunk in stream:
                if not first_token_received:
                    first_token_received = True
                    time_to_first_token = time.time() - start_time
                    logger.info(f'First token received in {time_to_first_token:.3f}s')
                yield {'chunk': chunk}
                
            total_time = time.time() - start_time
            logger.info(f'Generation completed in {total_time:.3f}s')
            
        except Exception as e:
            logger.error(f'Provider error: {e}')
            yield {'error': str(e)}
''',
    'app/orchestrator/core.py': '''import asyncio
import logging
from app.events.bus import EventBus
from app.events.models import JarvisEvent, JarvisState
from app.orchestrator.router import BrainRouter
from app.memory.session import SessionManager

logger = logging.getLogger('jarvis.orchestrator')

class Orchestrator:
    def __init__(self):
        self.bus = EventBus()
        self.router = BrainRouter()
        self.state = JarvisState.IDLE

    def set_state(self, new_state: JarvisState, data: dict = None):
        self.state = new_state
        event = JarvisEvent(type='state_changed', state=self.state, data=data or {})
        self.bus.publish(event.model_dump())

    async def handle_chat_message(self, session_id: str, message: str):
        session = SessionManager.get_or_create(session_id)
        
        self.set_state(JarvisState.THINKING)
        
        self.bus.publish({
            'type': 'ai_response_start',
            'session_id': session.session_id
        })

        full_response = []
        try:
            async for data in self.router.stream_response(message, session.history):
                if 'error' in data:
                    raise Exception(data['error'])
                
                chunk = data['chunk']
                full_response.append(chunk)
                self.bus.publish({
                    'type': 'ai_response_delta',
                    'session_id': session.session_id,
                    'delta': chunk
                })
                
            completed_text = ''.join(full_response)
            session.add_user_message(message)
            session.add_assistant_message(completed_text)
            
            self.bus.publish({
                'type': 'ai_response_complete',
                'session_id': session.session_id,
                'message': completed_text
            })
            self.set_state(JarvisState.IDLE)
            
        except Exception as e:
            logger.error(f'Failed to process chat: {e}')
            self.set_state(JarvisState.ERROR, {'detail': str(e)})
            self.bus.publish({
                'type': 'ai_response_error',
                'session_id': session.session_id,
                'error': str(e)
            })
            await asyncio.sleep(2)
            self.set_state(JarvisState.IDLE)
''',
    'app/api/ws.py': '''from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import logging
import asyncio
from app.events.bus import EventBus
from app.orchestrator.core import Orchestrator

logger = logging.getLogger('jarvis.ws')
router = APIRouter()
bus = EventBus()
orchestrator = Orchestrator()

@router.websocket('/ws/jarvis')
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    await websocket.send_json({
        'type': 'state_changed',
        'state': orchestrator.state,
        'data': {}
    })
    
    async def event_handler(event):
        try:
            await websocket.send_json(event)
        except Exception as e:
            logger.error(f'WS send error: {e}')

    bus.subscribe(event_handler)
    session_id = None
    
    try:
        while True:
            data_str = await websocket.receive_text()
            try:
                data = json.loads(data_str)
                if data.get('type') == 'chat_message':
                    session_id = data.get('session_id')
                    message = data.get('message')
                    if message:
                        asyncio.create_task(orchestrator.handle_chat_message(session_id, message))
            except json.JSONDecodeError:
                logger.error('Invalid JSON received')
    except WebSocketDisconnect:
        logger.info('Client disconnected')
        bus.unsubscribe(event_handler)
'''
}

for rel_path, content in files.items():
    p = base / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(content)

print('Backend Phase 1 scaffolded successfully.')
