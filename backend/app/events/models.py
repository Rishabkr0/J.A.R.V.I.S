from enum import Enum
from pydantic import BaseModel
from typing import Any, Dict

class JarvisState(str, Enum):
    IDLE = 'IDLE'
    LISTENING = 'LISTENING'
    THINKING = 'THINKING'
    EXECUTING = 'EXECUTING'
    SPEAKING = 'SPEAKING'
    ERROR = 'ERROR'
    OFFLINE = 'OFFLINE'

class JarvisEvent(BaseModel):
    type: str
    state: JarvisState
    data: Dict[str, Any] = {}
