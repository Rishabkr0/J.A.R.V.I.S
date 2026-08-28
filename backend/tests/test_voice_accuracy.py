import unittest
import numpy as np
from app.voice.audio import AudioCapture
from app.voice.stt import STT
from app.voice.normalization import TranscriptNormalizer
from app.orchestrator.fast_router import FastRouter, Intent

class TestVoiceAccuracyPipeline(unittest.TestCase):
    def setUp(self):
        self.normalizer = TranscriptNormalizer()
        self.router = FastRouter()

    def test_audio_rms_calculation(self):
        # Silent buffer (all zeros) -> RMS should be 0.0
        silent_chunk = np.zeros(1280, dtype=np.int16).tobytes()
        rms_silent = AudioCapture.get_rms_energy(silent_chunk)
        self.assertEqual(rms_silent, 0.0)

        # Sine wave audio buffer -> RMS should be approx amp / sqrt(2)
        samples = (3000 * np.sin(np.linspace(0, 2 * np.pi * 440, 1280))).astype(np.int16)
        rms_sine = AudioCapture.get_rms_energy(samples.tobytes())
        self.assertGreater(rms_sine, 1500)

    def test_transcript_normalization_voice_phrases(self):
        # 1. Repeated words ("open open chrome") -> "open chrome"
        raw_1 = "open open chrome"
        norm_1 = self.normalizer.normalize(raw_1)
        self.assertEqual(norm_1, "open chrome")

        # 2. Filler phrases ("please open chrome") -> "open chrome"
        raw_2 = "please open chrome"
        norm_2 = self.normalizer.normalize(raw_2)
        self.assertEqual(norm_2, "open chrome")

        # 3. Wake word bleeding ("hey jarvis open notepad") -> "open notepad"
        raw_3 = "hey jarvis open notepad"
        norm_3 = self.normalizer.normalize(raw_3)
        self.assertEqual(norm_3, "open notepad")

    def test_fast_router_browser_and_apps(self):
        intent, args = self.router.parse("open chrome")
        self.assertEqual(intent, Intent.OPEN_BROWSER)

        intent, args = self.router.parse("search google for black holes")
        self.assertEqual(intent, Intent.SEARCH_BROWSER)
        self.assertEqual(args.get("query"), "black holes")

        intent, args = self.router.parse("go to youtube.com")
        self.assertEqual(intent, Intent.NAVIGATE_BROWSER)
        self.assertEqual(args.get("url"), "youtube.com")

        intent, args = self.router.parse("open notepad")
        self.assertEqual(intent, Intent.OPEN_APP)
        self.assertEqual(args.get("app_name"), "notepad")

if __name__ == "__main__":
    unittest.main()
