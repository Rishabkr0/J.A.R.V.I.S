import re
import logging
from typing import Tuple, Dict, Any, Optional

logger = logging.getLogger('jarvis.fast_router')

class Intent:
    OPEN_APP = 'open_application'
    OPEN_URL = 'open_url'
    VOLUME_CONTROL = 'set_volume'
    SYS_INFO = 'get_system_info'
    LIST_DIR = 'list_directory'

class FastRouter:
    """
    Deterministically routes natural language text to Tool intents without LLM overhead.
    Returns (intent_name, kwargs) or None if it should fallback to Gemini.
    """
    
    def __init__(self):
        # Extremely lightweight regex mapping
        self.rules = [
            (r'^(?:open|launch|start) (chrome|edge|notepad|calculator|terminal|explorer|cmd)$', Intent.OPEN_APP),
            (r'^(?:can you )?(?:open|launch) (?:chrome|edge|notepad|calculator|terminal|explorer|cmd)$', Intent.OPEN_APP),
            (r'^(?:go to|open url) (.+\.[a-z]+)$', Intent.OPEN_URL),
            (r'^(?:open|launch) (.+\.[a-z]+)$', Intent.OPEN_URL),
            (r'^(?:turn )?volume up', Intent.VOLUME_CONTROL),
            (r'^(?:increase|raise) volume', Intent.VOLUME_CONTROL),
            (r'^(?:turn )?volume down', Intent.VOLUME_CONTROL),
            (r'^(?:decrease|lower) volume', Intent.VOLUME_CONTROL),
            (r'^(?:mute|silence)(?: volume)?', Intent.VOLUME_CONTROL),
            (r'^(?:unmute)(?: volume)?', Intent.VOLUME_CONTROL),
            (r'^(?:what is my system info|system info|system specs|get system info)', Intent.SYS_INFO),
        ]

    def parse(self, text: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        normalized = text.lower().strip().rstrip('.?!')
        
        # 1. Check Volume
        if 'volume up' in normalized or 'increase volume' in normalized or 'raise volume' in normalized:
            return Intent.VOLUME_CONTROL, {'action': 'up'}
        if 'volume down' in normalized or 'decrease volume' in normalized or 'lower volume' in normalized:
            return Intent.VOLUME_CONTROL, {'action': 'down'}
        if 'mute' in normalized or 'silence' in normalized:
            if 'unmute' not in normalized:
                return Intent.VOLUME_CONTROL, {'action': 'mute'}

        # 2. Check general regexes
        for pattern, intent in self.rules:
            match = re.search(pattern, normalized)
            if match:
                groups = match.groups()
                
                if intent == Intent.OPEN_APP:
                    app_name = groups[0] if groups else normalized.split()[-1]
                    return intent, {'app_name': app_name}
                    
                if intent == Intent.OPEN_URL:
                    return intent, {'url': groups[0]}

                if intent == Intent.SYS_INFO:
                    return intent, {}

        # 3. Check simple list dir (just for testing phase 2)
        if normalized.startswith('list files in '):
            path = text[14:].strip()
            return Intent.LIST_DIR, {'path': path}

        return None
