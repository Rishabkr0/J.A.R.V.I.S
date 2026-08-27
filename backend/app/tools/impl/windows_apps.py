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
            # os.startfile is Windows only, safe for known executables in PATH
            os.startfile(exe)
            return {
                "success": True,
                "tool": self.name,
                "message": f"Opened {app_name}.",
                "data": {"executable": exe},
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
