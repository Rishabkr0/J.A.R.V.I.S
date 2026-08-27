import platform
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
