import os
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
