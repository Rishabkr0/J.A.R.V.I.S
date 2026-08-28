import logging
import numpy as np
from openwakeword.model import Model

logger = logging.getLogger("jarvis.voice.wakeword")

class WakeWordDetector:
    def __init__(self):
        try:
            # Load the official built-in 'hey_jarvis' ONNX model
            self.model = Model(
                inference_framework="onnx",
                wakeword_models=["hey_jarvis"]
            )
            self.target_word = "hey_jarvis"
            logger.info(f"WakeWordDetector loaded successfully. Target: '{self.target_word}' (Models: {list(self.model.models.keys())})")
        except Exception as e:
            logger.error(f"Failed to load WakeWordDetector: {e}")
            self.model = None

    def process_chunk(self, audio_chunk: bytes) -> bool:
        if not self.model: return False
        
        # openwakeword expects int16 numpy array
        data = np.frombuffer(audio_chunk, dtype=np.int16)
        prediction = self.model.predict(data)
        
        if not hasattr(self, '_chunk_count'): self._chunk_count = 0
        self._chunk_count += 1
        
        for name, score in prediction.items():
            if self._chunk_count % 20 == 0:
                logger.debug(f"WakeWord Score ({name}): {score:.3f}")
            if score > 0.4:  # Sensitivity threshold for 'hey_jarvis'
                logger.info(f"WAKE WORD DETECTED ({name}) with score: {score:.3f}")
                return True
        return False
