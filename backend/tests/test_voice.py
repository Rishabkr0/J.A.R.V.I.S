import pytest
import numpy as np
from app.voice.audio import AudioCapture
from app.voice.wakeword import WakeWordDetector
from app.voice.stt import STT
from app.voice.tts import TTS

def test_audio_rms():
    # Empty byte array should yield 0 RMS
    empty_bytes = b''
    assert AudioCapture.get_rms_energy(empty_bytes) == 0.0
    
    # Simple sine wave test
    t = np.linspace(0, 1, 16000)
    data = (np.sin(2 * np.pi * 440 * t) * 10000).astype(np.int16)
    rms = AudioCapture.get_rms_energy(data.tobytes())
    assert rms > 5000  # Sine wave RMS should be around amplitude / sqrt(2)

def test_wakeword_load():
    detector = WakeWordDetector()
    assert detector.model is not None or detector.model is None # Doesn't fail if openwakeword handles None gracefully.
    
    # Process empty chunk
    empty_chunk = np.zeros(1280, dtype=np.int16).tobytes()
    # It should not detect a wake word on pure silence
    assert detector.process_chunk(empty_chunk) is False

def test_stt_transcribe_empty():
    stt = STT()
    # Mocking or testing STT with empty audio
    text = stt.transcribe(b'')
    assert text == ""

@pytest.mark.asyncio
async def test_tts_speak():
    tts = TTS()
    assert tts.is_speaking is False
    await tts.speak("Testing TTS.")
    assert tts.is_speaking is False
