import pytest
import asyncio
from app.providers.gemini import GeminiProvider
from app.orchestrator.router import BrainRouter
from app.memory.session import SessionManager, ConversationSession

# Mocking Google GenAI for tests
class MockGeminiChunk:
    def __init__(self, text):
        self.text = text

class MockGeminiStream:
    async def __aiter__(self):
        yield MockGeminiChunk("Hello, ")
        yield MockGeminiChunk("how can ")
        yield MockGeminiChunk("I help you?")

class MockGeminiModels:
    async def generate_content(self, **kwargs):
        class MockResp:
            text = "Mocked full response"
        return MockResp()

    async def generate_content_stream(self, **kwargs):
        return MockGeminiStream()

class MockGeminiAio:
    def __init__(self):
        self.models = MockGeminiModels()

class MockGeminiClient:
    def __init__(self, **kwargs):
        self.aio = MockGeminiAio()

@pytest.mark.asyncio
async def test_session_manager():
    session = SessionManager.get_or_create("test-123")
    assert session.session_id == "test-123"
    session.add_user_message("Hello")
    session.add_assistant_message("Hi there")
    assert len(session.history) == 2
    assert session.history[0]['role'] == 'user'

@pytest.mark.asyncio
async def test_gemini_provider_mock(monkeypatch):
    import app.providers.gemini as gemini_module
    from app.core.config import settings
    
    monkeypatch.setattr(gemini_module, 'genai', type('MockGenai', (), {'Client': MockGeminiClient}))
    monkeypatch.setattr(settings, 'GEMINI_API_KEY', 'dummy-key')
    
    provider = GeminiProvider()
    
    # generate
    resp = await provider.generate("Test")
    assert resp == "Mocked full response"

    # stream
    stream_results = []
    async for chunk in provider.stream("Test"):
        stream_results.append(chunk)
    
    assert "".join(stream_results) == "Hello, how can I help you?"
