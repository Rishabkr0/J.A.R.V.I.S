import asyncio
import logging
import time
from app.events.bus import EventBus
from app.events.models import JarvisEvent, JarvisState
from app.voice.audio import AudioCapture
from app.voice.wakeword import WakeWordDetector
from app.voice.stt import STT
from app.voice.tts import TTS
from app.core.config import settings
from app.orchestrator.core import Orchestrator

logger = logging.getLogger("jarvis.voice.pipeline")

class VoicePipeline:
    def __init__(self, orchestrator: Orchestrator):
        self.orchestrator = orchestrator
        self.bus = orchestrator.bus
        
        self.audio = AudioCapture(device=settings.AUDIO_INPUT_DEVICE)
        self.wakeword = WakeWordDetector()
        self.stt = STT()
        self.tts = TTS()
        
        self.is_running = False
        self.task = None
        
        # Audio capturing state
        self.state = "IDLE" # IDLE, LISTENING
        self.audio_buffer = bytearray()
        self.silence_start = None
        self.SILENCE_THRESHOLD_RMS = 500  # Adjust based on mic
        self.SILENCE_DURATION = 1.2       # Seconds of silence to trigger STT

    def start(self):
        if not settings.VOICE_ENABLED:
            logger.info("Voice is disabled in config.")
            return
            
        self.audio.start()
        self.is_running = True
        self.task = asyncio.create_task(self._run_loop())
        logger.info("Voice Pipeline started.")

    def stop(self):
        self.is_running = False
        self.audio.stop()
        if self.task:
            self.task.cancel()
        logger.info("Voice Pipeline stopped.")

    async def _run_loop(self):
        while self.is_running:
            try:
                # Non-blocking get
                chunk = self.audio.get_chunk(block=False)
                if not chunk:
                    await asyncio.sleep(0.01)
                    continue

                if self.state == "IDLE":
                    # Look for wake word
                    if self.wakeword.process_chunk(chunk):
                        logger.info("WAKE WORD DETECTED")
                        self.state = "LISTENING"
                        self.audio_buffer.clear()
                        self.silence_start = None
                        
                        self.bus.publish({
                            'type': 'state_changed',
                            'state': JarvisState.LISTENING,
                            'data': {'source': 'voice'}
                        })
                        
                elif self.state == "LISTENING":
                    self.audio_buffer.extend(chunk)
                    
                    rms = self.audio.get_rms_energy(chunk)
                    if rms < self.SILENCE_THRESHOLD_RMS:
                        if self.silence_start is None:
                            self.silence_start = time.time()
                        elif time.time() - self.silence_start > self.SILENCE_DURATION:
                            # End of utterance
                            await self._process_utterance()
                    else:
                        # Reset silence timer
                        self.silence_start = None

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Voice pipeline error: {e}")
                await asyncio.sleep(1)

    async def _process_utterance(self):
        self.state = "THINKING"
        self.bus.publish({
            'type': 'state_changed',
            'state': JarvisState.THINKING,
            'data': {}
        })
        
        # 1. STT
        audio_data = bytes(self.audio_buffer)
        self.audio_buffer.clear()
        
        text = self.stt.transcribe(audio_data)
        if not text:
            logger.info("No speech detected.")
            self.state = "IDLE"
            self.orchestrator.set_state(JarvisState.IDLE)
            return
            
        logger.info(f"User said: {text}")
        
        # Send text to UI
        session_id = "voice-sess"
        self.bus.publish({
            'type': 'chat_message',
            'session_id': session_id,
            'message': text,
            'role': 'user'
        })
        
        # 2. Route via Orchestrator
        # We use handle_chat_message which already processes FastRouter and Gemini
        # It's async so we can await it.
        await self.orchestrator.handle_chat_message(session_id, text)
        
        # For Phase 3: the TTS happens via catching the ai_response_complete event.
        # But to keep it simple, we could just hook into the event bus in TTS.
        
        self.state = "IDLE"
