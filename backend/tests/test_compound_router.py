import unittest
from app.orchestrator.fast_router import FastRouter, Intent

class TestCompoundRouter(unittest.TestCase):
    def setUp(self):
        self.router = FastRouter()

    def test_single_command(self):
        res = self.router.parse_compound("open chrome")
        self.assertIsNotNone(res)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][0], Intent.OPEN_BROWSER)

    def test_compound_and_command(self):
        res = self.router.parse_compound("open chrome and search for black holes")
        self.assertIsNotNone(res)
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0][0], Intent.OPEN_BROWSER)
        self.assertEqual(res[1][0], Intent.SEARCH_BROWSER)
        self.assertEqual(res[1][1]['query'], "black holes")

    def test_compound_then_command(self):
        res = self.router.parse_compound("open notepad and then type hello world")
        self.assertIsNotNone(res)
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0][0], Intent.OPEN_APP)
        self.assertEqual(res[0][1]['app_name'], "notepad")
        self.assertEqual(res[1][0], Intent.TYPE_TEXT)
        self.assertEqual(res[1][1]['text'], "hello world")

    def test_unroutable_compound_falls_back(self):
        # If one part is a general LLM question, parse_compound returns None for Gemini fallback
        res = self.router.parse_compound("open chrome and what is the meaning of life")
        self.assertIsNone(res)

if __name__ == '__main__':
    unittest.main()
