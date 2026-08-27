import webbrowser
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
