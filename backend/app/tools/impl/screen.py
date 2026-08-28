import logging
import asyncio
from typing import Optional, Dict, Any
from pydantic import BaseModel
from app.tools.base import Tool
from app.security.permissions import PermissionLevel
from app.screen.manager import ScreenManager
from app.tools.registry import ToolRegistry

logger = logging.getLogger("jarvis.tools.screen")
screen_manager = ScreenManager()

# ============================================================================
# INPUT SCHEMAS
# ============================================================================

class CaptureScreenInput(BaseModel):
    save: Optional[bool] = False

class EmptyInput(BaseModel):
    pass

# ============================================================================
# TOOLS
# ============================================================================

class CaptureScreenTool(Tool):
    name = "capture_screen"
    description = "Captures a screenshot of the local screen to memory (or disk if save=True)."
    input_schema = CaptureScreenInput
    permission_level = PermissionLevel.SAFE

    async def execute(self, save: bool = False, **kwargs) -> dict:
        result = await asyncio.to_thread(screen_manager.capture_screenshot, save_to_disk=save)
        if not result or "error" in result:
            err_msg = result.get('error', 'Unknown capture failure') if result else 'Unknown error'
            return {
                "success": False,
                "tool": self.name,
                "message": f"Failed to capture screen: {err_msg}",
                "data": {},
                "error": err_msg
            }
        
        msg = f"Screen captured successfully. Resolution: {result.get('size')}."
        if save and "saved_path" in result:
            msg += f" Saved locally to: {result['saved_path']}"
            
        return {
            "success": True,
            "tool": self.name,
            "message": msg,
            "data": {"size": result.get("size"), "saved_path": result.get("saved_path")},
            "error": None
        }

class GetActiveWindowTool(Tool):
    name = "get_active_window"
    description = "Returns active window title and process without OCR."
    input_schema = EmptyInput
    permission_level = PermissionLevel.SAFE

    async def execute(self, **kwargs) -> dict:
        state = await asyncio.to_thread(screen_manager.get_active_window_fast)
        if "error" in state:
            return {
                "success": False,
                "tool": self.name,
                "message": f"Could not get active window: {state['error']}",
                "data": {},
                "error": state["error"]
            }
            
        msg = f"Active Window: '{state.get('title')}' (Process: {state.get('process')}, PID: {state.get('pid')})\nBounds: {state.get('rect')}"
        return {
            "success": True,
            "tool": self.name,
            "message": msg,
            "data": state,
            "error": None
        }

class GetScreenStateTool(Tool):
    name = "get_screen_state"
    description = "Returns structured info about screen, monitors, and UI automation controls."
    input_schema = EmptyInput
    permission_level = PermissionLevel.SAFE

    async def execute(self, **kwargs) -> dict:
        monitors = await asyncio.to_thread(screen_manager.get_monitor_info)
        
        try:
            uia = await asyncio.wait_for(asyncio.to_thread(screen_manager.get_active_window_uia), timeout=2.5)
        except asyncio.TimeoutError:
            logger.warning("UIA scan timed out; falling back to fast window retrieval.")
            uia = await asyncio.to_thread(screen_manager.get_active_window_fast)
        
        lines = []
        lines.append(f"Monitors: {monitors.get('count', 0)}")
        if "error" not in uia:
            lines.append(f"Active Window: '{uia.get('title')}' (Process: {uia.get('process')})")
            controls = uia.get("controls", [])
            if controls:
                lines.append(f"Visible UI Controls ({len(controls)}):")
                for c in controls[:20]:
                    lines.append(f"  - [{c['type']}] {c['text']} @ {c['rect']}")
                if len(controls) > 20:
                    lines.append(f"  ... (and {len(controls) - 20} more)")
            else:
                lines.append("No UIA child controls detected for this window.")
        else:
            lines.append(f"UIA Error: {uia['error']}")
            
        msg = "\n".join(lines)
        return {
            "success": True,
            "tool": self.name,
            "message": msg,
            "data": {"monitors": monitors, "window": uia},
            "error": None
        }

class GetVisibleTextTool(Tool):
    name = "get_visible_text"
    description = "Runs native Windows OCR on the screen screenshot to extract visible text."
    input_schema = EmptyInput
    permission_level = PermissionLevel.SAFE

    async def execute(self, **kwargs) -> dict:
        shot = await asyncio.to_thread(screen_manager.capture_screenshot)
        if not shot or "error" in shot:
            err_msg = shot.get('error') if shot else 'Unknown error'
            return {
                "success": False,
                "tool": self.name,
                "message": f"Failed to capture screen for OCR: {err_msg}",
                "data": {},
                "error": err_msg
            }
            
        try:
            ocr = await asyncio.wait_for(screen_manager.get_ocr_text(shot["bytes"]), timeout=3.0)
        except asyncio.TimeoutError:
            return {
                "success": False,
                "tool": self.name,
                "message": "OCR processing timed out.",
                "data": {},
                "error": "TIMEOUT"
            }
            
        if "error" in ocr:
            return {
                "success": False,
                "tool": self.name,
                "message": f"OCR Error: {ocr['error']}",
                "data": {},
                "error": ocr["error"]
            }
            
        lines = ocr.get("lines", [])
        if not lines:
            msg = "No visible text detected on screen."
        else:
            msg = "Visible Text:\n" + "\n".join(lines)
            
        return {
            "success": True,
            "tool": self.name,
            "message": msg,
            "data": {"count": len(lines)},
            "error": None
        }

ToolRegistry.register(CaptureScreenTool())
ToolRegistry.register(GetActiveWindowTool())
ToolRegistry.register(GetScreenStateTool())
ToolRegistry.register(GetVisibleTextTool())
