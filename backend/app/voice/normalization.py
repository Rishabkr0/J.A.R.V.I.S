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

    def normalize(self, text: str) -> str:
        """
        Normalizes STT transcript to be more deterministic for FastRouter.
        """
        if not text:
            return ""

        # 1. Lowercase and basic punctuation removal (preserve dots for URLs like youtube.com)
        normalized = text.lower().strip()
        normalized = re.sub(r'[^\w\s\.]', '', normalized)
        # Strip trailing dot if it's just end-of-sentence punctuation (e.g., "open chrome.")
        if normalized.endswith('.') and not re.search(r'\.[a-z]{2,4}$', normalized):
            normalized = normalized.rstrip('.')

        # 2. Strip wake words if they bled into the transcript
        # Sometimes whisper transcribes "jarvis" or "hey jarvis"
        wake_words = ['hey jarvis', 'jarvis']
        for w in wake_words:
            if normalized.startswith(w):
                normalized = normalized[len(w):].strip()

        # 3. Remove filler phrases
        for filler in self.fillers:
            # Remove at the start
            if normalized.startswith(filler + ' '):
                normalized = normalized[len(filler) + 1:].strip()
            # Remove at the end
            if normalized.endswith(' ' + filler):
                normalized = normalized[:-len(filler) - 1].strip()

        # 4. Remove obvious duplicated command words
        # e.g., "open open chrome" -> "open chrome"
        # We only do this for command verbs to be conservative
        command_verbs = ['open', 'launch', 'start']
        words = normalized.split()
        if len(words) >= 2:
            first_word = words[0]
            if first_word in command_verbs:
                # Keep removing the second word if it's identical to the first
                while len(words) > 1 and words[1] == first_word:
                    words.pop(1)
            normalized = " ".join(words)

        # 5. Fuzzy match for known applications
        # FastRouter patterns typically look like "open <app>"
        words = normalized.split()
        if len(words) >= 2 and words[0] in command_verbs:
            app_name = " ".join(words[1:])
            # If it's an exact match, we do nothing
            if app_name not in self.known_apps:
                # Find the best match
                matches = difflib.get_close_matches(app_name, self.known_apps, n=1, cutoff=0.5)
                if matches:
                    best_match = matches[0]
                    logger.info(f"Fuzzy matched '{app_name}' to '{best_match}'")
                    normalized = f"{words[0]} {best_match}"

        return normalized
