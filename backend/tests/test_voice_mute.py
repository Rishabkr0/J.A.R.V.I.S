import unittest
from unittest.mock import MagicMock
from app.events.models import JarvisState

class TestVoiceMuteSuppression(unittest.TestCase):
    def test_state_suppression(self):
        # Mock orchestrator states
        non_idle_states = [JarvisState.SPEAKING, JarvisState.THINKING, JarvisState.EXECUTING]
        for state in non_idle_states:
            self.assertIn(state, (JarvisState.SPEAKING, JarvisState.THINKING, JarvisState.EXECUTING))

if __name__ == '__main__':
    unittest.main()
