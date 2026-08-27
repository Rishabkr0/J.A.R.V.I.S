import pytest
import os
import time
from app.memory.db import MemoryDatabase
from app.orchestrator.fast_router import FastRouter, Intent

@pytest.fixture
def memory_db():
    test_db = "data/test_memory.db"
    if os.path.exists(test_db):
        try:
            os.remove(test_db)
        except OSError:
            pass
    db = MemoryDatabase(test_db)
    yield db
    if hasattr(db, 'conn'):
        db.conn.close()
    if os.path.exists(test_db):
        try:
            os.remove(test_db)
        except OSError:
            pass

def test_create_and_get_memory(memory_db):
    mem = memory_db.create_memory("USER_PREFERENCE", "browser", "Chrome")
    assert mem is not None
    assert mem.key == "browser"
    assert mem.value == "Chrome"
    
    fetched = memory_db.get_memory_by_key("browser")
    assert fetched.id == mem.id

def test_credential_filtering(memory_db):
    # Should reject obvious API keys
    mem1 = memory_db.create_memory("USER_FACT", "api_key", "sk-123456789012345678901234567890")
    assert mem1 is None
    
    # Should reject passwords
    mem2 = memory_db.create_memory("USER_FACT", "secret", "my password is foo")
    assert mem2 is None

def test_memory_update_on_duplicate(memory_db):
    mem1 = memory_db.create_memory("USER_PREFERENCE", "browser", "Chrome")
    mem2 = memory_db.create_memory("USER_PREFERENCE", "browser", "Edge")
    
    assert mem1.id == mem2.id  # Same ID, it was updated
    assert mem2.value == "Edge"
    
    all_mems = memory_db.list_memories()
    assert len(all_mems) == 1

def test_search_memories(memory_db):
    memory_db.create_memory("USER_PREFERENCE", "browser", "Chrome")
    memory_db.create_memory("USER_FACT", "laptop_name", "Atlas")
    
    results = memory_db.search_memories("browser")
    assert len(results) == 1
    assert results[0].value == "Chrome"
    
    results2 = memory_db.search_memories("Atlas")
    assert len(results2) == 1
    assert results2[0].key == "laptop_name"

def test_fast_router_memory_intents():
    router = FastRouter()
    
    # Remember
    intent, kwargs = router.parse("Remember that my preferred browser is Chrome.")
    assert intent == Intent.REMEMBER
    assert kwargs['key'] == "preferred_browser"
    assert kwargs['value'] == "chrome"
    
    # Forget
    intent, kwargs = router.parse("Forget that my preferred browser is Chrome.")
    assert intent == Intent.FORGET
    assert kwargs['key'] == "preferred_browser"
    
    # Recall
    intent, kwargs = router.parse("What is my preferred browser?")
    assert intent == Intent.RECALL
    assert kwargs['query'] == "preferred_browser"
    
    # Clear All
    intent, kwargs = router.parse("Forget everything.")
    assert intent == Intent.CLEAR_MEMORIES
