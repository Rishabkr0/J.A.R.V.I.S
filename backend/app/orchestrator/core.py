import asyncio
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
