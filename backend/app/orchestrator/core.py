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
import app.tools.impl.windows_url
import app.tools.impl.windows_volume
import app.tools.impl.windows_sysinfo
import app.tools.impl.fs_tools
import app.tools.impl.memory_tools

logger = logging.getLogger('jarvis.orchestrator')

class Orchestrator:
    def __init__(self):
        self.bus = EventBus()
        self.router = BrainRouter()
        self.fast_router = FastRouter()
        self.state = JarvisState.IDLE

    def set_state(self, new_state: JarvisState, data: dict = None):
        self.state = new_state
        event = JarvisEvent(type='state_changed', state=self.state, data=data or {})
        self.bus.publish(event.model_dump())

    async def handle_chat_message(self, session_id: str, message: str):
        session = SessionManager.get_or_create(session_id)
        
        request_received_time = time.time()
        self.set_state(JarvisState.THINKING)
        
        # 1. Fast Router Pass
        router_start_time = time.time()
        local_intent = self.fast_router.parse(message)
        router_latency = time.time() - router_start_time
        logger.info(f"FastRouter latency: {router_latency:.4f}s")
        
        if local_intent:
            intent_name, kwargs = local_intent
            tool = ToolRegistry.get_tool(intent_name)
            
            if tool:
                # Local tool execution path
                self.set_state(JarvisState.EXECUTING)
                
                self.bus.publish({
                    'type': 'TOOL_STARTED',
                    'session_id': session.session_id,
                    'tool': tool.name
                })
                
                from app.security.permissions import PermissionLevel
                
                # Verify Permissions (Item 6 of Audit)
                if tool.permission_level == PermissionLevel.CONFIRMATION_REQUIRED:
                    result = {
                        "success": False,
                        "tool": tool.name,
                        "message": "This action requires explicit confirmation which is not yet supported in Phase 2.",
                        "data": {},
                        "error": "CONFIRMATION_REQUIRED"
                    }
                    tool_latency = 0.0
                elif tool.permission_level == PermissionLevel.BLOCKED:
                    result = {
                        "success": False,
                        "tool": tool.name,
                        "message": "This action is explicitly blocked by security policy.",
                        "data": {},
                        "error": "BLOCKED"
                    }
                    tool_latency = 0.0
                else:
                    tool_start_time = time.time()
                    result = await tool.execute(**kwargs)
                    tool_latency = time.time() - tool_start_time
                
                total_latency = time.time() - request_received_time
                
                logger.info(f"Tool {tool.name} latency: {tool_latency:.4f}s | Total Local Latency: {total_latency:.4f}s")
                
                self.bus.publish({
                    'type': 'TOOL_COMPLETED',
                    'session_id': session.session_id,
                    'tool': tool.name,
                    'success': result['success']
                })
                
                session.add_user_message(message)
                session.add_assistant_message(result['message'])
                
                # We reuse ai_response_complete to show the local response instantly
                self.bus.publish({
                    'type': 'ai_response_complete',
                    'session_id': session.session_id,
                    'message': result['message'],
                    'is_local': True
                })
                
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
