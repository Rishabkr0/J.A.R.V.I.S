import unittest
import asyncio
from app.browser.manager import BrowserManager

class TestBrowserManager(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.manager = BrowserManager()
        # Reset state just in case due to singleton
        await self.manager.stop()

    async def asyncTearDown(self):
        await self.manager.stop()

    async def test_startup_and_status(self):
        self.assertEqual(self.manager.get_status(), "OFFLINE")
        
        success = await self.manager.start()
        self.assertTrue(success)
        self.assertEqual(self.manager.get_status(), "READY")

    async def test_navigation_validation(self):
        # Invalid URLs
        res = await self.manager.navigate("file:///C:/secrets.txt")
        self.assertFalse(res['success'])
        
        res = await self.manager.navigate("javascript:alert(1)")
        self.assertFalse(res['success'])
        
        # Valid URLs format check (doesn't need to actually load if we mock, but let's test a fast domain)
        res = await self.manager.navigate("example.com")
        self.assertTrue(res['success'])

    async def test_search(self):
        res = await self.manager.search("black holes")
        self.assertTrue(res['success'])
        self.assertIn("Navigated to", res['message'])

    async def test_lifecycle(self):
        await self.manager.start()
        self.assertEqual(self.manager.get_status(), "READY")
        await self.manager.stop()
        self.assertEqual(self.manager.get_status(), "OFFLINE")
        
        # ensure_running should restart it
        await self.manager.ensure_running()
        self.assertEqual(self.manager.get_status(), "READY")

if __name__ == '__main__':
    unittest.main()
