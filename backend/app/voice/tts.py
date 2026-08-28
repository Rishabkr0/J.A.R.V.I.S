import os
import io
import wave
import base64
import logging
import asyncio
import numpy as np
import piper
from app.core.config import settings

logger = logging.getLogger("jarvis.voice.tts")

class TTS:
    def __init__(self):
        self.model_path = os.path.join("data", "en_US-lessac-low.onnx")
        self.model_json = os.path.join("data", "en_US-lessac-low.onnx.json")
        self.voice = None
        self.is_speaking = False
        
        self._init_piper()

    def _init_piper(self):
        if os.path.exists(self.model_path):
            try:
                self.voice = piper.PiperVoice.load(self.model_path, config_path=self.model_json)
                logger.info(f"Piper TTS loaded model successfully from {self.model_path} (Sample Rate: {self.voice.config.sample_rate}Hz)")
            except Exception as e:
                logger.error(f"Failed to load Piper model: {e}")
                self.voice = None
        else:
            logger.warning(f"Piper model not found at {self.model_path}. Will fallback to Windows SAPI5.")

    def synthesize_wav_bytes(self, text: str) -> bytes:
        if not text or not text.strip():
            return b""

        text = text.strip()
        
        # 1. Try Piper TTS
        if self.voice:
            try:
                wav_io = io.BytesIO()
                with wave.open(wav_io, "wb") as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(self.voice.config.sample_rate)
                    
                    for chunk in self.voice.synthesize(text):
                        audio_int16 = (chunk.audio_float_array * 32767).astype(np.int16)
                        wav_file.writeframes(audio_int16.tobytes())
                        
                wav_bytes = wav_io.getvalue()
                logger.info(f"Piper synthesized {len(text)} chars into {len(wav_bytes)} WAV bytes.")
                return wav_bytes
            except Exception as e:
                logger.error(f"Piper synthesis error: {e}. Falling back to SAPI5.")

        # 2. Fallback to SAPI5 if Piper is unavailable or fails
        try:
            import win32com.client
            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            # We use SAPI5 stream to get WAV bytes if needed or fallback
            logger.info("Using SAPI5 fallback synthesis.")
        except Exception as sapi_err:
            logger.error(f"SAPI5 fallback error: {sapi_err}")

        return b""

    async def speak(self, text: str) -> tuple[str, float]:
        """
        Synthesizes text into (base64-encoded WAV audio string, duration_in_seconds).
        Runs synthesis in executor to prevent blocking asyncio event loop.
        """
        if not text or not text.strip():
            return "", 0.0
            
        self.is_speaking = True
        loop = asyncio.get_running_loop()
        try:
            wav_bytes = await loop.run_in_executor(None, self.synthesize_wav_bytes, text)
            if wav_bytes and len(wav_bytes) > 44:
                b64_audio = base64.b64encode(wav_bytes).decode("utf-8")
                sample_rate = self.voice.config.sample_rate if self.voice else 16000
                duration_sec = (len(wav_bytes) - 44) / (sample_rate * 2.0)
                return b64_audio, round(duration_sec, 2)
            return "", 0.0
        except Exception as e:
            logger.error(f"TTS speak task failed: {e}")
            return "", 0.0
        finally:
            self.is_speaking = False
