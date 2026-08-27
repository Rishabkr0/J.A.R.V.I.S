import logging
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
