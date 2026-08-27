import pytest
from app.orchestrator.fast_router import FastRouter, Intent

def test_fast_router_volume():
    router = FastRouter()
    
    assert router.parse("turn the volume up")[0] == Intent.VOLUME_CONTROL
    assert router.parse("volume down")[0] == Intent.VOLUME_CONTROL
    assert router.parse("mute")[0] == Intent.VOLUME_CONTROL

def test_fast_router_open_app():
    router = FastRouter()
    
    intent, kwargs = router.parse("open chrome")
    assert intent == Intent.OPEN_APP
    assert kwargs['app_name'] == 'chrome'
    
    intent, kwargs = router.parse("launch notepad")
    assert intent == Intent.OPEN_APP
    assert kwargs['app_name'] == 'notepad'

def test_fast_router_open_url():
    router = FastRouter()
    
    intent, kwargs = router.parse("open google.com")
    assert intent == Intent.OPEN_URL
    assert kwargs['url'] == 'google.com'

def test_fast_router_unmatched():
    router = FastRouter()
    
    # Complex query should return None (fallback to Gemini)
    assert router.parse("what is a black hole?") is None
    assert router.parse("explain why chrome keeps crashing") is None
