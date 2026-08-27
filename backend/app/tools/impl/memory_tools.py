import logging
from app.tools.registry import ToolRegistry
from app.tools.base import Tool
from app.security.permissions import PermissionLevel
from app.memory.db import memory_db

logger = logging.getLogger("jarvis.tools.memory")

class RememberTool(Tool):
    name = "remember_information"
    description = "Explicitly saves information to persistent memory."
    permission_level = PermissionLevel.SAFE
    
    async def execute(self, key: str, value: str, type: str = "USER_FACT", **kwargs) -> dict:
        memory = memory_db.create_memory(type=type, key=key, value=value, source="explicit")
        if not memory:
            return {
                "success": False,
                "message": f"I cannot store that information. It appears to contain sensitive credentials.",
                "data": {}
            }
            
        return {
            "success": True,
            "message": f"I'll remember that {key.replace('_', ' ')} is {value}.",
            "data": {"id": memory.id}
        }

class ForgetTool(Tool):
    name = "forget_information"
    description = "Deletes information from persistent memory by key."
    permission_level = PermissionLevel.SAFE
    
    async def execute(self, key: str = None, memory_id: str = None, **kwargs) -> dict:
        if memory_id:
            success = memory_db.delete_memory(memory_id)
        elif key:
            mem = memory_db.get_memory_by_key(key)
            if mem:
                success = memory_db.delete_memory(mem.id)
            else:
                success = False
        else:
            return {"success": False, "message": "No key or memory_id provided.", "data": {}}
            
        if success:
            return {"success": True, "message": f"I've forgotten that preference.", "data": {}}
        else:
            return {"success": False, "message": f"I couldn't find any memory matching that.", "data": {}}

class RecallTool(Tool):
    name = "recall_information"
    description = "Retrieves information from persistent memory by query."
    permission_level = PermissionLevel.SAFE
    
    async def execute(self, query: str, **kwargs) -> dict:
        results = memory_db.search_memories(query, limit=1)
        if results:
            return {
                "success": True,
                "message": f"Your {results[0].key.replace('_', ' ')} is {results[0].value}.",
                "data": {"key": results[0].key, "value": results[0].value}
            }
        else:
            return {
                "success": False,
                "message": "I don't have that in my memory.",
                "data": {}
            }

class ClearAllMemoriesTool(Tool):
    name = "clear_all_memories"
    description = "Deletes all persistent memories."
    # Mandatory Confirmation Required per PRD for destructive resets
    permission_level = PermissionLevel.CONFIRMATION_REQUIRED
    
    async def execute(self, **kwargs) -> dict:
        # If this executes, it means permission was somehow granted (Phase 2 blocks this currently)
        memory_db.clear_all()
        return {
            "success": True,
            "message": "All memories have been permanently deleted.",
            "data": {}
        }

ToolRegistry.register(RememberTool())
ToolRegistry.register(ForgetTool())
ToolRegistry.register(RecallTool())
ToolRegistry.register(ClearAllMemoriesTool())
