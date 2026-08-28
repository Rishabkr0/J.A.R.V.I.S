import unittest
from app.voice.normalization import TranscriptNormalizer
from app.orchestrator.fast_router import FastRouter, Intent

class TestTranscriptNormalization(unittest.TestCase):
    def setUp(self):
        self.normalizer = TranscriptNormalizer()
        self.router = FastRouter()

    def test_strip_wake_words(self):
        self.assertEqual(self.normalizer.normalize("Jarvis open chrome"), "open chrome")
        self.assertEqual(self.normalizer.normalize("hey jarvis open chrome"), "open chrome")

    def test_remove_fillers(self):
        self.assertEqual(self.normalizer.normalize("please open chrome"), "open chrome")
        self.assertEqual(self.normalizer.normalize("open chrome please"), "open chrome")
        self.assertEqual(self.normalizer.normalize("could you open notepad"), "open notepad")

    def test_remove_duplicates(self):
        self.assertEqual(self.normalizer.normalize("open open chrome"), "open chrome")
        self.assertEqual(self.normalizer.normalize("open open open edge"), "open edge")

    def test_fuzzy_matching(self):
        self.assertEqual(self.normalizer.normalize("open crew"), "open chrome")
        self.assertEqual(self.normalizer.normalize("launch calc"), "launch calculator")
        self.assertEqual(self.normalizer.normalize("start note pad"), "start notepad")

    def test_router_integration(self):
        # Should route to OPEN_BROWSER for chrome due to Phase 5A rules
        res = self.router.parse("Jarvis, open open crew, please.")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], Intent.OPEN_BROWSER)

        # Should route to OPEN_APP for notepad
        res_app = self.router.parse("Jarvis, start note pad, please.")
        self.assertIsNotNone(res_app)
        self.assertEqual(res_app[0], Intent.OPEN_APP)
        self.assertEqual(res_app[1]['app_name'], 'notepad')

if __name__ == '__main__':
    unittest.main()
