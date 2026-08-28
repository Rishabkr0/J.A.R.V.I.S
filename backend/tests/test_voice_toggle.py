import asyncio
import unittest
from unittest.mock import MagicMock
from app.orchestrator.core import Orchestrator
from app.voice.pipeline import VoicePipeline

class TestVoiceToggle(unittest.TestCase):
    def test_pipeline_toggle_cycle(self):
        orchestrator = Orchestrator()
        pipeline = VoicePipeline(orchestrator)
        
        # Mock audio start/stop to avoid hardware dependency in tests
        pipeline.audio.start = MagicMock()
        pipeline.audio.stop = MagicMock()
        pipeline.audio.is_running = True
        
        # 1. First start
        asyncio.run(self._toggle_cycle(pipeline))
        self.assertFalse(pipeline.is_running)

    async def _toggle_cycle(self, pipeline):
        pipeline.start()
        self.assertTrue(pipeline.is_running)
        await asyncio.sleep(0.05)
        
        # Try duplicate start (should be ignored)
        pipeline.start()
        self.assertTrue(pipeline.is_running)
        
        # Stop
        pipeline.stop()
        self.assertFalse(pipeline.is_running)
        self.assertIsNone(pipeline.task)
        
        # Start again
        pipeline.start()
        self.assertTrue(pipeline.is_running)
        await asyncio.sleep(0.05)
        
        # Final stop
        pipeline.stop()
        self.assertFalse(pipeline.is_running)

if __name__ == '__main__':
    unittest.main()
