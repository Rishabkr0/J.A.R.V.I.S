import re
import logging
from typing import Tuple, Dict, Any, Optional
from app.voice.normalization import TranscriptNormalizer

logger = logging.getLogger('jarvis.fast_router')

class Intent:
    OPEN_APP = 'open_application'
    OPEN_URL = 'open_url'
    VOLUME_CONTROL = 'set_volume'
    SYS_INFO = 'get_system_info'
    LIST_DIR = 'list_directory'
    REMEMBER = 'remember_information'
    FORGET = 'forget_information'
    RECALL = 'recall_information'
    CLEAR_MEMORIES = 'clear_all_memories'
    
    # Browser Intents
    OPEN_BROWSER = 'open_browser'
    NAVIGATE_BROWSER = 'navigate_browser'
    SEARCH_BROWSER = 'search_browser'
    GO_BACK = 'go_back'
    GO_FORWARD = 'go_forward'
    REFRESH_BROWSER = 'refresh_browser'
    CLOSE_BROWSER = 'close_browser'
    GET_BROWSER_STATUS = 'get_browser_status'

class FastRouter:
    """
    Deterministically routes natural language text to Tool intents without LLM overhead.
    Returns (intent_name, kwargs) or None if it should fallback to Gemini.
    """
    
    def __init__(self):
        self.normalizer = TranscriptNormalizer()
        # Extremely lightweight regex mapping
        self.rules = [
            # Browser specifics (Must be before open_app to intercept chrome)
            (r'^(?:open|launch|start) (?:chrome|browser)$', Intent.OPEN_BROWSER),
            (r'^(?:go to|navigate to) (.+)$', Intent.NAVIGATE_BROWSER),
            (r'^(?:search google for) (.+)$', Intent.SEARCH_BROWSER),
            (r'^(?:search|google|look up) (.+)$', Intent.SEARCH_BROWSER),
            (r'^go back$', Intent.GO_BACK),
            (r'^go forward$', Intent.GO_FORWARD),
            (r'^refresh(?: the page)?$', Intent.REFRESH_BROWSER),
            (r'^close (?:chrome|browser)$', Intent.CLOSE_BROWSER),
            (r'^(?:is the )?browser (?:open|status|ready)\??$', Intent.GET_BROWSER_STATUS),
            
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
            (r'^remember that (?:my )?(.+?) is (.+)$', Intent.REMEMBER),
            (r'^forget that (?:my )?(.+?) is (.+)$', Intent.FORGET),
            (r'^forget everything(?: you remember)?$', Intent.CLEAR_MEMORIES),
            (r'^(?:what is|what\'s) my (.+?)$', Intent.RECALL),
        ]

    def parse(self, text: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        normalized = self.normalizer.normalize(text)
        logger.info(f"FastRouter raw: '{text}' -> normalized: '{normalized}'")
        
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
                
                # Browser intents
                if intent == Intent.OPEN_BROWSER:
                    return intent, {}
                if intent == Intent.NAVIGATE_BROWSER:
                    return intent, {'url': groups[0]}
                if intent == Intent.SEARCH_BROWSER:
                    return intent, {'query': groups[0]}
                if intent in [Intent.GO_BACK, Intent.GO_FORWARD, Intent.REFRESH_BROWSER, Intent.CLOSE_BROWSER, Intent.GET_BROWSER_STATUS]:
                    return intent, {}
                
                if intent == Intent.OPEN_APP:
                    app_name = groups[0] if groups else normalized.split()[-1]
                    return intent, {'app_name': app_name}
                    
                if intent == Intent.OPEN_URL:
                    return intent, {'url': groups[0]}

                if intent == Intent.SYS_INFO:
                    return intent, {}
                    
                if intent == Intent.REMEMBER:
                    key = groups[0].replace(' ', '_')
                    val = groups[1]
                    return intent, {'key': key, 'value': val}
                    
                if intent == Intent.FORGET:
                    key = groups[0].replace(' ', '_')
                    return intent, {'key': key}
                    
                if intent == Intent.RECALL:
                    key = groups[0].replace(' ', '_')
                    return intent, {'query': key}
                    
                if intent == Intent.CLEAR_MEMORIES:
                    return intent, {}

        # 3. Check simple list dir (just for testing phase 2)
        if normalized.startswith('list files in '):
            path = text[14:].strip()
            return Intent.LIST_DIR, {'path': path}

        return None
