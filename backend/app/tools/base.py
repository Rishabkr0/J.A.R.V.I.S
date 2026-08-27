from abc import ABC, abstractmethod
from typing import Any, Dict, Type
from pydantic import BaseModel
from app.security.permissions import PermissionLevel

class Tool(ABC):
    name: str
    description: str
    input_schema: Type[BaseModel]
    permission_level: PermissionLevel

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        pass
