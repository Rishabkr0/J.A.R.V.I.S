import asyncio
import unittest
from unittest.mock import MagicMock, patch
from app.voice.tts import TTS
from app.orchestrator.core import Orchestrator

class TestTTSPipeline(unittest.TestCase):
    def setUp(self):
        self.tts = TTS()

    def test_tts_initialization(self):
        self.assertIsNotNone(self.tts)
        self.assertFalse(self.tts.is_speaking)

    def test_empty_text_returns_empty(self):
        audio, duration = asyncio.run(self.tts.speak(""))
        self.assertEqual(audio, "")
        self.assertEqual(duration, 0.0)
        
        audio2, duration2 = asyncio.run(self.tts.speak("   "))
        self.assertEqual(audio2, "")
        self.assertEqual(duration2, 0.0)

    def test_piper_synthesis_generates_audio(self):
        audio, duration = asyncio.run(self.tts.speak("Testing Piper TTS voice output."))
        self.assertIsNotNone(audio)
        self.assertTrue(len(audio) > 100) # Base64 audio payload
        self.assertTrue(duration > 0.5)

    @patch('app.events.bus.EventBus.publish')
    def test_orchestrator_emits_audio_response(self, mock_publish):
        orchestrator = Orchestrator()
        
        # Test emitting voice audio
        asyncio.run(
            orchestrator._emit_voice_audio_if_needed("voice-sess-123", is_voice=True, text="Testing voice audio emission.")
        )
        
        # Verify event was published
        mock_publish.assert_called()
        call_args = mock_publish.call_args[0][0]
        self.assertEqual(call_args['type'], 'audio_response')
        self.assertEqual(call_args['session_id'], 'voice-sess-123')
        self.assertTrue(len(call_args['audio']) > 100)
        self.assertTrue(call_args['duration'] > 0.5)

if __name__ == '__main__':
    unittest.main()
