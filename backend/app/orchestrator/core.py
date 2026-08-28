import asyncio
import logging
import time
from app.events.bus import EventBus
from app.events.models import JarvisEvent, JarvisState
from app.orchestrator.router import BrainRouter
from app.orchestrator.fast_router import FastRouter
from app.memory.session import SessionManager
from app.memory.retriever import MemoryRetriever
from app.tools.registry import ToolRegistry
# Ensure tools are imported so they register
import app.tools.impl.windows_apps
import app.tools.impl.windows_gui
import app.tools.impl.windows_url
import app.tools.impl.windows_volume
import app.tools.impl.windows_sysinfo
import app.tools.impl.fs_tools
import app.tools.impl.memory_tools
import app.tools.impl.browser_tools

from app.voice.tts import TTS

logger = logging.getLogger('jarvis.orchestrator')

class Orchestrator:
    def __init__(self):
        self.bus = EventBus()
        self.router = BrainRouter()
        self.fast_router = FastRouter()
        self.tts = TTS()
        self.state = JarvisState.IDLE

    def set_state(self, new_state: JarvisState, data: dict = None):
        self.state = new_state
        event = JarvisEvent(type='state_changed', state=self.state, data=data or {})
        self.bus.publish(event.model_dump())

    def cancel_execution(self):
        logger.info("Cancelling current execution upon user request...")
        if hasattr(self, 'current_task') and self.current_task and not self.current_task.done():
            self.current_task.cancel()
            logger.info("Active orchestrator task cancelled.")
        
        self.bus.publish({
            'type': 'ai_response_error',
            'session_id': 'cancelled',
            'error': 'Execution cancelled by user.'
        })
        self.set_state(JarvisState.IDLE)

    async def _emit_voice_audio_if_needed(self, session_id: str, is_voice: bool, text: str):
        is_voice_session = is_voice or session_id.startswith("voice")
        if is_voice_session and text and text.strip():
            logger.info(f"Synthesizing voice audio for response: '{text[:40]}...'")
            audio_b64, duration_sec = await self.tts.speak(text)
            if audio_b64:
                self.set_state(JarvisState.SPEAKING)
                self.bus.publish({
                    'type': 'audio_response',
                    'session_id': session_id,
                    'audio': audio_b64,
                    'duration': duration_sec
                })
                
                # Duration lock reset task (acts as safety backup if WebSocket playback events are delayed)
                async def _reset_speaking_state(duration: float):
                    await asyncio.sleep(duration + 0.8)
                    if self.state == JarvisState.SPEAKING:
                        logger.info("Duration lock timeout reached. Returning state to IDLE.")
                        self.set_state(JarvisState.IDLE)
                        
                asyncio.create_task(_reset_speaking_state(duration_sec))
            else:
                logger.warning("TTS audio generation returned empty payload.")

    async def handle_chat_message(self, session_id: str, message: str, is_voice: bool = False):
        self.current_task = asyncio.current_task()
        session = SessionManager.get_or_create(session_id)
        
        request_received_time = time.time()
        self.set_state(JarvisState.THINKING)
        
        # 1. Fast Router Pass (supports compound sentences)
        router_start_time = time.time()
        local_intents = self.fast_router.parse_compound(message)
        router_latency = time.time() - router_start_time
        logger.info(f"FastRouter latency: {router_latency:.4f}s")
        
        if local_intents:
            self.set_state(JarvisState.EXECUTING)
            combined_messages = []
            overall_success = True
            
            for intent_name, kwargs in local_intents:
                tool = ToolRegistry.get_tool(intent_name)
                if not tool:
                    continue
                    
                self.bus.publish({
                    'type': 'TOOL_STARTED',
                    'session_id': session.session_id,
                    'tool': tool.name
                })
                
                from app.security.permissions import PermissionLevel
                
                if tool.permission_level == PermissionLevel.CONFIRMATION_REQUIRED:
                    logger.warning(f"Tool {tool.name} requires confirmation. Auto-approving because it was explicitly requested via FastRouter.")
                    pass
                
                if tool.permission_level == PermissionLevel.BLOCKED:
                    result = {
                        "success": False,
                        "tool": tool.name,
                        "message": "This action is explicitly blocked by security policy.",
                        "data": {},
                        "error": "BLOCKED"
                    }
                else:
                    tool_start_time = time.time()
                    try:
                        result = await tool.execute(**kwargs)
                    except Exception as e:
                        logger.error(f"[ERROR] tool execution failed: {e}", exc_info=True)
                        result = {
                            "success": False,
                            "tool": tool.name,
                            "message": "Tool execution failed due to an internal error.",
                            "data": {},
                            "error": str(e)
                        }
                    tool_latency = time.time() - tool_start_time
                    logger.info(f"Tool {tool.name} latency: {tool_latency:.4f}s")

                if not result['success']:
                    overall_success = False
                    self.bus.publish({
                        'type': 'TOOL_ERROR',
                        'session_id': session.session_id,
                        'tool': tool.name,
                        'error': result['message']
                    })
                    combined_messages.append(f"[{tool.name} Error: {result['message']}]")
                else:
                    self.bus.publish({
                        'type': 'TOOL_COMPLETED',
                        'session_id': session.session_id,
                        'tool': tool.name,
                        'success': True
                    })
                    combined_messages.append(result['message'])
                    
            final_message = "\n".join(combined_messages) if combined_messages else "Commands processed."
            session.add_user_message(message)
            session.add_assistant_message(final_message)
            
            self.bus.publish({
                'type': 'ai_response_complete',
                'session_id': session.session_id,
                'message': final_message,
                'is_local': True
            })
            await self._emit_voice_audio_if_needed(session.session_id, is_voice, final_message)
            
            self.set_state(JarvisState.IDLE)
            return

        # 2. Gemini Fallback Path
        self.bus.publish({
            'type': 'ai_response_start',
            'session_id': session.session_id
        })

        # Fetch Contextual Memory
        memory_context = MemoryRetriever.get_context(message)
        if memory_context:
            logger.info("Injected memory context into Gemini prompt.")

        full_response = []
        try:
            async for data in self.router.stream_response(message, session.history, memory_context):
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
                'message': completed_text,
                'is_local': False
            })
            await self._emit_voice_audio_if_needed(session.session_id, is_voice, completed_text)
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
