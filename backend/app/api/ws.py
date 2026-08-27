from fastapi import APIRouter, WebSocket, WebSocketDisconnect
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
