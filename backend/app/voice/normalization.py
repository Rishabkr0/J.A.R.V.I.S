import re
import logging
import difflib

logger = logging.getLogger('jarvis.voice.normalization')

class TranscriptNormalizer:
    def __init__(self):
        # Known applications we can fuzzy match against
        self.known_apps = [
            'chrome', 'edge', 'notepad', 'calculator', 
            'terminal', 'explorer', 'cmd'
        ]
        
        # Filler phrases to remove
        self.fillers = [
            'please', 'could you', 'can you', 'would you', 'kindly'
        ]

        # Known phonetic STT acoustic misrecognitions on short commands
        self.stt_phonetic_fixes = {
            "what we do is active": "what window is active",
            "what when do is active": "what window is active",
            "which when do is active": "which window is active",
            "reed my screen": "read my screen",
            "red my screen": "read my screen",
            "what is on my screen": "whats on my screen",
            "take screenshot": "take a screenshot",
        }

        # Canonical command phrases for strict structure matching
        self.canonical_commands = [
            "what window is active",
            "which window is active",
            "what application is active",
            "which application is active",
            "what app is active",
            "which app is active",
            "read my screen",
            "read the screen",
            "whats on my screen",
            "what is on my screen",
            "take a screenshot",
            "capture screen",
            "open chrome",
            "open notepad",
            "go to youtube",
            "go back",
            "refresh",
            "close browser",
        ]

    def normalize(self, text: str) -> str:
        """
        Normalizes STT transcript to be deterministic for FastRouter.
        Applies cleaning, filler removal, phonetic fixes, and controlled high-confidence fuzzy matching.
        """
        if not text:
            return ""

        # 1. Lowercase and basic punctuation removal
        normalized = text.lower().strip()

        # 2. Strip wake words AND any punctuation immediately following wake word (e.g. "hey jarvis.", "hey jarvis,")
        normalized = re.sub(r'^(?:hey\s+)?jarvis[\s\.,!\?:]*', '', normalized).strip()

        # 3. Clean leading non-alphanumeric characters and special chars (preserve dots for URLs)
        normalized = re.sub(r'^[^\w]+', '', normalized)
        normalized = re.sub(r'[^\w\s\.]', '', normalized)
        if normalized.endswith('.') and not re.search(r'\.[a-z]{2,4}$', normalized):
            normalized = normalized.rstrip('.')
        normalized = normalized.strip()

        # 3. Remove filler phrases
        for filler in self.fillers:
            if normalized.startswith(filler + ' '):
                normalized = normalized[len(filler) + 1:].strip()
            if normalized.endswith(' ' + filler):
                normalized = normalized[:-len(filler) - 1].strip()

        # 4. Direct Phonetic Fixes for known acoustic STT misrecognitions
        if normalized in self.stt_phonetic_fixes:
            fixed = self.stt_phonetic_fixes[normalized]
            logger.info(f"Phonetic STT fix applied: '{normalized}' -> '{fixed}'")
            return fixed

        # 5. Controlled High-Confidence Fuzzy Phrase Matching
        # Prevents long conversational sentences (e.g. "I was talking about an active window yesterday")
        # from triggering command executions by enforcing strict sentence length and similarity constraints.
        words = normalized.split()
        if len(words) <= 7: # Only attempt fuzzy phrase mapping for short command-like sentences
            best_match = None
            best_score = 0.0
            
            for cmd in self.canonical_commands:
                cmd_words = cmd.split()
                # Action verb must match (e.g. 'close' cannot fuzzy match 'open')
                if words[0] != cmd_words[0]:
                    continue
                # Strict word count delta constraint (+/- 2 words max)
                if abs(len(words) - len(cmd_words)) > 2:
                    continue
                    
                ratio = difflib.SequenceMatcher(None, normalized, cmd).ratio()
                if ratio >= 0.75 and ratio > best_score:
                    best_score = ratio
                    best_match = cmd
                    
            if best_match:
                logger.info(f"Controlled command fuzzy match: '{normalized}' -> '{best_match}' (Confidence: {best_score:.2f})")
                return best_match

        # 6. Remove obvious duplicated command words
        command_verbs = ['open', 'launch', 'start']
        if len(words) >= 2:
            first_word = words[0]
            if first_word in command_verbs:
                while len(words) > 1 and words[1] == first_word:
                    words.pop(1)
            normalized = " ".join(words)

        # 7. Fuzzy match for known applications
        # Handle common app alias splits e.g. "note pad" -> "notepad", "calc" -> "calculator"
        normalized = re.sub(r'\bnote pad\b', 'notepad', normalized)
        normalized = re.sub(r'\bcalc\b', 'calculator', normalized)
        
        words = normalized.split()
        if len(words) >= 2 and words[0] in command_verbs:
            app_name = " ".join(words[1:])
            if app_name not in self.known_apps:
                matches = difflib.get_close_matches(app_name, self.known_apps, n=1, cutoff=0.5)
                if matches:
                    best_match = matches[0]
                    logger.info(f"Fuzzy matched application '{app_name}' to '{best_match}'")
                    normalized = f"{words[0]} {best_match}"

        return normalized
