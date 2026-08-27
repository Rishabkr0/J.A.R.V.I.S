import os
import pathlib

base = pathlib.Path(r'c:\Users\Rishab\Documents\J.A.R.V.I.S\backend')

files = {
    'app/tools/registry.py': '''import logging
from typing import Dict, Any, Optional, Type
from app.tools.base import Tool

logger = logging.getLogger('jarvis.tools.registry')

class ToolRegistry:
    _tools: Dict[str, Tool] = {}

    @classmethod
    def register(cls, tool_instance: Tool):
        cls._tools[tool_instance.name] = tool_instance
        logger.info(f"Registered tool: {tool_instance.name}")

    @classmethod
    def get_tool(cls, name: str) -> Optional[Tool]:
        return cls._tools.get(name)

    @classmethod
    def get_all(cls) -> Dict[str, Tool]:
        return cls._tools
''',
    'app/tools/impl/__init__.py': '',
    'app/tools/impl/windows_apps.py': '''import os
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
''',
    'app/tools/impl/windows_url.py': '''import webbrowser
import urllib.parse
from pydantic import BaseModel
from app.tools.base import Tool
from app.security.permissions import PermissionLevel
from app.tools.registry import ToolRegistry

class OpenUrlInput(BaseModel):
    url: str

class OpenUrlTool(Tool):
    name = "open_url"
    description = "Opens a URL safely in the default browser."
    input_schema = OpenUrlInput
    permission_level = PermissionLevel.SAFE

    async def execute(self, url: str) -> dict:
        url = url.strip()
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'https://' + url
            
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ['http', 'https']:
            return {
                "success": False,
                "tool": self.name,
                "message": "Invalid URL scheme. Only http and https are allowed.",
                "data": {},
                "error": "INVALID_URL_SCHEME"
            }
            
        try:
            webbrowser.open(url)
            return {
                "success": True,
                "tool": self.name,
                "message": f"Opened {url}.",
                "data": {"url": url},
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "tool": self.name,
                "message": f"Failed to open URL.",
                "data": {},
                "error": str(e)
            }

ToolRegistry.register(OpenUrlTool())
''',
    'app/tools/impl/windows_volume.py': '''import ctypes
from pydantic import BaseModel
from app.tools.base import Tool
from app.security.permissions import PermissionLevel
from app.tools.registry import ToolRegistry

class VolumeInput(BaseModel):
    action: str # up, down, mute

class SetVolumeTool(Tool):
    name = "set_volume"
    description = "Adjusts Windows volume or mutes."
    input_schema = VolumeInput
    permission_level = PermissionLevel.SAFE

    VK_VOLUME_MUTE = 0xAD
    VK_VOLUME_DOWN = 0xAE
    VK_VOLUME_UP = 0xAF

    async def execute(self, action: str) -> dict:
        try:
            # We simulate pressing the media keys.
            # 5 steps for up/down so it's noticeable (usually 1 step = 2%)
            steps = 5 if action in ['up', 'down'] else 1
            
            for _ in range(steps):
                if action == 'mute':
                    ctypes.windll.user32.keybd_event(self.VK_VOLUME_MUTE, 0, 0, 0)
                    ctypes.windll.user32.keybd_event(self.VK_VOLUME_MUTE, 0, 2, 0) # keyup
                elif action == 'up':
                    ctypes.windll.user32.keybd_event(self.VK_VOLUME_UP, 0, 0, 0)
                    ctypes.windll.user32.keybd_event(self.VK_VOLUME_UP, 0, 2, 0)
                elif action == 'down':
                    ctypes.windll.user32.keybd_event(self.VK_VOLUME_DOWN, 0, 0, 0)
                    ctypes.windll.user32.keybd_event(self.VK_VOLUME_DOWN, 0, 2, 0)
                else:
                    raise ValueError("Unknown volume action")

            return {
                "success": True,
                "tool": self.name,
                "message": f"Volume set to {action}.",
                "data": {},
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "tool": self.name,
                "message": "Failed to adjust volume.",
                "data": {},
                "error": str(e)
            }

ToolRegistry.register(SetVolumeTool())
''',
    'app/tools/impl/windows_sysinfo.py': '''import platform
import psutil
from pydantic import BaseModel
from app.tools.base import Tool
from app.security.permissions import PermissionLevel
from app.tools.registry import ToolRegistry

class SysInfoInput(BaseModel):
    pass

class SysInfoTool(Tool):
    name = "get_system_info"
    description = "Gets read-only system information."
    input_schema = SysInfoInput
    permission_level = PermissionLevel.SAFE

    async def execute(self) -> dict:
        try:
            uname = platform.uname()
            svmem = psutil.virtual_memory()
            
            info = {
                "system": uname.system,
                "node_name": uname.node,
                "release": uname.release,
                "version": uname.version,
                "machine": uname.machine,
                "processor": uname.processor,
                "total_ram_gb": round(svmem.total / (1024 ** 3), 2),
                "available_ram_gb": round(svmem.available / (1024 ** 3), 2),
            }
            
            message = f"OS: {info['system']} {info['release']} | CPU: {info['processor']} | RAM: {info['total_ram_gb']}GB"

            return {
                "success": True,
                "tool": self.name,
                "message": message,
                "data": info,
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "tool": self.name,
                "message": "Failed to get system info.",
                "data": {},
                "error": str(e)
            }

ToolRegistry.register(SysInfoTool())
''',
    'app/tools/impl/fs_tools.py': '''import os
from pydantic import BaseModel
from app.tools.base import Tool
from app.security.permissions import PermissionLevel
from app.tools.registry import ToolRegistry

class ListDirInput(BaseModel):
    path: str

class ListDirTool(Tool):
    name = "list_directory"
    description = "Lists files in a given directory."
    input_schema = ListDirInput
    permission_level = PermissionLevel.SAFE

    async def execute(self, path: str) -> dict:
        try:
            # Basic path validation
            if not os.path.exists(path):
                raise FileNotFoundError(f"Path does not exist: {path}")
            if not os.path.isdir(path):
                raise NotADirectoryError(f"Path is not a directory: {path}")
            
            files = os.listdir(path)
            
            return {
                "success": True,
                "tool": self.name,
                "message": f"Found {len(files)} items in {path}.",
                "data": {"files": files},
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "tool": self.name,
                "message": f"Failed to list directory.",
                "data": {},
                "error": str(e)
            }

ToolRegistry.register(ListDirTool())
''',
    'app/orchestrator/fast_router.py': '''import re
import logging
from typing import Tuple, Dict, Any, Optional

logger = logging.getLogger('jarvis.fast_router')

class Intent:
    OPEN_APP = 'open_application'
    OPEN_URL = 'open_url'
    VOLUME_CONTROL = 'set_volume'
    SYS_INFO = 'get_system_info'
    LIST_DIR = 'list_directory'

class FastRouter:
    """
    Deterministically routes natural language text to Tool intents without LLM overhead.
    Returns (intent_name, kwargs) or None if it should fallback to Gemini.
    """
    
    def __init__(self):
        # Extremely lightweight regex mapping
        self.rules = [
            (r'^(?:open|launch|start) (chrome|edge|notepad|calculator|terminal|explorer|cmd)$', Intent.OPEN_APP),
            (r'^(?:can you )?(?:open|launch) (?:chrome|edge|notepad|calculator|terminal|explorer|cmd)$', Intent.OPEN_APP),
            (r'^(?:go to|open url) (.+\.[a-z]+)$', Intent.OPEN_URL),
            (r'^(?:open|launch) (.+\.[a-z]+)$', Intent.OPEN_URL),
            (r'^(?:turn )?volume up', Intent.VOLUME_CONTROL),
            (r'^(?:increase|raise) volume', Intent.VOLUME_CONTROL),
            (r'^(?:turn )?volume down', Intent.VOLUME_CONTROL),
            (r'^(?:decrease|lower) volume', Intent.VOLUME_CONTROL),
            (r'^(?:mute|silence)(?: volume)?', Intent.VOLUME_CONTROL),
            (r'^(?:unmute)(?: volume)?', Intent.VOLUME_CONTROL),
            (r'^(?:what is my system info|system info|system specs|get system info)', Intent.SYS_INFO),
        ]

    def parse(self, text: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        normalized = text.lower().strip().rstrip('.?!')
        
        # 1. Check Volume
        if 'volume up' in normalized or 'increase volume' in normalized or 'raise volume' in normalized:
            return Intent.VOLUME_CONTROL, {'action': 'up'}
        if 'volume down' in normalized or 'decrease volume' in normalized or 'lower volume' in normalized:
            return Intent.VOLUME_CONTROL, {'action': 'down'}
        if 'mute' in normalized or 'silence' in normalized:
            if 'unmute' not in normalized:
                return Intent.VOLUME_CONTROL, {'action': 'mute'}

        # 2. Check general regexes
        for pattern, intent in self.rules:
            match = re.search(pattern, normalized)
            if match:
                groups = match.groups()
                
                if intent == Intent.OPEN_APP:
                    app_name = groups[0] if groups else normalized.split()[-1]
                    return intent, {'app_name': app_name}
                    
                if intent == Intent.OPEN_URL:
                    return intent, {'url': groups[0]}

                if intent == Intent.SYS_INFO:
                    return intent, {}

        # 3. Check simple list dir (just for testing phase 2)
        if normalized.startswith('list files in '):
            path = text[14:].strip()
            return Intent.LIST_DIR, {'path': path}

        return None
'''
}

for rel_path, content in files.items():
    p = base / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(content)

print('Backend Phase 2 scaffolded successfully.')
