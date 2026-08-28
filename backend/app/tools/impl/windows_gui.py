import ctypes
import logging
import psutil
import time
from typing import Optional, List, Dict, Any, Tuple
from pydantic import BaseModel
import pywinauto
from pywinauto.application import Application

from app.tools.base import Tool
from app.security.permissions import PermissionLevel
from app.tools.registry import ToolRegistry
from app.tools.impl.gui_context import GUITargetContext

logger = logging.getLogger('jarvis.tools.gui')

def _find_windows(title_query: str):
    query_lower = title_query.lower()
    desktop = pywinauto.Desktop(backend="uia")
    matches = []
    for w in desktop.windows():
        try:
            t = w.window_text()
            if t and w.is_visible() and query_lower in t.lower():
                matches.append(w)
        except:
            pass
            
    if not matches:
        desktop = pywinauto.Desktop(backend="win32")
        for w in desktop.windows():
            try:
                t = w.window_text()
                if t and w.is_visible() and query_lower in t.lower():
                    matches.append(w)
            except:
                pass
    return matches


def resolve_and_focus_target(target_window_query: Optional[str] = None) -> Tuple[bool, Any, str, str]:
    """
    Resolves target window, brings it to foreground, and verifies focus via GetForegroundWindow.
    Returns (success, target_wrapper, message, error_code).
    """
    ctx = GUITargetContext.get_instance()
    target_wrapper = None

    # 1. Explicit target_window query passed
    if target_window_query:
        matches = _find_windows(target_window_query)
        if not matches:
            return False, None, f"Could not find window matching '{target_window_query}'.", "WINDOW_NOT_FOUND"
        if len(matches) > 1:
            titles = [w.window_text() for w in matches]
            return False, None, f"Ambiguous request. Multiple windows match '{target_window_query}': {', '.join(titles)}.", "AMBIGUOUS_WINDOW"
        target_wrapper = matches[0]
        ctx.set_target(target_wrapper.handle, target_wrapper.window_text())

    # 2. Contextual target lookup
    elif ctx.is_valid():
        desktop = pywinauto.Desktop(backend="uia")
        for w in desktop.windows():
            if w.handle == ctx.handle:
                target_wrapper = w
                break
        if not target_wrapper:
            desktop = pywinauto.Desktop(backend="win32")
            for w in desktop.windows():
                if w.handle == ctx.handle:
                    target_wrapper = w
                    break
        if not target_wrapper:
            ctx.clear()

    if not target_wrapper:
        return False, None, "No active target application window context found. Please specify a target window (e.g. 'Type hello into Notepad') or open an application first.", "NO_TARGET_WINDOW"

    # 3. Explicitly focus target window
    try:
        target_wrapper.set_focus()
        time.sleep(0.1) # brief cushion for OS window focus transition
    except Exception as e:
        logger.warning(f"set_focus failed: {e}. Falling back to win32 SetForegroundWindow.")
        try:
            user32 = ctypes.windll.user32
            user32.SetForegroundWindow(target_wrapper.handle)
            time.sleep(0.1)
        except Exception as e2:
            logger.error(f"SetForegroundWindow failed: {e2}")

    # 4. FOCUS VERIFICATION via GetForegroundWindow
    try:
        user32 = ctypes.windll.user32
        fg_hwnd = user32.GetForegroundWindow()
        
        # Check direct handle match or root window match
        root_fg = user32.GetAncestor(fg_hwnd, 2) # GA_ROOT = 2
        
        if fg_hwnd != target_wrapper.handle and root_fg != target_wrapper.handle:
            # Get title of whatever window has foreground currently
            length = user32.GetWindowTextLengthW(fg_hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(fg_hwnd, buf, length + 1)
            current_fg_title = buf.value or "Unknown"
            
            logger.error(f"FOCUS VERIFICATION FAILED! Active window is '{current_fg_title}' ({fg_hwnd}), but target is '{target_wrapper.window_text()}' ({target_wrapper.handle}). ABORTING TYPING.")
            return False, None, f"Focus verification failed. Target window '{target_wrapper.window_text()}' could not gain active focus (Active: '{current_fg_title}'). Typing aborted to prevent typing into wrong app.", "FOCUS_VERIFICATION_FAILED"
    except Exception as ver_err:
        logger.error(f"Focus verification error: {ver_err}")

    return True, target_wrapper, "Success", ""


# ============================================================================
# WINDOW MANAGEMENT TOOLS
# ============================================================================

class ListWindowsTool(Tool):
    name = "list_windows"
    description = "Lists open and visible application windows on the desktop."
    input_schema = type("EmptyInput", (BaseModel,), {})
    permission_level = PermissionLevel.SAFE

    async def execute(self) -> dict:
        try:
            desktop = pywinauto.Desktop(backend="uia")
            windows = desktop.windows()
            
            visible_windows = []
            for w in windows:
                try:
                    title = w.window_text()
                    if title and w.is_visible():
                        visible_windows.append(title)
                except Exception:
                    pass
                    
            if not visible_windows:
                desktop_win32 = pywinauto.Desktop(backend="win32")
                for w in desktop_win32.windows():
                    try:
                        title = w.window_text()
                        if title and w.is_visible() and title not in visible_windows:
                            visible_windows.append(title)
                    except Exception:
                        pass
                        
            return {
                "success": True,
                "tool": self.name,
                "message": f"Found {len(visible_windows)} open windows.",
                "data": {"windows": visible_windows, "target_context": GUITargetContext.get_instance().to_dict()},
                "error": None
            }
        except Exception as e:
            logger.error(f"List windows failed: {e}")
            return {
                "success": False,
                "tool": self.name,
                "message": "Failed to list windows.",
                "data": {},
                "error": str(e)
            }


class WindowTargetInput(BaseModel):
    window_title: str

class FocusWindowTool(Tool):
    name = "focus_window"
    description = "Brings a specified window to the foreground."
    input_schema = WindowTargetInput
    permission_level = PermissionLevel.SAFE

    async def execute(self, window_title: str) -> dict:
        success, target_wrapper, msg, err = resolve_and_focus_target(window_title)
        if not success:
            return {
                "success": False,
                "tool": self.name,
                "message": msg,
                "data": {},
                "error": err
            }
            
        GUITargetContext.get_instance().set_target(target_wrapper.handle, target_wrapper.window_text())
        return {
            "success": True,
            "tool": self.name,
            "message": f"Focused window '{target_wrapper.window_text()}'.",
            "data": {"title": target_wrapper.window_text(), "handle": target_wrapper.handle},
            "error": None
        }


class MinimizeWindowTool(Tool):
    name = "minimize_window"
    description = "Minimizes a specified window."
    input_schema = WindowTargetInput
    permission_level = PermissionLevel.SAFE
    
    async def execute(self, window_title: str) -> dict:
        matches = _find_windows(window_title)
        if not matches:
            return {"success": False, "tool": self.name, "message": f"Window not found: {window_title}", "error": "WINDOW_NOT_FOUND"}
        if len(matches) > 1:
            return {"success": False, "tool": self.name, "message": "Ambiguous window.", "error": "AMBIGUOUS_WINDOW"}
            
        try:
            matches[0].minimize()
            return {"success": True, "tool": self.name, "message": f"Minimized '{matches[0].window_text()}'.", "data": {}, "error": None}
        except Exception as e:
            return {"success": False, "tool": self.name, "message": "Failed.", "error": str(e)}


class MaximizeWindowTool(Tool):
    name = "maximize_window"
    description = "Maximizes a specified window."
    input_schema = WindowTargetInput
    permission_level = PermissionLevel.SAFE
    
    async def execute(self, window_title: str) -> dict:
        matches = _find_windows(window_title)
        if not matches: return {"success": False, "tool": self.name, "message": f"Window not found: {window_title}", "error": "WINDOW_NOT_FOUND"}
        if len(matches) > 1: return {"success": False, "tool": self.name, "message": "Ambiguous window.", "error": "AMBIGUOUS_WINDOW"}
            
        try:
            matches[0].maximize()
            return {"success": True, "tool": self.name, "message": f"Maximized '{matches[0].window_text()}'.", "data": {}, "error": None}
        except Exception as e:
            return {"success": False, "tool": self.name, "message": "Failed.", "error": str(e)}


class RestoreWindowTool(Tool):
    name = "restore_window"
    description = "Restores a specified window."
    input_schema = WindowTargetInput
    permission_level = PermissionLevel.SAFE
    
    async def execute(self, window_title: str) -> dict:
        matches = _find_windows(window_title)
        if not matches: return {"success": False, "tool": self.name, "message": f"Window not found: {window_title}", "error": "WINDOW_NOT_FOUND"}
        if len(matches) > 1: return {"success": False, "tool": self.name, "message": "Ambiguous window.", "error": "AMBIGUOUS_WINDOW"}
            
        try:
            matches[0].restore()
            GUITargetContext.get_instance().set_target(matches[0].handle, matches[0].window_text())
            return {"success": True, "tool": self.name, "message": f"Restored '{matches[0].window_text()}'.", "data": {}, "error": None}
        except Exception as e:
            return {"success": False, "tool": self.name, "message": "Failed.", "error": str(e)}


class CloseWindowTool(Tool):
    name = "close_window"
    description = "Closes a specified window."
    input_schema = WindowTargetInput
    permission_level = PermissionLevel.CONFIRMATION_REQUIRED
    
    async def execute(self, window_title: str) -> dict:
        matches = _find_windows(window_title)
        if not matches: return {"success": False, "tool": self.name, "message": f"Window not found: {window_title}", "error": "WINDOW_NOT_FOUND"}
        if len(matches) > 1: return {"success": False, "tool": self.name, "message": "Ambiguous window.", "error": "AMBIGUOUS_WINDOW"}
            
        try:
            target = matches[0]
            target.close()
            ctx = GUITargetContext.get_instance()
            if ctx.handle == target.handle:
                ctx.clear()
            return {"success": True, "tool": self.name, "message": f"Closed '{target.window_text()}'.", "data": {}, "error": None}
        except Exception as e:
            return {"success": False, "tool": self.name, "message": "Failed.", "error": str(e)}


# ============================================================================
# KEYBOARD & TEXT TOOLS
# ============================================================================

def escape_pywinauto_keys(text: str) -> str:
    chars = []
    for c in text:
        if c in ("{", "}", "^", "%", "+", "~"):
            chars.append(f"{{{c}}}")
        else:
            chars.append(c)
    return "".join(chars)

class TypeTextInput(BaseModel):
    text: str
    target_window: Optional[str] = None
    new_line: Optional[bool] = False

class TypeTextTool(Tool):
    name = "type_text"
    description = "Safely types text into the targeted application window after focus verification."
    input_schema = TypeTextInput
    permission_level = PermissionLevel.CONFIRMATION_REQUIRED

    async def execute(self, text: str, target_window: Optional[str] = None, new_line: Optional[bool] = False) -> dict:
        clean_text = text.strip('\'"')
        if len(clean_text) > 1000:
            return {
                "success": False,
                "tool": self.name,
                "message": "Text is too long (limit 1000 chars).",
                "data": {},
                "error": "PAYLOAD_TOO_LARGE"
            }
            
        success, target_wrapper, msg, err = resolve_and_focus_target(target_window)
        if not success:
            return {
                "success": False,
                "tool": self.name,
                "message": msg,
                "data": {},
                "error": err
            }
            
        try:
            if new_line:
                pywinauto.keyboard.send_keys("{ENTER}", pause=0.03)
                time.sleep(0.05)
                
            escaped_text = escape_pywinauto_keys(clean_text)
            pywinauto.keyboard.send_keys(escaped_text, with_spaces=True, with_newlines=True, with_tabs=True, pause=0.03)
            return {
                "success": True,
                "tool": self.name,
                "message": f"Typed text into '{target_wrapper.window_text()}'.",
                "data": {"length": len(clean_text), "target": target_wrapper.window_text()},
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "tool": self.name,
                "message": f"Failed to type text: {e}",
                "data": {},
                "error": str(e)
            }


class PressKeyInput(BaseModel):
    keys: str
    target_window: Optional[str] = None

class PressKeyTool(Tool):
    name = "press_key"
    description = "Presses specific keys or combinations on the targeted application window."
    input_schema = PressKeyInput
    permission_level = PermissionLevel.CONFIRMATION_REQUIRED

    ALLOWED_KEYS = [
        "{ENTER}", "{TAB}", "{ESC}", "{BACKSPACE}", "{SPACE}",
        "{UP}", "{DOWN}", "{LEFT}", "{RIGHT}",
        "^s", "^c", "^v", "^x", "^z", "%{TAB}"
    ]

    async def execute(self, keys: str, target_window: Optional[str] = None) -> dict:
        if keys not in self.ALLOWED_KEYS and not keys.isalnum():
            return {
                "success": False,
                "tool": self.name,
                "message": f"Key combination '{keys}' is not permitted for safety.",
                "data": {},
                "error": "UNAUTHORIZED_KEY"
            }

        success, target_wrapper, msg, err = resolve_and_focus_target(target_window)
        if not success:
            return {
                "success": False,
                "tool": self.name,
                "message": msg,
                "data": {},
                "error": err
            }

        try:
            pywinauto.keyboard.send_keys(keys)
            return {
                "success": True,
                "tool": self.name,
                "message": f"Pressed key '{keys}' on '{target_wrapper.window_text()}'.",
                "data": {"target": target_wrapper.window_text()},
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "tool": self.name,
                "message": "Failed to press key.",
                "data": {},
                "error": str(e)
            }


# ============================================================================
# MOUSE CONTROL TOOLS
# ============================================================================

class MouseInput(BaseModel):
    x: int
    y: int

class MoveMouseTool(Tool):
    name = "move_mouse"
    description = "Moves the mouse cursor to absolute screen coordinates."
    input_schema = MouseInput
    permission_level = PermissionLevel.SAFE

    async def execute(self, x: int, y: int) -> dict:
        try:
            pywinauto.mouse.move(coords=(x, y))
            return {"success": True, "tool": self.name, "message": f"Moved mouse to ({x},{y}).", "data": {}, "error": None}
        except Exception as e:
            return {"success": False, "tool": self.name, "message": "Failed to move mouse.", "data": {}, "error": str(e)}

class ClickMouseTool(Tool):
    name = "click_mouse"
    description = "Clicks the left mouse button at absolute screen coordinates."
    input_schema = MouseInput
    permission_level = PermissionLevel.CONFIRMATION_REQUIRED

    async def execute(self, x: int, y: int) -> dict:
        try:
            pywinauto.mouse.click(button='left', coords=(x, y))
            return {"success": True, "tool": self.name, "message": f"Clicked mouse at ({x},{y}).", "data": {}, "error": None}
        except Exception as e:
            return {"success": False, "tool": self.name, "message": "Failed to click mouse.", "data": {}, "error": str(e)}


# Register all GUI tools
ToolRegistry.register(ListWindowsTool())
ToolRegistry.register(FocusWindowTool())
ToolRegistry.register(MinimizeWindowTool())
ToolRegistry.register(MaximizeWindowTool())
ToolRegistry.register(RestoreWindowTool())
ToolRegistry.register(CloseWindowTool())
ToolRegistry.register(TypeTextTool())
ToolRegistry.register(PressKeyTool())
ToolRegistry.register(MoveMouseTool())
ToolRegistry.register(ClickMouseTool())
