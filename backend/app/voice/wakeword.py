import logging
import numpy as np
from openwakeword.model import Model

logger = logging.getLogger("jarvis.voice.wakeword")

class WakeWordDetector:
    def __init__(self):
        # We use a standard openwakeword model "alexa" for this phase as it requires no training.
        # Alternatively, "hey_jarvis" requires a custom trained model to be downloaded.
        # Since we must keep dependencies low and strictly local, we will use alexa or hey mycroft.
        try:
            self.model = Model(inference_framework="onnx")
            # Actually, openwakeword comes with 'alexa', 'hey_mycroft', 'timer' built-in.
            self.target_word = "alexa" # Using standard model as a stand-in for JARVIS
            logger.info(f"WakeWordDetector loaded. Target: {self.target_word}")
        except Exception as e:
            logger.error(f"Failed to load WakeWordDetector: {e}")
            self.model = None

    def process_chunk(self, audio_chunk: bytes) -> bool:
        if not self.model: return False
        
        # openwakeword expects int16 numpy array
        data = np.frombuffer(audio_chunk, dtype=np.int16)
        prediction = self.model.predict(data)
        
        # prediction is a dict: {'alexa': 0.123, ...}
        for name, score in prediction.items():
            if score > 0.5:  # threshold
                return True
        return False
