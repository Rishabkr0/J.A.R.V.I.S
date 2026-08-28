from typing import Any, Dict
from pydantic import BaseModel
from app.tools.base import Tool
from app.security.permissions import PermissionLevel
from app.browser.manager import BrowserManager
from app.events.bus import EventBus

# Shared browser manager instance
manager = BrowserManager()
bus = EventBus()

async def emit_status(status=None):
    if status is None:
        status = manager.get_status()
    bus.publish({'type': 'browser_status', 'status': status})


class OpenBrowserSchema(BaseModel):
    pass

class OpenBrowserTool(Tool):
    name = "open_browser"
    description = "Opens the web browser."
    input_schema = OpenBrowserSchema
    permission_level = PermissionLevel.SAFE

    async def execute(self, **kwargs) -> Dict[str, Any]:
        await emit_status("STARTING")
        success = await manager.ensure_running()
        await emit_status()
        if success:
            return {"success": True, "message": "Browser opened successfully.", "data": {}}
        return {"success": False, "message": "Failed to open browser.", "data": {}}


class NavigateBrowserSchema(BaseModel):
    url: str

class NavigateBrowserTool(Tool):
    name = "navigate_browser"
    description = "Navigates the browser to a specific URL."
    input_schema = NavigateBrowserSchema
    permission_level = PermissionLevel.SAFE

    async def execute(self, url: str, **kwargs) -> Dict[str, Any]:
        await emit_status("NAVIGATING")
        result = await manager.navigate(url)
        await emit_status()
        return {"success": result['success'], "message": result['message'], "data": {}}


class SearchBrowserSchema(BaseModel):
    query: str

class SearchBrowserTool(Tool):
    name = "search_browser"
    description = "Searches the web using the browser."
    input_schema = SearchBrowserSchema
    permission_level = PermissionLevel.SAFE

    async def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        await emit_status("SEARCHING")
        result = await manager.search(query)
        await emit_status()
        return {"success": result['success'], "message": result['message'], "data": {}}


class GoBackSchema(BaseModel):
    pass

class GoBackTool(Tool):
    name = "go_back"
    description = "Navigates back to the previous page."
    input_schema = GoBackSchema
    permission_level = PermissionLevel.SAFE

    async def execute(self, **kwargs) -> Dict[str, Any]:
        await emit_status("NAVIGATING")
        result = await manager.go_back()
        await emit_status()
        return {"success": result['success'], "message": result['message'], "data": {}}


class GoForwardSchema(BaseModel):
    pass

class GoForwardTool(Tool):
    name = "go_forward"
    description = "Navigates forward to the next page."
    input_schema = GoForwardSchema
    permission_level = PermissionLevel.SAFE

    async def execute(self, **kwargs) -> Dict[str, Any]:
        await emit_status("NAVIGATING")
        result = await manager.go_forward()
        await emit_status()
        return {"success": result['success'], "message": result['message'], "data": {}}


class RefreshBrowserSchema(BaseModel):
    pass

class RefreshBrowserTool(Tool):
    name = "refresh_browser"
    description = "Refreshes the current page."
    input_schema = RefreshBrowserSchema
    permission_level = PermissionLevel.SAFE

    async def execute(self, **kwargs) -> Dict[str, Any]:
        await emit_status("REFRESHING")
        result = await manager.refresh()
        await emit_status()
        return {"success": result['success'], "message": result['message'], "data": {}}


class CloseBrowserSchema(BaseModel):
    pass

class CloseBrowserTool(Tool):
    name = "close_browser"
    description = "Closes the browser."
    input_schema = CloseBrowserSchema
    permission_level = PermissionLevel.SAFE

    async def execute(self, **kwargs) -> Dict[str, Any]:
        await manager.stop()
        await emit_status()
        return {"success": True, "message": "Browser closed.", "data": {}}


class GetBrowserStatusSchema(BaseModel):
    pass

class GetBrowserStatusTool(Tool):
    name = "get_browser_status"
    description = "Gets the current status of the browser."
    input_schema = GetBrowserStatusSchema
    permission_level = PermissionLevel.SAFE

    async def execute(self, **kwargs) -> Dict[str, Any]:
        status = manager.get_status()
        return {"success": True, "message": f"Browser status is: {status}", "data": {"status": status}}

# Register tools
from app.tools.registry import ToolRegistry

ToolRegistry.register(OpenBrowserTool())
ToolRegistry.register(NavigateBrowserTool())
ToolRegistry.register(SearchBrowserTool())
ToolRegistry.register(GoBackTool())
ToolRegistry.register(GoForwardTool())
ToolRegistry.register(RefreshBrowserTool())
ToolRegistry.register(CloseBrowserTool())
ToolRegistry.register(GetBrowserStatusTool())
