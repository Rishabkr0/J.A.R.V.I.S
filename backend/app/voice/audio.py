import numpy as np
import sounddevice as sd
import queue
import logging
import asyncio

logger = logging.getLogger("jarvis.voice.audio")

class AudioCapture:
    def __init__(self, device=None, sample_rate=16000, chunk_size=1280):
        self.device = device
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.queue = queue.Queue()
        self.stream = None
        self.is_running = False

    def audio_callback(self, indata, frames, time, status):
        if status:
            logger.warning(f"Audio status: {status}")
        self.queue.put(bytes(indata))

    def start(self):
        if self.is_running: return
        try:
            self.stream = sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=self.chunk_size,
                device=self.device,
                channels=1,
                dtype='int16',
                callback=self.audio_callback
            )
            self.stream.start()
            self.is_running = True
            logger.info("Microphone started.")
        except Exception as e:
            logger.error(f"Failed to open microphone: {e}")
            self.is_running = False

    def stop(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
        self.is_running = False
        logger.info("Microphone stopped.")

    def get_chunk(self, block=False, timeout=None):
        try:
            return self.queue.get(block=block, timeout=timeout)
        except queue.Empty:
            return None

    @staticmethod
    def get_rms_energy(audio_chunk: bytes) -> float:
        """Lightweight Volume/Energy VAD computation."""
        data = np.frombuffer(audio_chunk, dtype=np.int16)
        if len(data) == 0: return 0.0
        return np.sqrt(np.mean(data.astype(np.float32)**2))
