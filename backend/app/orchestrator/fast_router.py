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
    
    # Windows GUI Intents
    LIST_WINDOWS = 'list_windows'
    FOCUS_WINDOW = 'focus_window'
    MINIMIZE_WINDOW = 'minimize_window'
    MAXIMIZE_WINDOW = 'maximize_window'
    RESTORE_WINDOW = 'restore_window'
    CLOSE_WINDOW = 'close_window'
    TYPE_TEXT = 'type_text'
    PRESS_KEY = 'press_key'
    MOVE_MOUSE = 'move_mouse'
    CLICK_MOUSE = 'click_mouse'
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
            
            # Windows GUI specifics
            (r'^(?:list|show)(?: all)? (?:open )?windows$', Intent.LIST_WINDOWS),
            (r'^(?:focus|switch to|bring) (.+?)(?: to the front)?$', Intent.FOCUS_WINDOW),
            (r'^minimize (.+)$', Intent.MINIMIZE_WINDOW),
            (r'^maximize (.+)$', Intent.MAXIMIZE_WINDOW),
            (r'^restore (.+)$', Intent.RESTORE_WINDOW),
            (r'^close (.+)$', Intent.CLOSE_WINDOW),
            
            # Typing with formatting & target options
            (r'^type "(.*?)" (?:in|on) (?:the )?(?:next|new) line into (.+)$', Intent.TYPE_TEXT),
            (r'^type "(.*?)" (?:in|on) (?:the )?(?:next|new) line$', Intent.TYPE_TEXT),
            (r'^type (.*?) (?:in|on) (?:the )?(?:next|new) line into (.+)$', Intent.TYPE_TEXT),
            (r'^type (.*?) (?:in|on) (?:the )?(?:next|new) line$', Intent.TYPE_TEXT),
            (r'^type "(.*?)" into (.+)$', Intent.TYPE_TEXT),
            (r'^type "(.*?)"$', Intent.TYPE_TEXT),
            (r'^type (.+?) into (.+)$', Intent.TYPE_TEXT),
            (r'^type (.+)$', Intent.TYPE_TEXT),
            (r'^(?:press|hit) (.+)$', Intent.PRESS_KEY),
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
                    query = groups[0]
                    if query.lower().startswith('for '):
                        query = query[4:].strip()
                    return intent, {'query': query}
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
                    
                # GUI Intents
                if intent == Intent.LIST_WINDOWS:
                    return intent, {}
                if intent in [Intent.FOCUS_WINDOW, Intent.MINIMIZE_WINDOW, Intent.MAXIMIZE_WINDOW, Intent.RESTORE_WINDOW, Intent.CLOSE_WINDOW]:
                    return intent, {'window_title': groups[0]}
                if intent == Intent.TYPE_TEXT:
                    raw_lower = normalized.lower()
                    has_newline = 'next line' in raw_lower or 'new line' in raw_lower
                    
                    text_content = groups[0].strip('\'"')
                    if len(groups) == 2:
                        return intent, {'text': text_content, 'target_window': groups[1], 'new_line': has_newline}
                    return intent, {'text': text_content, 'new_line': has_newline}
                if intent == Intent.PRESS_KEY:
                    key_map = {
                        "enter": "{ENTER}",
                        "return": "{ENTER}",
                        "tab": "{TAB}",
                        "escape": "{ESC}",
                        "esc": "{ESC}",
                        "backspace": "{BACKSPACE}",
                        "space": "{SPACE}",
                        "up": "{UP}",
                        "down": "{DOWN}",
                        "left": "{LEFT}",
                        "right": "{RIGHT}",
                        "ctrl s": "^s",
                        "control s": "^s",
                        "ctrl c": "^c",
                        "ctrl v": "^v",
                        "alt tab": "%{TAB}"
                    }
                    key_str = groups[0].lower().strip()
                    # Map natural language keys to pywinauto codes
                    mapped = key_map.get(key_str, key_str)
                    return intent, {'keys': mapped}

        # 3. Check simple list dir (just for testing phase 2)
        if normalized.startswith('list files in '):
            path = text[14:].strip()
            return Intent.LIST_DIR, {'path': path}

        return None

    def parse_compound(self, text: str) -> Optional[List[Tuple[str, Dict[str, Any]]]]:
        """
        Parses compound sentences connected by 'and', 'then', or 'and then'.
        Returns a list of (intent_name, kwargs) tuples, or None if unroutable.
        """
        parts = [p.strip() for p in re.split(r'\b(?:and then|and|then)\b', text, flags=re.IGNORECASE) if p.strip()]
        
        if len(parts) <= 1:
            res = self.parse(text)
            return [res] if res else None
            
        intents = []
        for part in parts:
            res = self.parse(part)
            if res:
                intents.append(res)
            else:
                # If any part of a compound command cannot be routed deterministically, fallback to Gemini
                logger.info(f"Compound part '{part}' could not be routed locally. Falling back to Gemini.")
                return None
                
        return intents if intents else None
