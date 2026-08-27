from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel
from app.memory.db import memory_db, MemoryItem

router = APIRouter()

class MemoryCreate(BaseModel):
    key: str
    value: str
    type: str = "USER_FACT"

@router.get('/api/memories', response_model=List[MemoryItem])
async def list_memories(limit: int = 50, offset: int = 0):
    return memory_db.list_memories(limit, offset)

@router.post('/api/memories', response_model=MemoryItem)
async def create_memory(mem: MemoryCreate):
    created = memory_db.create_memory(type=mem.type, key=mem.key, value=mem.value, source="ui")
    if not created:
        raise HTTPException(status_code=400, detail="Failed to create memory. May contain sensitive information.")
    return created

@router.delete('/api/memories/{memory_id}')
async def delete_memory(memory_id: str):
    success = memory_db.delete_memory(memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found.")
    return {"success": True}

@router.delete('/api/memories')
async def clear_all_memories():
    memory_db.clear_all()
    return {"success": True}

@router.get('/api/memories/search', response_model=List[MemoryItem])
async def search_memories(q: str):
    return memory_db.search_memories(q)
