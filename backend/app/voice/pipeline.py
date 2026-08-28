import asyncio
import logging
import time
import collections
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
        self.preroll_buffer = collections.deque(maxlen=20) # ~1.6 seconds pre-roll
        self.silence_start = None
        self.SILENCE_THRESHOLD_RMS = 300  # Tuned for moderate background noise vs user voice
        self.SILENCE_DURATION = 1.2       # Seconds of silence to trigger STT

    def start(self):
        if not settings.VOICE_ENABLED:
            logger.info("Voice is disabled in config.")
            return
            
        if self.is_running and self.task and not self.task.done():
            logger.info("Voice Pipeline is already running.")
            return

        self.audio_buffer.clear()
        self.preroll_buffer.clear()
        self.state = "IDLE"

        self.audio.start()
        if not self.audio.is_running:
            logger.error("Microphone failed to start. Stopping voice pipeline.")
            self.bus.publish({
                'type': 'ai_response_error',
                'error': 'Microphone initialization failed. Please check your audio devices.',
                'session_id': 'voice-error'
            })
            self.orchestrator.set_state(JarvisState.IDLE)
            return

        self.is_running = True
        self.task = asyncio.create_task(self._run_loop())
        logger.info("Voice Pipeline started.")

    def stop(self):
        self.is_running = False
        self.audio.stop()
        if self.task and not self.task.done():
            self.task.cancel()
        self.task = None
        self.audio_buffer.clear()
        self.preroll_buffer.clear()
        self.state = "IDLE"
        logger.info("Voice Pipeline stopped cleanly.")

    async def _run_loop(self):
        while self.is_running:
            try:
                # Non-blocking get
                chunk = self.audio.get_chunk(block=False)
                if not chunk:
                    await asyncio.sleep(0.01)
                    continue

                # Self-listening suppression check:
                # If system is speaking, thinking, or executing, discard microphone audio to prevent feedback loop
                orchestrator_state = self.orchestrator.state
                if orchestrator_state in (JarvisState.SPEAKING, JarvisState.THINKING, JarvisState.EXECUTING) or self.tts.is_speaking:
                    self.audio_buffer.clear()
                    self.preroll_buffer.clear()
                    self.speaking_end_time = time.time()
                    await asyncio.sleep(0.01)
                    continue

                # Echo cushion: wait 0.8s after speech completes before listening again
                if hasattr(self, 'speaking_end_time'):
                    if time.time() - self.speaking_end_time < 0.8:
                        self.preroll_buffer.clear()
                        await asyncio.sleep(0.01)
                        continue
                    else:
                        delattr(self, 'speaking_end_time')

                if self.state == "IDLE":
                    self.preroll_buffer.append(chunk)
                    # Look for wake word
                    if self.wakeword.process_chunk(chunk):
                        logger.info("WAKE WORD DETECTED")
                        self.state = "LISTENING"
                        self.audio_buffer.clear()
                        # Keep last 12 chunks (~960ms cushion) so start of utterances ("what...", "which...") are never clipped
                        cushion_chunks = list(self.preroll_buffer)[-12:]
                        for c in cushion_chunks:
                            self.audio_buffer.extend(c)
                        self.silence_start = None
                        self.speech_start_time = time.time()
                        
                        self.bus.publish({
                            'type': 'state_changed',
                            'state': JarvisState.LISTENING,
                            'data': {'source': 'voice'}
                        })
                        
                elif self.state == "LISTENING":
                    self.audio_buffer.extend(chunk)
                    
                    if not hasattr(self, 'listening_start'):
                        self.listening_start = time.time()
                    
                    rms = self.audio.get_rms_energy(chunk)
                    
                    # Force process if we've been listening too long (e.g., noisy room preventing silence)
                    if time.time() - self.listening_start > 6.0:
                        logger.info("Max recording duration reached, forcing processing.")
                        delattr(self, 'listening_start')
                        try:
                            await self._process_utterance()
                        except asyncio.CancelledError:
                            logger.info("Utterance processing cancelled. Resetting voice state.")
                            self.state = "IDLE"
                            self.orchestrator.set_state(JarvisState.IDLE)
                        continue
                        
                    if rms < self.SILENCE_THRESHOLD_RMS:
                        if self.silence_start is None:
                            self.silence_start = time.time()
                        elif time.time() - self.silence_start > self.SILENCE_DURATION:
                            # End of utterance
                            delattr(self, 'listening_start')
                            try:
                                await self._process_utterance()
                            except asyncio.CancelledError:
                                logger.info("Utterance processing cancelled. Resetting voice state.")
                                self.state = "IDLE"
                                self.orchestrator.set_state(JarvisState.IDLE)
                    else:
                        # Reset silence timer
                        self.silence_start = None

            except asyncio.CancelledError:
                if not self.is_running:
                    break
                logger.info("Voice loop caught cancellation while active; resetting state to IDLE.")
                self.state = "IDLE"
                self.orchestrator.set_state(JarvisState.IDLE)
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Voice pipeline error: {e}")
                await asyncio.sleep(1)

    async def _process_utterance(self):
        speech_end_time = time.time()
        speech_start_time = getattr(self, 'speech_start_time', speech_end_time - 1.0)
        utterance_duration = speech_end_time - speech_start_time
        logger.info(f"VAD timing | speech_start: {speech_start_time:.2f}s | speech_end: {speech_end_time:.2f}s | duration: {utterance_duration:.2f}s")
        
        self.state = "THINKING"
        self.bus.publish({
            'type': 'state_changed',
            'state': JarvisState.THINKING,
            'data': {}
        })
        
        # 1. STT
        audio_data = bytes(self.audio_buffer)
        self.audio_buffer.clear()
        
        stt_start_time = time.time()
        text = self.stt.transcribe(audio_data)
        stt_latency = time.time() - stt_start_time
        
        if not text:
            logger.info("No speech detected by STT.")
            self.state = "IDLE"
            self.orchestrator.set_state(JarvisState.IDLE)
            return
            
        logger.info(f"User said (RAW STT): '{text}' in {stt_latency:.3f}s")
        
        # Send raw text to UI
        session_id = "voice-sess"
        self.bus.publish({
            'type': 'chat_message',
            'session_id': session_id,
            'message': text,
            'role': 'user'
        })
        
        # Calculate normalized text & local intent for debug tracking
        normalized_text = self.orchestrator.fast_router.normalizer.normalize(text)
        local_intent = self.orchestrator.fast_router.parse(text)
        intent_name = local_intent[0] if local_intent else "Gemini (Fallback)"
        
        # Publish rich debug payload for developer view
        self.bus.publish({
            'type': 'voice_debug',
            'raw_stt': text,
            'normalized_stt': normalized_text,
            'intent': intent_name,
            'stt_latency': round(stt_latency, 3),
            'utterance_duration': round(utterance_duration, 2)
        })
        
        # 2. Route via Orchestrator (Voice Mode)
        await self.orchestrator.handle_chat_message(session_id, text, is_voice=True)
        self.state = "IDLE"

