import asyncio
import logging
from typing import Callable, List, Any

logger = logging.getLogger('jarvis.bus')

class EventBus:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.subscribers = []
        return cls._instance

    def subscribe(self, callback: Callable[[Any], Any]):
        self.subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[Any], Any]):
        if callback in self.subscribers:
            self.subscribers.remove(callback)

    def publish(self, event: dict):
        logger.info(f'Publishing event: {event}')
        for sub in self.subscribers:
            asyncio.create_task(sub(event))
