import unittest
from unittest.mock import patch, MagicMock
from app.tools.impl.gui_context import GUITargetContext
from app.tools.impl.windows_gui import resolve_and_focus_target, TypeTextTool
from app.orchestrator.fast_router import FastRouter, Intent

class TestGUITargetFocus(unittest.TestCase):
    def setUp(self):
        self.ctx = GUITargetContext.get_instance()
        self.ctx.clear()

    def test_gui_context_lifecycle(self):
        self.assertFalse(self.ctx.is_valid())
        self.ctx.set_target(12345, "Test Window", "test.exe")
        self.assertEqual(self.ctx.handle, 12345)
        self.assertEqual(self.ctx.title, "Test Window")
        
        # Simulated clearing
        self.ctx.clear()
        self.assertFalse(self.ctx.is_valid())

    @patch('ctypes.windll.user32.GetForegroundWindow')
    @patch('app.tools.impl.windows_gui._find_windows')
    def test_focus_verification_failure_aborts_typing(self, mock_find_windows, mock_get_fg):
        # Setup mock target window wrapper (handle 999)
        mock_win = MagicMock()
        mock_win.handle = 999
        mock_win.window_text.return_value = "Notepad"
        mock_find_windows.return_value = [mock_win]

        # Mock GetForegroundWindow to return handle 111 (e.g. Chrome Browser) instead of 999
        mock_get_fg.return_value = 111

        # Attempt to resolve target
        success, wrapper, msg, err_code = resolve_and_focus_target("Notepad")
        
        # Verify focus verification failed and execution aborted
        self.assertFalse(success)
        self.assertEqual(err_code, "FOCUS_VERIFICATION_FAILED")
        self.assertIn("could not gain active focus", msg)

    def test_no_target_context_returns_error(self):
        # Context is clear, no explicit target provided
        success, wrapper, msg, err_code = resolve_and_focus_target(None)
        self.assertFalse(success)
        self.assertEqual(err_code, "NO_TARGET_WINDOW")

    def test_fast_router_explicit_target_parsing(self):
        router = FastRouter()
        result = router.parse("type hello JARVIS into Notepad")
        self.assertIsNotNone(result)
        self.assertEqual(result[0], Intent.TYPE_TEXT)
        self.assertEqual(result[1]['text'], "hello jarvis")
        self.assertEqual(result[1]['target_window'], "notepad")

    def test_fast_router_implicit_target_parsing(self):
        router = FastRouter()
        result = router.parse("type hello JARVIS")
        self.assertIsNotNone(result)
        self.assertEqual(result[0], Intent.TYPE_TEXT)
        self.assertEqual(result[1]['text'], "hello jarvis")
        self.assertNotIn('target_window', result[1])

if __name__ == '__main__':
    unittest.main()
