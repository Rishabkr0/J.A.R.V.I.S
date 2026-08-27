import ctypes
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
