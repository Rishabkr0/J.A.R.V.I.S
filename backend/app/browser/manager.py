import sys
import asyncio
import threading
import logging
from urllib.parse import urlparse, quote_plus
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Playwright, Browser, BrowserContext, Page, Error as PlaywrightError

logger = logging.getLogger("jarvis.browser.manager")

class BrowserManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BrowserManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.is_running = False
        self._initialized = True
        
        # Dedicated thread & event loop for Playwright on Windows (Proactor loop)
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._start_background_loop()

    def _start_background_loop(self):
        def run_loop():
            if sys.platform == 'win32':
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_forever()

        self._thread = threading.Thread(target=run_loop, daemon=True)
        self._thread.start()
        
        # Wait briefly for loop to initialize
        while self._loop is None or not self._loop.is_running():
            pass

    async def _run_async(self, coro):
        """Helper to run a coroutine safely inside our dedicated Proactor loop."""
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return await asyncio.wrap_future(future)

    # ----------------------------------------------------
    # Public Async Methods (called from Uvicorn context)
    # ----------------------------------------------------

    async def start(self) -> bool:
        return await self._run_async(self._impl_start())

    async def stop(self):
        return await self._run_async(self._impl_stop())

    async def ensure_running(self) -> bool:
        return await self._run_async(self._impl_ensure_running())

    async def navigate(self, url: str) -> Dict[str, Any]:
        return await self._run_async(self._impl_navigate(url))

    async def search(self, query: str) -> Dict[str, Any]:
        return await self._run_async(self._impl_search(query))

    async def go_back(self) -> Dict[str, Any]:
        return await self._run_async(self._impl_go_back())

    async def go_forward(self) -> Dict[str, Any]:
        return await self._run_async(self._impl_go_forward())

    async def refresh(self) -> Dict[str, Any]:
        return await self._run_async(self._impl_refresh())

    def get_status(self) -> str:
        if not self.is_running:
            return "OFFLINE"
        if not self.page or self.page.is_closed():
            return "ERROR"
        return "READY"

    # ----------------------------------------------------
    # Internal Async Implementation (runs inside Proactor thread)
    # ----------------------------------------------------

    async def _impl_start(self) -> bool:
        if self.is_running and self.page and not self.page.is_closed():
            return True
            
        try:
            if not self.playwright:
                self.playwright = await async_playwright().start()
            
            if not self.browser:
                self.browser = await self.playwright.chromium.launch(
                    headless=False
                )
                logger.info("Launched Chromium via Playwright (Proactor Thread).")
            
            if not self.context:
                self.context = await self.browser.new_context(
                    viewport={'width': 1280, 'height': 800}
                )
            
            if not self.page or self.page.is_closed():
                self.page = await self.context.new_page()
                
            self.is_running = True
            logger.info("BrowserManager started successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to start browser: {e}", exc_info=True)
            await self._impl_stop()
            return False

    async def _impl_stop(self):
        try:
            if self.page:
                await self.page.close()
        except: pass
        
        try:
            if self.context:
                await self.context.close()
        except: pass
        
        try:
            if self.browser:
                await self.browser.close()
        except: pass
        
        try:
            if self.playwright:
                await self.playwright.stop()
        except: pass

        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None
        self.is_running = False
        logger.info("BrowserManager stopped.")

    async def _impl_ensure_running(self) -> bool:
        if not self.is_running or not self.page or self.page.is_closed():
            logger.info("Browser not running or page closed, starting new session...")
            return await self._impl_start()
        return True

    def _validate_url(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            if not parsed.scheme and '.' in parsed.path:
                return True
            return parsed.scheme in ['http', 'https']
        except Exception:
            return False

    def _format_url(self, url: str) -> str:
        parsed = urlparse(url)
        if not parsed.scheme:
            return f"https://{url}"
        return url

    async def _impl_navigate(self, url: str) -> Dict[str, Any]:
        if not self._validate_url(url):
            return {"success": False, "message": f"Invalid or unsafe URL scheme: {url}"}
            
        formatted_url = self._format_url(url)
        
        if not await self._impl_ensure_running():
            return {"success": False, "message": "Failed to start browser session."}
            
        try:
            await self.page.goto(formatted_url, timeout=15000, wait_until='domcontentloaded')
            title = await self.page.title()
            return {"success": True, "message": f"Navigated to {title}"}
        except PlaywrightError as e:
            return {"success": False, "message": f"Navigation failed: {str(e)}"}
        except Exception as e:
            return {"success": False, "message": f"Unexpected error: {str(e)}"}

    async def _impl_search(self, query: str) -> Dict[str, Any]:
        encoded_query = quote_plus(query)
        search_url = f"https://www.google.com/search?q={encoded_query}"
        return await self._impl_navigate(search_url)

    async def _impl_go_back(self) -> Dict[str, Any]:
        if not self.is_running or not self.page:
            return {"success": False, "message": "Browser is not currently running."}
        try:
            resp = await self.page.go_back(timeout=10000)
            if resp:
                return {"success": True, "message": "Navigated back."}
            return {"success": False, "message": "No history to go back to."}
        except Exception as e:
            return {"success": False, "message": f"Failed to go back: {str(e)}"}

    async def _impl_go_forward(self) -> Dict[str, Any]:
        if not self.is_running or not self.page:
            return {"success": False, "message": "Browser is not currently running."}
        try:
            resp = await self.page.go_forward(timeout=10000)
            if resp:
                return {"success": True, "message": "Navigated forward."}
            return {"success": False, "message": "No history to go forward to."}
        except Exception as e:
            return {"success": False, "message": f"Failed to go forward: {str(e)}"}

    async def _impl_refresh(self) -> Dict[str, Any]:
        if not self.is_running or not self.page:
            return {"success": False, "message": "Browser is not currently running."}
        try:
            await self.page.reload(timeout=15000)
            return {"success": True, "message": "Page refreshed."}
        except Exception as e:
            return {"success": False, "message": f"Failed to refresh page: {str(e)}"}
