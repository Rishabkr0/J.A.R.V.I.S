import logging
import io
import time
import numpy as np
from faster_whisper import WhisperModel
from app.core.config import settings

logger = logging.getLogger("jarvis.voice.stt")

class STT:
    def __init__(self):
        self.model = None
        try:
            logger.info(f"Loading faster-whisper model {settings.STT_MODEL} on {settings.STT_DEVICE} ({settings.STT_COMPUTE_TYPE})")
            self.model = WhisperModel(
                model_size_or_path=settings.STT_MODEL,
                device=settings.STT_DEVICE,
                compute_type=settings.STT_COMPUTE_TYPE
            )
            logger.info("STT Model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load STT model: {e}")

    def transcribe(self, audio_data: bytes) -> str:
        """Transcribes raw int16 16kHz audio."""
        if not self.model: return ""
        if not audio_data: return ""
        
        try:
            start = time.time()
            # Convert bytes to float32 numpy array normalized to [-1.0, 1.0] for whisper
            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Optimize transcription parameters for local command accuracy:
            # - vad_filter=True: strips leading/trailing non-speech noise with Silero VAD
            # - condition_on_previous_text=False: prevents repetitive phrase loops ("open open chrome")
            # - initial_prompt: primes Whisper beam search vocabulary towards local commands
            initial_prompt = "JARVIS voice command: Open Chrome, Open Notepad, Search Google for, Go to YouTube, Refresh, Go back."
            segments, info = self.model.transcribe(
                audio_np,
                language="en",
                beam_size=5,
                vad_filter=True,
                condition_on_previous_text=False,
                initial_prompt=initial_prompt
            )
            text = "".join([segment.text for segment in segments]).strip()
            
            logger.info(f"STT Latency: {time.time() - start:.3f}s | Result: '{text}'")
            return text
        except Exception as e:
            logger.error(f"STT Transcription failed: {e}")
            return ""
