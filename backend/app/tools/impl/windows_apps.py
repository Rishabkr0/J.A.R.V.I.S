import os
import subprocess
import logging
from typing import Any
from pydantic import BaseModel
from app.tools.base import Tool
from app.security.permissions import PermissionLevel
from app.tools.registry import ToolRegistry

logger = logging.getLogger('jarvis.tools.apps')

class OpenAppInput(BaseModel):
    app_name: str

class OpenAppTool(Tool):
    name = "open_application"
    description = "Opens a known Windows application."
    input_schema = OpenAppInput
    permission_level = PermissionLevel.SAFE

    # Hardcoded known safe executables to prevent arbitrary command execution
    KNOWN_APPS = {
        "chrome": "chrome.exe",
        "edge": "msedge.exe",
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "explorer": "explorer.exe",
        "terminal": "wt.exe",
        "file explorer": "explorer.exe",
        "cmd": "cmd.exe"
    }

    def _find_executable(self, exe_name: str) -> str | None:
        import shutil
        import winreg
        import os
        
        # 1. Check PATH
        path = shutil.which(exe_name)
        if path:
            return path
        
        # 2. Check App Paths in Registry
        for hkey in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            try:
                key = winreg.OpenKey(hkey, rf'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{exe_name}')
                path, _ = winreg.QueryValueEx(key, '')
                if os.path.exists(path):
                    return path
            except Exception:
                continue
                
        return None

    async def execute(self, app_name: str) -> dict:
        normalized_name = app_name.lower().strip()
        exe = self.KNOWN_APPS.get(normalized_name)
        
        if not exe:
            return {
                "success": False,
                "tool": self.name,
                "message": f"Application '{app_name}' is not in the safe allowed list.",
                "data": {},
                "error": "APPLICATION_NOT_FOUND"
            }
        
        try:
            logger.info(f"[5] Resolving path for {exe}")
            resolved_path = self._find_executable(exe)
            
            if not resolved_path:
                logger.error(f"Could not find executable for {exe} in PATH or Registry.")
                return {
                    "success": False,
                    "tool": self.name,
                    "message": f"Could not locate '{app_name}' on this system.",
                    "data": {},
                    "error": "EXECUTABLE_NOT_FOUND"
                }
                
            logger.info(f"[6] Windows launch operation started via os.startfile: {resolved_path}")
            try:
                os.startfile(resolved_path)
            except Exception:
                subprocess.Popen([resolved_path])
            logger.info("[7] Windows launch operation returned successfully")
            
            # Register Target Context
            import asyncio
            import pywinauto
            from app.tools.impl.gui_context import GUITargetContext
            
            await asyncio.sleep(0.5)
            try:
                desktop = pywinauto.Desktop(backend="uia")
                for w in desktop.windows():
                    t = w.window_text()
                    if t and w.is_visible() and normalized_name in t.lower():
                        GUITargetContext.get_instance().set_target(w.handle, t, exe)
                        break
            except Exception as ctx_err:
                logger.warning(f"Could not automatically register target context for {app_name}: {ctx_err}")

            return {
                "success": True,
                "tool": self.name,
                "message": f"Opened {app_name}.",
                "data": {
                    "executable": exe,
                    "resolved_path": resolved_path,
                    "target_context": GUITargetContext.get_instance().to_dict()
                },
                "error": None
            }
        except Exception as e:
            logger.error(f"Failed to open {exe}: {e}")
            return {
                "success": False,
                "tool": self.name,
                "message": f"Failed to open {app_name}.",
                "data": {},
                "error": str(e)
            }

ToolRegistry.register(OpenAppTool())
