import unittest
from app.orchestrator.fast_router import FastRouter, Intent

class TestFastRouterGUI(unittest.TestCase):
    def setUp(self):
        self.router = FastRouter()

    def test_list_windows(self):
        result = self.router.parse("List open windows")
        self.assertIsNotNone(result)
        self.assertEqual(result[0], Intent.LIST_WINDOWS)
        
        result2 = self.router.parse("show all windows")
        self.assertIsNotNone(result2)
        self.assertEqual(result2[0], Intent.LIST_WINDOWS)

    def test_focus_window(self):
        result = self.router.parse("Focus Notepad")
        self.assertIsNotNone(result)
        self.assertEqual(result[0], Intent.FOCUS_WINDOW)
        self.assertEqual(result[1]['window_title'], "notepad")
        
        result2 = self.router.parse("Switch to Chrome")
        self.assertIsNotNone(result2)
        self.assertEqual(result2[0], Intent.FOCUS_WINDOW)
        self.assertEqual(result2[1]['window_title'], "chrome")

    def test_minimize_maximize_restore(self):
        result = self.router.parse("Minimize Notepad")
        self.assertIsNotNone(result)
        self.assertEqual(result[0], Intent.MINIMIZE_WINDOW)
        self.assertEqual(result[1]['window_title'], "notepad")
        
        result2 = self.router.parse("Maximize edge")
        self.assertIsNotNone(result2)
        self.assertEqual(result2[0], Intent.MAXIMIZE_WINDOW)
        self.assertEqual(result2[1]['window_title'], "edge")

    def test_close_window(self):
        # NOTE: 'close chrome' routes to CLOSE_BROWSER because it is intercepted earlier.
        result = self.router.parse("Close notepad")
        self.assertIsNotNone(result)
        self.assertEqual(result[0], Intent.CLOSE_WINDOW)
        self.assertEqual(result[1]['window_title'], "notepad")

    def test_type_text(self):
        result = self.router.parse("type hello world")
        self.assertIsNotNone(result)
        self.assertEqual(result[0], Intent.TYPE_TEXT)
        self.assertEqual(result[1]['text'], "hello world")

    def test_press_key(self):
        result = self.router.parse("press enter")
        self.assertIsNotNone(result)
        self.assertEqual(result[0], Intent.PRESS_KEY)
        self.assertEqual(result[1]['keys'], "{ENTER}")
        
        result2 = self.router.parse("hit ctrl s")
        self.assertIsNotNone(result2)
        self.assertEqual(result2[0], Intent.PRESS_KEY)
        self.assertEqual(result2[1]['keys'], "^s")

if __name__ == '__main__':
    unittest.main()
